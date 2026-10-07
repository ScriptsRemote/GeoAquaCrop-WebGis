"""Synthetic inputs for the demo mode.

Writes a ``processed/`` folder with exactly the files, variable names and
dimensions that geoaquacrop_preprocess produces, so the *real*
geoaquacrop_simulate stage runs on it unchanged. The values are plausible but
invented (latitude-driven climate, smooth random soils, textbook planting
dates). Use it to test the interface and the pipeline in seconds — never to
draw conclusions about a region.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import xarray as xr

from .aoi import grid_cells
from .i18n import tr

# Day of year of planting, northern / southern hemisphere (extra-tropical).
PLANTING_DOY = {
    "Maize": (120, 300), "Soybean": (135, 310), "Wheat_winter": (285, 140),
    "Wheat_summer": (110, 160), "Barley": (105, 150), "Sorghum": (135, 320),
    "Cotton": (120, 300), "DryBean": (140, 290), "Potato": (110, 250),
    "SugarBeet": (95, 260), "Sunflower": (120, 290), "PaddyRice1": (130, 320),
    "PaddyRice2": (200, 30), "Cassava": (110, 290), "SugarCane": (80, 270),
}
# Length used for crops whose AquaCrop default is a different cultivar type.
SEASON_LENGTH_OVERRIDE = {"Wheat_winter": 250}


def _field(seed: int, gx, gy, scale: float = 1.0, waves: int = 4):
    """Smooth pseudo-random field in [-1, 1] over the grid."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(gx, dtype=float)
    span = max(np.ptp(gx), np.ptp(gy), 0.5)
    for _ in range(waves):
        kx, ky = rng.uniform(0.5, 3.0, 2) * 2 * np.pi / span
        phase = rng.uniform(0, 2 * np.pi)
        out += np.sin(kx * gx + ky * gy + phase)
    out /= waves
    return np.clip(out * scale, -1, 1)


def _extraterrestrial_radiation(lat_deg, doy):
    """FAO-56 Eq. 21, MJ m-2 day-1."""
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def _spam_refyear(start_year: int, end_year: int) -> int:
    avg = np.ceil(np.mean([start_year, end_year]))
    return min([2010, 2020], key=lambda yr: abs(yr - avg))


