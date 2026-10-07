"""Turn per-cell simulation output into the files and numbers the UI shows.

Written to ``data/jobs/<id>/results/``:

* ``seasons.csv``   one row per cell per harvested season (tidy, for analysis)
* ``map.json``      per-year values aligned to the cell list (for the map)
* ``yield_grid.nc`` (year, y, x) grids of the main variables (for GIS)
* ``cells.geojson`` cell squares with per-year attributes (for QGIS)
* ``daily.nc``      daily series per cell (already written during simulation)
* ``model/summary_results_*.pkl`` the toolchain's own format (compatibility)

Domain statistics are weighted by the crop's physical area in each cell
(SPAM) when available — that is how official yield statistics are formed
(production / area). Cells without area fall back to cos(latitude), i.e. land
area.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .jobs import Job

# English labels go into the files' metadata; the interface translates by key.
MAP_VARS = {
    "yield_dry": ("Dry yield", "t/ha", "green"),
    "yield_pot": ("Potential yield (no water stress)", "t/ha", "green"),
    "yield_gap": ("Water-limited yield gap (potential - actual)", "t/ha", "orange"),
    "production_t": ("Production (yield x SPAM area)", "t", "green"),
    "precip_mm": ("In-season precipitation", "mm", "blue"),
    "et_mm": ("In-season evapotranspiration (Tr + Es)", "mm", "blue"),
    "irrigation_mm": ("Applied irrigation", "mm", "blue"),
    "deep_perc_mm": ("Deep percolation", "mm", "blue"),
    "runoff_mm": ("Surface runoff", "mm", "blue"),
    "wp_et": ("Water productivity (yield / ET)", "kg/m3", "green"),
    "season_length": ("Season length", "days", "orange"),
}


def _crop_area(validated: dict, cells: pd.DataFrame) -> np.ndarray:
    import xarray as xr

    spam = validated.get("spam") or {}
    if not spam.get("variable"):
        return np.full(len(cells), np.nan)
    with xr.open_dataset(spam["filepath"]) as ds:
        da = ds[spam["variable"]]
        if "band" in da.dims:
            da = da.max(dim="band", skipna=True)
        vals = da.sel(x=xr.DataArray(cells["x"].values, dims="c"),
                      y=xr.DataArray(cells["y"].values, dims="c"), method="nearest").values
    return np.asarray(vals, dtype=float)


def _wstats(values: np.ndarray, weights: np.ndarray) -> dict:
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not ok.any():
        return {"mean": None, "p10": None, "p50": None, "p90": None, "min": None, "max": None, "n": 0}
    v, w = values[ok], weights[ok]
    q = np.percentile(v, [10, 50, 90])
    return {"mean": float(np.sum(v * w) / np.sum(w)), "p10": float(q[0]), "p50": float(q[1]),
            "p90": float(q[2]), "min": float(v.min()), "max": float(v.max()), "n": int(ok.sum())}


def _r(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return None
    return round(float(x), nd)


def build_results(job: Job, sim: dict, out: Path) -> dict:
    p = job.params
    res = float(p["resolution"])
    frames = [s for s in sim["summaries"] if s is not None and "error" not in s.columns]
    if not frames:
        reasons = pd.DataFrame(sim["errors"])["error"].value_counts().to_dict() if sim["errors"] else {}
        raise RuntimeError(job.t("err.no_result", reasons=reasons))
    summary = pd.concat(frames, ignore_index=True)
    seasons = pd.concat(sim["seasons"], ignore_index=True)
    df = summary.merge(seasons, on=["cell_id", "Season"], how="left")
    df["harvest_date"] = pd.to_datetime(df["Harvest Date (YYYY/MM/DD)"], errors="coerce")
    df = df.dropna(subset=["harvest_date"])
    df["year"] = df["harvest_date"].dt.year.astype(int)

    cells = (df[["cell_id", "x", "y"]].drop_duplicates("cell_id")
             .sort_values("cell_id").reset_index(drop=True))
    cells["crop_area_ha"] = _crop_area(sim["validated"], cells)
    df = df.merge(cells[["cell_id", "crop_area_ha"]], on="cell_id", how="left")

    df["yield_dry"] = df["Dry yield (tonne/ha)"].astype(float)
    df["yield_fresh"] = df["Fresh yield (tonne/ha)"].astype(float)
    df["yield_pot"] = df["Yield potential (tonne/ha)"].astype(float)
    df["yield_gap"] = (df["yield_pot"] - df["yield_dry"]).clip(lower=0)
    df["production_t"] = df["yield_dry"] * df["crop_area_ha"]
    df["wp_et"] = np.where(df["et_mm"] > 0, df["yield_dry"] * 100 / df["et_mm"], np.nan)
    df["rue"] = np.where(df["precip_mm"] > 0, df["yield_dry"] * 100 / df["precip_mm"], np.nan)
    df["season_length"] = df.get("season_length_days", np.nan)

    keep = ["cell_id", "x", "y", "year", "Season", "planting_date", "harvest_date",
            "yield_dry", "yield_fresh", "yield_pot", "yield_gap", "crop_area_ha", "production_t",
            "precip_mm", "et0_mm", "et_mm", "tr_mm", "es_mm", "runoff_mm", "deep_perc_mm",
            "irrigation_mm", "wp_et", "rue", "season_length", "days_in_field"]
    tidy = df[[c for c in keep if c in df.columns]].sort_values(["year", "cell_id"])
    tidy.to_csv(out / "seasons.csv", index=False, float_format="%.4f", date_format="%Y-%m-%d")

    # per (cell, year): mean over seasons harvested in the same year (rare: rice)
    per_cy = tidy.groupby(["year", "cell_id"]).mean(numeric_only=True).reset_index()
    years = sorted(int(y) for y in per_cy["year"].unique())

    area_w = cells.set_index("cell_id")["crop_area_ha"]
    use_area = bool(np.nansum(area_w.values) > 0)
    lat_w = np.cos(np.deg2rad(cells.set_index("cell_id")["y"]))
    weights = (area_w.fillna(0) if use_area else lat_w)

    # ---- map payload: values per variable per year aligned to `cells` ----
    idx = {cid: k for k, cid in enumerate(cells["cell_id"])}
    values = {}
    for var in MAP_VARS:
        if var not in per_cy.columns:
            continue
        values[var] = {}
        for y in years:
            arr = [None] * len(cells)
            sub = per_cy[per_cy["year"] == y]
            for cid, v in zip(sub["cell_id"], sub[var]):
                arr[idx[cid]] = _r(v, 3)
            values[var][str(y)] = arr
        allv = [v for y in years for v in values[var][str(y)] if v is not None]
        values[var]["_range"] = [float(np.percentile(allv, 2)), float(np.percentile(allv, 98))] \
            if allv else [0, 1]
    map_payload = {
        "resolution": res,
        "cells": [[int(c), round(float(x), 6), round(float(y), 6),
                   _r(a, 1) if np.isfinite(a) else None]
                  for c, x, y, a in cells[["cell_id", "x", "y", "crop_area_ha"]].itertuples(index=False)],
        "years": years,
        "vars": {k: {"label": v[0], "units": v[1], "ramp": v[2]} for k, v in MAP_VARS.items() if k in values},
        "values": values,
        "errors": sim["errors"][:2000],
    }
    (out / "map.json").write_text(json.dumps(map_payload, separators=(",", ":")), encoding="utf-8")

    # ---- domain statistics per year ----
    by_year = []
    for y in years:
        sub = per_cy[per_cy["year"] == y].set_index("cell_id")
        w = weights.reindex(sub.index).to_numpy(float)
        row = {"year": y, "cells": int(len(sub))}
        for var in ("yield_dry", "yield_pot", "yield_gap", "precip_mm", "et0_mm", "et_mm", "tr_mm",
                    "es_mm", "runoff_mm", "deep_perc_mm", "irrigation_mm", "season_length"):
            if var in sub.columns:
                st = _wstats(sub[var].to_numpy(float), w)
                row[var] = {k: _r(v) for k, v in st.items()}
        wsum = np.nansum(w * (sub["et_mm"].to_numpy(float) > 0))
        row["wp_et"] = _r(np.nansum(w * sub["yield_dry"].to_numpy(float)) * 100 /
                          np.nansum(w * sub["et_mm"].to_numpy(float))) if wsum > 0 else None
        row["production_t"] = _r(np.nansum(sub["production_t"].to_numpy(float)), 1) if use_area else None
        row["crop_area_ha"] = _r(np.nansum(sub["crop_area_ha"].to_numpy(float)), 1) if use_area else None
        by_year.append(row)

    _write_grid(per_cy, cells, years, res, out)
    _write_cells_geojson(per_cy, cells, years, res, out)

    err_counts = pd.DataFrame(sim["errors"])["error"].value_counts().head(8).to_dict() \
        if sim["errors"] else {}
    files = {f.name: f.stat().st_size for f in sorted(out.glob("*")) if f.is_file()}
    start, end = int(p["start_year"]), int(p["end_year"])
    missing_years = sorted(set(range(start, end + 1)) - set(years))
    return {
        "finished": time.time(),
        "years": years,
        "by_year": by_year,
        "weighting": "crop_area" if use_area else "cell_area",
        "n_cells": int(sim["n_cells"]),
        "n_ok": int(len(cells)),
        "n_failed": int(len(sim["errors"])),
        "failure_reasons": err_counts,
        "files": files,
        "missing_years": missing_years,
    }


def _write_grid(per_cy, cells, years, res, out: Path):
    import xarray as xr

    xs = np.round(np.sort(cells["x"].unique()), 6)
    ys = np.round(np.sort(cells["y"].unique())[::-1], 6)
    data = {}
    for var in ("yield_dry", "yield_pot", "yield_gap", "production_t", "et_mm", "precip_mm",
                "irrigation_mm", "wp_et"):
        if var not in per_cy.columns:
            continue
        cube = np.full((len(years), len(ys), len(xs)), np.nan, dtype="float32")
        xi = {v: i for i, v in enumerate(xs)}
        yi = {v: i for i, v in enumerate(ys)}
        for k, y in enumerate(years):
            sub = per_cy[per_cy["year"] == y]
            for xv, yv, val in zip(np.round(sub["x"], 6), np.round(sub["y"], 6), sub[var]):
                cube[k, yi[yv], xi[xv]] = val
        data[var] = (("year", "y", "x"), cube, {"long_name": MAP_VARS.get(var, (var,))[0],
                                                 "units": MAP_VARS.get(var, (None, ""))[1]})
    ds = xr.Dataset(data, coords={"year": years, "y": ys, "x": xs})
    ds["x"].attrs.update(units="degrees_east", standard_name="longitude")
    ds["y"].attrs.update(units="degrees_north", standard_name="latitude")
    ds.attrs.update(crs="EPSG:4326", resolution_deg=res, source="GeoAquaCrop WebGIS / geoaquacrop_simulate")
    ds.to_netcdf(out / "yield_grid.nc",
                 encoding={v: {"zlib": True, "complevel": 4} for v in data})


def _write_cells_geojson(per_cy, cells, years, res, out: Path):
    h = res / 2
    wide = per_cy.pivot_table(index="cell_id", columns="year",
                              values=["yield_dry", "et_mm", "precip_mm"], aggfunc="mean")
    feats = []
    for cid, x, y, area in cells[["cell_id", "x", "y", "crop_area_ha"]].itertuples(index=False):
        props = {"cell_id": int(cid), "x": float(x), "y": float(y),
                 "crop_area_ha": _r(area, 1) if np.isfinite(area) else None}
        if cid in wide.index:
            for (var, yr), v in wide.loc[cid].items():
                props[f"{var}_{yr}"] = _r(v, 3)
        feats.append({"type": "Feature", "properties": props, "geometry": {
            "type": "Polygon",
            "coordinates": [[[x - h, y - h], [x + h, y - h], [x + h, y + h], [x - h, y + h], [x - h, y - h]]]}})
    (out / "cells.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}),
                                       encoding="utf-8")
