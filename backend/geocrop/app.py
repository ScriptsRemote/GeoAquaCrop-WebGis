"""GeoAquaCrop WebGIS: web API + static frontend."""
from __future__ import annotations

import os
import shutil
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import catalog
from .aoi import AOIError, estimate_cells, normalise, read_upload
from .i18n import fmt_int, norm, tr
from .jobs import get_manager
from .pipeline import climate_source, plan_steps
from .settings import PROJECT_ROOT, settings

FRONTEND = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(_app):
    get_manager()          # start the job worker and reload past analyses
    yield


app = FastAPI(title="GeoAquaCrop WebGIS", version="0.1.0", lifespan=lifespan)


def _err(status: int, key: str, lang: str | None, **kw):
    """HTTP error with a message in the interface language (X-Lang header)."""
    return HTTPException(status, tr(key, lang, **kw))


def _pkg(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


# ------------------------------------------------------------------ meta --

@app.get("/api/meta")
def meta():
    real_ok = all(_pkg(p) for p in ("geoaquacrop_preprocess", "geoaquacrop_simulate"))
    return {
        "crops": [{"id": c, "label": l} for c, l in catalog.CROPS],
        "resolutions": catalog.RESOLUTIONS,
        "nex_models": [{"id": m, "ensemble": e} for m, e in catalog.NEX_MODELS],
        "ssps": [{"id": s, "label": l} for s, l in catalog.SSPS],
        "co2_scenarios": catalog.CO2_SCENARIOS,
        "years": catalog.year_limits(),
        "has_cds_token": bool(settings.cds_api_token),
        "google_maps_api_key": settings.google_maps_api_key or None,
        "real_mode_available": real_ok,
        "max_cells": settings.max_cells,
        "workers": settings.workers or max(1, (os.cpu_count() or 2) - 1),
        "seconds_per_cell_year": catalog.SECONDS_PER_CELL_YEAR,
        "versions": {p: _pkg(p) for p in ("geoaquacrop", "geoaquacrop_preprocess",
                                          "geoaquacrop_simulate", "aquacrop")},
    }


# ------------------------------------------------------------------- AOI --

class GeometryIn(BaseModel):
    geometry: dict
    name: str = ""
    source: str = "draw"


@app.post("/api/aoi/upload")
async def aoi_upload(file: UploadFile = File(...), x_lang: str | None = Header(None)):
    payload = await file.read()
    try:
        geoms, names, warnings = read_upload(file.filename or "upload", payload)
        return normalise(geoms, names, warnings, source=file.filename or "file", lang=norm(x_lang))
    except AOIError as exc:
        raise HTTPException(422, exc.text(norm(x_lang))) from exc


@app.post("/api/aoi/geometry")
def aoi_geometry(body: GeometryIn, x_lang: str | None = Header(None)):
    from shapely.geometry import shape

    g = body.geometry
    if g.get("type") == "Feature":
        g = g.get("geometry") or {}
    if g.get("type") == "FeatureCollection":
        geoms = [shape(f["geometry"]) for f in g.get("features", []) if f.get("geometry")]
    else:
        try:
            geoms = [shape(g)]
        except Exception as exc:  # noqa: BLE001
            raise _err(422, "err.geometry", x_lang, err=exc) from exc
    try:
        return normalise(geoms, [body.name], source=body.source, lang=norm(x_lang))
    except AOIError as exc:
        raise HTTPException(422, exc.text(norm(x_lang))) from exc


@app.get("/api/search")
def search(q: str, x_lang: str | None = Header(None)):
    from .search import search_places

    try:
        return search_places(q, lang=norm(x_lang))
    except Exception as exc:  # noqa: BLE001
        raise _err(502, "err.search", x_lang, err=exc) from exc


# ------------------------------------------------------------------ jobs --

class ClimateIn(BaseModel):
    nasanex_model: str = "GFDL-CM4"
    nasanex_scenario: str = "ssp245"
    nasanex_ensemble: str = "r1i1p1f1"


class PatchesIn(BaseModel):
    soil_profile: bool = False
    co2_scenario: str | None = None


class JobIn(BaseModel):
    aoi: dict
    mode: str = Field("demo", pattern="^(demo|real)$")
    crop: str = "Maize"
    irrigation: str = Field("rainfed", pattern="^(rainfed|irrigated)$")
    start_year: int
    end_year: int
    resolution: float = 0.05
    climate: ClimateIn = ClimateIn()
    patches: PatchesIn = PatchesIn()
    api_token: str = ""
    keep_area_cache: bool = True
    label: str = ""


def _validate_job(body: JobIn, lang: str) -> dict:
    crops = {c for c, _ in catalog.CROPS}
    if body.crop not in crops:
        raise _err(422, "err.unknown_crop", lang, crop=body.crop)
    if body.start_year > body.end_year:
        raise _err(422, "err.years_order", lang)
    if not (1950 <= body.start_year <= 2100 and 1950 <= body.end_year <= 2100):
        raise _err(422, "err.years_range", lang)
    if body.resolution <= 0 or body.resolution > 1:
        raise _err(422, "err.resolution", lang)
    if not body.aoi.get("geometry"):
        raise _err(422, "err.no_aoi", lang)
    n = estimate_cells(body.aoi["geometry"], body.resolution)
    if body.mode == "real":
        source = climate_source(body.start_year, body.end_year)
        token = (body.api_token or settings.cds_api_token or "").strip()
        if source == "agera5" and len(token) <= 30:
            raise _err(422, "err.token", lang)
        if n > settings.max_cells:
            raise _err(422, "err.too_many_cells", lang, n=fmt_int(n, lang), max=fmt_int(settings.max_cells, lang))
    elif n > 3000:
        raise _err(422, "err.demo_cells", lang, n=fmt_int(n, lang))
    params = body.model_dump()
    params["lang"] = lang
    params["estimated_cells"] = n
    params["climate_source"] = ("synthetic" if body.mode == "demo"
                                else climate_source(body.start_year, body.end_year))
    return params


@app.post("/api/estimate")
def estimate(body: JobIn):
    n = estimate_cells(body.aoi["geometry"], body.resolution)
    years = body.end_year - body.start_year + 1
    workers = settings.workers or max(1, (os.cpu_count() or 2) - 1)
    sim_s = n * years * catalog.SECONDS_PER_CELL_YEAR / workers
    return {"cells": n, "years": years, "workers": workers, "simulation_seconds": sim_s,
            "climate_source": climate_source(body.start_year, body.end_year),
            "over_limit": n > settings.max_cells}


@app.post("/api/jobs")
def create_job(body: JobIn, x_lang: str | None = Header(None)):
    params = _validate_job(body, norm(x_lang))
    job = get_manager().create(params, plan_steps(params))
    return job.to_dict()


@app.get("/api/jobs")
def list_jobs():
    mgr = get_manager()
    out = []
    for job in sorted(mgr.jobs.values(), key=lambda j: j.created, reverse=True):
        p = job.params
        out.append({"id": job.id, "status": job.status, "created": job.created,
                    "crop": p.get("crop"), "irrigation": p.get("irrigation"), "mode": p.get("mode"),
                    "start_year": p.get("start_year"), "end_year": p.get("end_year"),
                    "label": p.get("label") or (p.get("aoi") or {}).get("name") or "",
                    "area_km2": (p.get("aoi") or {}).get("area_km2")})
    return out


def _job(job_id, lang=None):
    job = get_manager().jobs.get(job_id)
    if job is None:
        raise _err(404, "err.job_not_found", lang)
    return job


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = _job(job_id)
    d = job.to_dict(log_tail=200)
    d["queue_position"] = get_manager().queue_position(job_id)
    return d


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    _job(job_id)
    return get_manager().cancel(job_id).to_dict()


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, x_lang: str | None = Header(None)):
    job = _job(job_id, x_lang)
    if job.status in ("queued", "running"):
        raise _err(409, "err.cancel_first", x_lang)
    shutil.rmtree(job.dir, ignore_errors=True)
    del get_manager().jobs[job_id]
    return {"deleted": job_id}


