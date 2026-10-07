"""The analysis pipeline: area → inputs → AquaCrop per cell → results → cleanup.

Data handling, as agreed for this tool:

* Every download lands in a per-analysis temporary folder
  (``data/tmp/<job>``) and that folder is deleted when the analysis ends,
  whatever the outcome.
* Two things are kept on purpose, because re-downloading them each time is
  what makes runs slow:
  - ``data/cache/global``: the global, area-independent archives (SPAM crop
    areas, GGCMI crop calendar), hundreds of MB that are identical for every
    area;
  - ``data/cache/areas/<area>``: the *processed* inputs of an area (clipped,
    small NetCDFs), so changing only the crop, irrigation or patches re-runs the
    simulation without downloading anything. Can be switched off per run, and
    cleared from the interface.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import pickle
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path

from .aoi import estimate_cells, to_feature_collection
from .i18n import fmt_int
from .jobs import Cancelled, Job
from .settings import settings

WEATHER_VARS = ("MinTemp", "MaxTemp", "Precipitation", "ReferenceET")
SOIL_FILES = tuple(f"soil_{d}.nc" for d in ("0-5", "5-15", "15-30", "30-60", "60-100", "100-200"))
GLOBAL_RAW = ("cropmasks", "cropcalendar")


# ----------------------------------------------------------------- helpers --

class _JobStream(io.TextIOBase):
    """Send print() output of the toolchain to the job log (and the console)."""

    def __init__(self, job: Job, echo):
        self.job, self.echo, self._buf = job, echo, ""

    def write(self, s):
        if self.echo is not None:
            try:
                self.echo.write(s)
            except Exception:  # noqa: BLE001
                pass
        self._buf += s.replace("\r", "\n")
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip() and "it/s]" not in line and "cells/s]" not in line:
                self.job.write(line)
        return len(s)

    def flush(self):
        if self._buf.strip():
            self.job.write(self._buf)
        self._buf = ""


@contextlib.contextmanager
def capture_output(job: Job):
    out, err = sys.stdout, sys.stderr
    stream = _JobStream(job, out)
    sys.stdout = sys.stderr = stream
    try:
        yield
    finally:
        stream.flush()
        sys.stdout, sys.stderr = out, err


def _link_or_copy(src, dst):
    if os.path.exists(dst):          # already linked in an earlier pass
        return dst
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)
    return dst


def _link_tree(src: Path, dst: Path):
    if src.exists():
        shutil.copytree(src, dst, copy_function=_link_or_copy, dirs_exist_ok=True)


def _merge_into(src: Path, dst: Path):
    """Move files from src into dst unless already present there."""
    if not src.exists():
        return
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target))


def spam_refyear(start_year: int, end_year: int) -> int:
    import numpy as np
    avg = np.ceil(np.mean([start_year, end_year]))
    return min([2010, 2020], key=lambda yr: abs(yr - avg))


def climate_source(start_year: int, end_year: int) -> str:
    """Same rule as geoaquacrop_preprocess."""
    current = dt.date.today().year
    return "agera5" if (start_year >= 1979 and end_year < current) else "nex-gddp-cmip6"


def area_key(geometry: dict, resolution: float) -> str:
    blob = json.dumps(geometry, sort_keys=True, separators=(",", ":")) + f"|{resolution:.4f}"
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def climate_signature(p: dict) -> str:
    if climate_source(p["start_year"], p["end_year"]) == "agera5":
        return "agera5"
    c = p.get("climate") or {}
    return "nex_{}_{}_{}".format(c.get("nasanex_model", "GFDL-CM4"),
                                 c.get("nasanex_scenario", "ssp245"),
                                 c.get("nasanex_ensemble", "r1i1p1f1"))


def expected_outputs(step: str, p: dict) -> list[str]:
    tag = f"{p['start_year']}{p['end_year']}"
    if step == "soil":
        return list(SOIL_FILES)
    if step == "crop_areas":
        return [f"spam{spam_refyear(p['start_year'], p['end_year'])}_physical_area.nc"]
    if step == "crop_calendar":
        return ["cropcalendar.nc"]
    if step == "climate":
        return [f"{v}{tag}.nc" for v in WEATHER_VARS]
    raise KeyError(step)


# ------------------------------------------------------------------- steps --

def prepare_area(job: Job, work: Path) -> Path:
    p = job.params
    job.start_step("area")
    work.mkdir(parents=True, exist_ok=True)
    aoi_path = work / "aoi.geojson"
    fc = to_feature_collection(p["aoi"])
    aoi_path.write_text(json.dumps(fc), encoding="utf-8")
    (job.dir / "aoi.geojson").write_text(json.dumps(fc), encoding="utf-8")
    n = estimate_cells(p["aoi"]["geometry"], p["resolution"])
    job.finish_step("area", msg=("msg.area_done", {"area": int(round(p["aoi"].get("area_km2", 0) or 0)),
                                                   "n": n, "res": p["resolution"]}))
    return aoi_path


def prepare_synthetic(job: Job, work: Path) -> dict:
    from .synthetic import write_synthetic_inputs

    p = job.params
    job.start_step("synthetic", ("msg.synthetic_start", {}))
    processed = work / "processed"
    with capture_output(job):
        write_synthetic_inputs(processed, p["aoi"]["geometry"], p["resolution"],
                               p["start_year"], p["end_year"], p["crop"], p["irrigation"],
                               log=job.write, lang=job.lang)
    job.finish_step("synthetic")
    return {"weather_path": processed, "soil_path": processed,
            "pheno_path": processed, "spam_path": processed}


def prepare_real(job: Job, work: Path, aoi_path: Path) -> dict:
    """Run geoaquacrop_preprocess one dataset at a time, reusing caches."""
    # the same function gac.preprocess.run delegates to (GeoAquaCrop façade)
    from geoaquacrop_preprocess import run as preprocess_run

    p = job.params
    keep = p.get("keep_area_cache", True)
    akey = area_key(p["aoi"]["geometry"], p["resolution"])
    static_cache = settings.area_cache_dir / akey / "static"
    climate_cache = settings.area_cache_dir / akey / "climate" / climate_signature(p)
    processed = work / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    (settings.area_cache_dir / akey).mkdir(parents=True, exist_ok=True)
    if keep:
        (settings.area_cache_dir / akey / "aoi.geojson").write_text(
            json.dumps(to_feature_collection(p["aoi"])), encoding="utf-8")

    # global archives: hard-link the cached copies into this run's raw folder
    for name in GLOBAL_RAW:
        _link_tree(settings.global_cache_dir / name, work / "rawdata" / name)

    token = (p.get("api_token") or settings.cds_api_token or "").strip()
    clim = p.get("climate") or {}
    source = climate_source(p["start_year"], p["end_year"])

    for step in ("soil", "crop_areas", "crop_calendar", "climate"):
        cache_dir = climate_cache if step == "climate" else static_cache
        files = expected_outputs(step, p)
        if keep and all((cache_dir / f).exists() for f in files):
            job.finish_step(step, status="skipped", msg=("msg.cache_reused", {}))
            continue
        msg = None
        if step == "climate":
            msg = (("msg.climate_agera5", {}) if source == "agera5" else
                   ("msg.climate_nex", {"model": clim.get("nasanex_model", "GFDL-CM4"),
                                        "ssp": clim.get("nasanex_scenario", "ssp245")}))
        job.start_step(step, msg)
        with capture_output(job):
            preprocess_run(
                domain_shape_path=str(aoi_path),
                start_year=int(p["start_year"]), end_year=int(p["end_year"]),
                api_token=token,          # the toolchain validates it on every step
                cell_resolution=float(p["resolution"]),
                preprocess=[step],
                nasanex_model=clim.get("nasanex_model", "GFDL-CM4"),
                nasanex_scenario=clim.get("nasanex_scenario", "ssp245"),
                nasanex_ensemble=clim.get("nasanex_ensemble", "r1i1p1f1"),
                workingdirectory=str(work),
            )
        missing = [f for f in files if not (processed / f).exists()]
        if missing:
            raise RuntimeError(job.t("err.step_no_output", step=step, files=", ".join(missing)))
        if keep:
            cache_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                shutil.copy2(processed / f, cache_dir / f)
        job.finish_step(step)
        # bank newly downloaded global archives right away (survives a later failure)
        for name in GLOBAL_RAW:
            _merge_into(work / "rawdata" / name, settings.global_cache_dir / name)
            _link_tree(settings.global_cache_dir / name, work / "rawdata" / name)

    if keep:
        return {"weather_path": climate_cache, "soil_path": static_cache,
                "pheno_path": static_cache, "spam_path": static_cache}
    return {"weather_path": processed, "soil_path": processed,
            "pheno_path": processed, "spam_path": processed}


def simulate(job: Job, paths: dict, results_dir: Path):
    """Validate inputs with the toolchain, then run every cell in parallel."""
    from geoaquacrop_simulate.config import SimulationConfig
    from geoaquacrop_simulate.run_aquacrop import build_config

    from .daily_store import DailyWriter
    from .sim_worker import run_cell

    p = job.params
    job.start_step("simulate", ("msg.sim_validating", {}))
    model_dir = results_dir / "model"
    cfg = build_config(
        **{k: str(v) for k, v in paths.items()},
        start_date=f"{p['start_year']}/01/01", end_date=f"{p['end_year']}/12/31",
        crop=p["crop"], irrigation=p["irrigation"], output_dir=str(model_dir),
        geocrop_patches=p.get("patches") or {},
    )
    with capture_output(job):
        sim_config = SimulationConfig(cfg)
        validated = sim_config.validate_all_inputs()
    coords = validated["coords"].reset_index(drop=True)
    n = len(coords)
    if n == 0:
        raise RuntimeError(job.t("err.no_cells"))
    if p["mode"] == "real" and n > settings.max_cells:
        raise RuntimeError(job.t("err.too_many_cells_run", n=fmt_int(n, job.lang),
                                 max=fmt_int(settings.max_cells, job.lang)))

    workers = settings.workers or max(1, (os.cpu_count() or 2) - 1)
    workers = min(workers, n)
    job.progress("simulate", 0.0, ("msg.sim_start", {"n": n, "workers": workers}))
    start = dt.date(int(p["start_year"]), 1, 1)
    n_days = (dt.date(int(p["end_year"]), 12, 31) - start).days + 1
    writer = DailyWriter(results_dir / "daily.nc", start, n_days)

    sim_cfg = dict(sim_config.config)
    summaries, seasons, errors = [], [], []
    t0, done = time.time(), 0
    ctx = get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
        futures = [pool.submit(run_cell, i, row, validated, sim_cfg) for i, row in coords.iterrows()]
        try:
            for fut in as_completed(futures):
                if job.cancelled():
                    raise Cancelled()
                r = fut.result()
                done += 1
                summaries.append(r["summary"])
                if r["error"]:
                    errors.append({"cell_id": r["i"], "x": r["x"], "y": r["y"], "error": r["error"]})
                else:
                    s = r["seasons"]
                    s["cell_id"] = r["i"]
                    seasons.append(s)
                    writer.add(r["i"], r["x"], r["y"], r["daily"])
                if done == 1 or done % max(1, n // 200) == 0 or done == n:
                    rate = done / max(time.time() - t0, 1e-6)
                    eta = (n - done) / rate if rate > 0 else 0
                    job.progress("simulate", done / n,
                                 ("msg.sim_progress", {"done": done, "n": n, "eta": round(eta)}))
        except BaseException:
            for f in futures:
                f.cancel()
            pool.shutdown(wait=False, cancel_futures=True)
            writer.close()
            raise
    writer.close()

    model_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(model_dir / f"summary_results_{stamp}.pkl", "wb") as fh:   # toolchain format
        pickle.dump(summaries, fh, pickle.HIGHEST_PROTOCOL)
    elapsed = round(time.time() - t0)
    if errors:
        job.finish_step("simulate", msg=("msg.sim_done_failed",
                                         {"ok": n - len(errors), "failed": len(errors), "elapsed": elapsed}))
    else:
        job.finish_step("simulate", msg=("msg.sim_done", {"ok": n, "elapsed": elapsed}))
    return {"summaries": summaries, "seasons": seasons, "errors": errors,
            "validated": validated, "coords": coords, "n_cells": n}


# --------------------------------------------------------------- run a job --

def plan_steps(params: dict) -> list[str]:
    if params["mode"] == "demo":
        return ["area", "synthetic", "simulate", "results", "cleanup"]
    return ["area", "soil", "crop_areas", "crop_calendar", "climate", "simulate", "results", "cleanup"]


def run_job(job: Job):
    from .results import build_results

    p = job.params
    work = settings.tmp_dir / job.id
    results_dir = job.dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    try:
        aoi_path = prepare_area(job, work)
        if p["mode"] == "demo":
            paths = prepare_synthetic(job, work)
        else:
            paths = prepare_real(job, work, aoi_path)
        sim = simulate(job, paths, results_dir)
        job.start_step("results")
        job.result = build_results(job, sim, results_dir)
        job.finish_step("results", msg=("msg.results_done", {"n": len(job.result.get("years", []))}))
    finally:
        try:
            step = job.step("cleanup")
            step.status, step.started = "running", time.time()
            size = sum(f.stat().st_size for f in work.rglob("*") if f.is_file()) if work.exists() else 0
            shutil.rmtree(work, ignore_errors=True)
            job.finish_step("cleanup", msg=("msg.cleanup_done", {"mb": round(size / 1e6, 1)}))
        except Exception as exc:  # noqa: BLE001
            job.write(job.t("log.cleanup_failed", err=exc))