def write_synthetic_inputs(processed_dir, geometry: dict, resolution: float,
                           start_year: int, end_year: int, crop: str,
                           irrigation: str, log=print, lang: str = "pt") -> dict:
    processed_dir.mkdir(parents=True, exist_ok=True)
    xs, ys, inside = grid_cells(geometry, resolution)
    gx, gy = np.meshgrid(xs, ys)
    seed = int(hashlib.sha1(f"{xs[:3]}{ys[:3]}{len(xs)}{len(ys)}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    mask = np.where(inside, 1.0, np.nan)
    n_in = int(inside.sum())
    log(tr("log.synthetic_grid", lang, n=n_in, ny=len(ys), nx=len(xs), res=resolution))

    # ---------------------------------------------------------- climate --
    time = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-31", freq="D")
    doy = time.dayofyear.values.astype(float)
    lat = gy
    south = lat < 0
    abs_lat = np.abs(lat)
    t_mean_annual = 27.5 - 0.42 * np.maximum(abs_lat - 10, 0) + 2.0 * _field(seed + 1, gx, gy)
    amplitude = 1.5 + 0.28 * abs_lat
    phase = np.where(south, 15.0, 197.0)          # warmest day of year
    seasonal = np.cos(2 * np.pi * (doy[:, None, None] - phase[None]) / 365.0)
    anomaly = np.zeros(len(time))
    for i in range(1, len(time)):                  # AR(1) weather noise, shared regionally
        anomaly[i] = 0.75 * anomaly[i - 1] + rng.normal(0, 1.2)
    year_offset = {y: rng.normal(0, 0.8) for y in range(start_year, end_year + 1)}
    yearly = np.array([year_offset[y] for y in time.year])
    tmean = t_mean_annual[None] + amplitude[None] * seasonal + (anomaly + yearly)[:, None, None]
    dtr = 9.0 + 2.5 * _field(seed + 2, gx, gy)[None] + rng.normal(0, 1.0, (len(time), 1, 1))
    dtr = np.clip(dtr, 4, 18)
    tmin = tmean - dtr / 2
    tmax = tmean + dtr / 2

    annual_p = 900 + 450 * _field(seed + 3, gx, gy)            # mm/yr
    wet_peak = np.where(south, 15.0, 196.0)
    seasonality = np.clip(abs_lat / 25.0, 0.2, 0.9)
    rain_shape = 1 + seasonality[None] * np.cos(2 * np.pi * (doy[:, None, None] - wet_peak[None]) / 365.0)
    p_wet = np.clip(0.33 * rain_shape, 0.03, 0.85)
    year_wet = {y: rng.uniform(0.7, 1.3) for y in range(start_year, end_year + 1)}
    yfac = np.array([year_wet[y] for y in time.year])[:, None, None]
    occurs = rng.random((len(time), 1, 1)) < p_wet[:, :1, :1]     # regional rain days
    occurs = occurs | (rng.random(p_wet.shape) < p_wet * 0.25)    # plus local showers
    mean_wet_day = annual_p[None] / 365.0 / np.clip(p_wet.mean(axis=0, keepdims=True), 0.05, 1)
    amount = rng.gamma(0.8, 1.0, p_wet.shape) * mean_wet_day * yfac
    precip = np.where(occurs, amount, 0.0)

    ra = _extraterrestrial_radiation(lat[None], doy[:, None, None])
    et0 = 0.0023 * 0.408 * ra * (tmean + 17.8) * np.sqrt(np.clip(tmax - tmin, 0.1, None))
    et0 = np.clip(et0, 0.1, None)

    tag = f"{start_year}{end_year}"
    coords = {"time": time, "y": ys, "x": xs}
    for name, arr, units in (("MinTemp", tmin, "degC"), ("MaxTemp", tmax, "degC"),
                             ("Precipitation", precip, "mm day-1"),
                             ("ReferenceET", et0, "mm day-1")):
        da = xr.DataArray((arr * mask[None]).astype("float32"), coords=coords,
                          dims=("time", "y", "x"), name=name, attrs={"units": units})
        da.to_dataset().to_netcdf(processed_dir / f"{name}{tag}.nc",
                                  encoding={name: {"zlib": True, "complevel": 4}})
    log(tr("log.synthetic_climate", lang))

    # ------------------------------------------------------------- soil --
    layers = ["0-5", "5-15", "15-30", "30-60", "60-100", "100-200"]
    base_clay = 28 + 14 * _field(seed + 4, gx, gy)
    base_sand = 42 - 18 * _field(seed + 5, gx, gy)
    for k, layer in enumerate(layers):
        clay = np.clip(base_clay + 2.0 * k, 5, 65)
        sand = np.clip(base_sand - 1.5 * k, 5, 85)
        total = clay + sand
        over = total > 95
        sand = np.where(over, sand * 95 / total, sand)
        clay = np.where(over, clay * 95 / total, clay)
        silt = 100 - clay - sand
        som = np.clip(3.2 * np.exp(-0.45 * k) + 0.4 * _field(seed + 6, gx, gy), 0.2, 8)
        ds = xr.Dataset({v: (("y", "x"), (a * mask).astype("float32"))
                         for v, a in (("Clay", clay), ("Sand", sand), ("Silt", silt), ("Som", som))},
                        coords={"y": ys, "x": xs})
        ds.to_netcdf(processed_dir / f"soil_{layer}.nc")
    log(tr("log.synthetic_soil", lang))

    # ---------------------------------------------------- crop calendar --
    from aquacrop import Crop

    base_name = "Wheat" if crop.startswith("Wheat_") else ("PaddyRice" if crop.startswith("PaddyRice") else crop)
    default_len = SEASON_LENGTH_OVERRIDE.get(crop, Crop(base_name, planting_date="01/01").MaturityCD)
    nh, sh = PLANTING_DOY.get(crop, (120, 300))
    planting = np.where(south, sh, nh) + 8 * _field(seed + 7, gx, gy)
    planting = np.clip(np.round(planting), 1, 365)
    planting = np.where(planting == 60, 61, planting)
    gsl = np.round(default_len * (1 + 0.08 * _field(seed + 8, gx, gy)))
    cal = {}
    for irr in ("rf", "ir"):
        cal[f"{crop}_{irr}_planting"] = (("y", "x"), (planting * mask).astype("float32"))
        cal[f"{crop}_{irr}_growing_season_length"] = (("y", "x"), (gsl * mask).astype("float32"))
    xr.Dataset(cal, coords={"y": ys, "x": xs}).to_netcdf(processed_dir / "cropcalendar.nc")
    log(tr("log.synthetic_calendar", lang, doy=int(np.nanmedian(planting * mask)),
           gsl=int(np.nanmedian(gsl * mask))))

    # -------------------------------------------------------- crop area --
    refyear = _spam_refyear(start_year, end_year)
    cell_km2 = (resolution * 111.32) ** 2 * np.cos(np.deg2rad(gy))
    share = np.clip(0.25 + 0.2 * _field(seed + 9, gx, gy), 0.02, 0.6)
    area = {}
    for irr, frac in (("rf", 0.85), ("ir", 0.15)):
        area[f"{crop}_{irr}_physical_area"] = (("y", "x"),
                                               (cell_km2 * 100 * share * frac * mask).astype("float32"))
    xr.Dataset(area, coords={"y": ys, "x": xs}).to_netcdf(
        processed_dir / f"spam{refyear}_physical_area.nc")
    log(tr("log.synthetic_area", lang, year=refyear))
    return {"cells": n_in, "nx": len(xs), "ny": len(ys)}