@app.get("/api/jobs/{job_id}/map")
def job_map(job_id: str, x_lang: str | None = Header(None)):
    path = _job(job_id, x_lang).dir / "results" / "map.json"
    if not path.exists():
        raise _err(404, "err.results_not_ready", x_lang)
    return FileResponse(path, media_type="application/json")


@app.get("/api/jobs/{job_id}/aoi")
def job_aoi(job_id: str, x_lang: str | None = Header(None)):
    path = _job(job_id, x_lang).dir / "aoi.geojson"
    if not path.exists():
        raise _err(404, "err.aoi_not_found", x_lang)
    return FileResponse(path, media_type="application/geo+json")


@app.get("/api/jobs/{job_id}/cell/{cell_id}")
def job_cell(job_id: str, cell_id: int, x_lang: str | None = Header(None)):
    from .daily_store import read_cell

    path = _job(job_id, x_lang).dir / "results" / "daily.nc"
    if not path.exists():
        raise _err(404, "err.daily_missing", x_lang)
    data = read_cell(path, cell_id)
    if data is None:
        raise _err(404, "err.cell_missing", x_lang)
    return JSONResponse(data)


@app.get("/api/jobs/{job_id}/files/{name:path}")
def job_file(job_id: str, name: str):
    base = (_job(job_id).dir / "results").resolve()
    target = (base / name).resolve()
    if not str(target).startswith(str(base)) or not target.is_file():
        raise _err(404, "err.file_missing", None)
    return FileResponse(target, filename=f"{job_id}_{target.name}")


@app.get("/api/jobs/{job_id}/log")
def job_log(job_id: str):
    return {"log": _job(job_id).log}


# ----------------------------------------------------------------- cache --

def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) if path.exists() else 0


@app.get("/api/cache")
def cache_info():
    areas = [d for d in settings.area_cache_dir.iterdir() if d.is_dir()] if settings.area_cache_dir.exists() else []
    return {"global_bytes": _dir_size(settings.global_cache_dir),
            "areas_bytes": _dir_size(settings.area_cache_dir), "areas": len(areas),
            "tmp_bytes": _dir_size(settings.tmp_dir), "path": str(settings.cache_dir)}


@app.delete("/api/cache")
def clear_cache(scope: str = "areas", x_lang: str | None = Header(None)):
    if any(j.status == "running" for j in get_manager().jobs.values()):
        raise _err(409, "err.cache_busy", x_lang)
    targets = {"areas": [settings.area_cache_dir], "global": [settings.global_cache_dir],
               "all": [settings.area_cache_dir, settings.global_cache_dir, settings.tmp_dir]}.get(scope)
    if targets is None:
        raise _err(422, "err.cache_scope", x_lang)
    for t in targets:
        shutil.rmtree(t, ignore_errors=True)
        t.mkdir(parents=True, exist_ok=True)
    return cache_info()


# -------------------------------------------------------------- frontend --

if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
