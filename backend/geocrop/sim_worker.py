"""Per-cell simulation worker, executed in child processes.

Wraps ``geoaquacrop_simulate.processor.worker_run`` — the toolchain's own
per-cell routine — and adds three things around it:

* per-season water balance recomputed from the daily output (the upstream
  enrichers sum ET and precipitation over the whole simulation period and give
  every season the same total; see the study notes, finding H);
* compact daily series for the interface;
* optional, explicitly requested scientific patches (soil profile depth, CO2
  scenario). With no patch selected the AquaCrop run is the upstream one.

Everything here must be importable in a fresh process (Windows uses spawn), so
the patches are applied inside the child, at call time.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

DAILY_VARS = ["canopy_cover", "biomass", "z_root", "Wr", "Tr", "Es",
              "Runoff", "DeepPerc", "IrrDay", "Precipitation", "ReferenceET",
              "MinTemp", "MaxTemp"]

# Compartments aligned to the six SoilGrids layer boundaries (0.05 ... 2.0 m).
ALIGNED_DZ = [0.05, 0.10, 0.15, 0.15, 0.15, 0.20, 0.20, 0.25, 0.25, 0.25, 0.25]
LAYER_THICKNESS = [0.05, 0.10, 0.15, 0.30, 0.40, 1.00]

_state = {"patched": False, "last_weather": None, "soil_fix": False, "co2": None}


def _install_hooks():
    """Wrap upstream loaders once per process (idempotent)."""
    if _state["patched"]:
        return
    from geoaquacrop_simulate import processor

    original_weather = processor.DataLoader.load_weather_for_point
    original_soil = processor.DataLoader.load_soil_for_point
    original_model = processor.AquaCropModel

    def weather_hook(*args, **kwargs):
        df = original_weather(*args, **kwargs)
        _state["last_weather"] = df
        return df

    def soil_hook(soil_files, x, y):
        if not _state["soil_fix"]:
            return original_soil(soil_files, x, y)
        import xarray as xr
        from aquacrop import Soil
        layers = []
        for key in ["0_5cm", "5_15cm", "15_30cm", "30_60cm", "60_100cm", "100_200cm"]:
            with xr.open_dataset(soil_files[key]) as ds:
                pt = ds.sel(x=x, y=y, method="nearest")
                vals = (float(pt["Sand"].values), float(pt["Clay"].values), float(pt["Som"].values))
            if any(np.isnan(v) for v in vals):
                return None
            layers.append(vals)
        soil = Soil("custom", cn=46, rew=7, dz=ALIGNED_DZ)
        for (sand, clay, om), thickness in zip(layers, LAYER_THICKNESS):
            soil.add_layer_from_texture(thickness=thickness, Sand=sand, Clay=clay,
                                        OrgMat=om, penetrability=100)
        return soil

    def model_hook(*args, **kwargs):
        if _state["co2"] and "co2_concentration" not in kwargs:
            from aquacrop.entities.co2 import CO2
            kwargs["co2_concentration"] = CO2(scenario=_state["co2"])
        return original_model(*args, **kwargs)

    processor.DataLoader.load_weather_for_point = staticmethod(weather_hook)
    processor.DataLoader.load_soil_for_point = staticmethod(soil_hook)
    processor.AquaCropModel = model_hook
    _state["patched"] = True


def _season_table(final_stats: pd.DataFrame, water_flux: pd.DataFrame,
                  weather: pd.DataFrame | None) -> pd.DataFrame:
    """Per-season sums over the days the crop was in the field (dap >= 1)."""
    rows = []
    wf = water_flux.reset_index(drop=True)
    if weather is not None and len(weather) >= len(wf):
        wx = weather.iloc[: len(wf)].reset_index(drop=True)
    else:
        wx = None
    for season in final_stats["Season"].astype(int):
        sel = (wf["season_counter"] == season) & (wf["dap"] >= 1)
        tr, es = float(wf.loc[sel, "Tr"].sum()), float(wf.loc[sel, "Es"].sum())
        rec = {"Season": season, "tr_mm": tr, "es_mm": es, "et_mm": tr + es,
               "runoff_mm": float(wf.loc[sel, "Runoff"].sum()),
               "deep_perc_mm": float(wf.loc[sel, "DeepPerc"].sum()),
               "irrigation_mm": float(wf.loc[sel, "IrrDay"].sum()),
               "days_in_field": int(sel.sum())}
        if wx is not None:
            rec["precip_mm"] = float(wx.loc[sel.values, "Precipitation"].sum())
            rec["et0_mm"] = float(wx.loc[sel.values, "ReferenceET"].sum())
        else:
            rec["precip_mm"] = np.nan
            rec["et0_mm"] = np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def run_cell(i, coords_row, validated_inputs, config):
    """Simulate one grid cell. Returns a small, picklable dict."""
    _install_hooks()
    from geoaquacrop_simulate import processor

    patches = config.get("geocrop_patches") or {}
    _state["soil_fix"] = bool(patches.get("soil_profile"))
    _state["co2"] = patches.get("co2_scenario") or None
    _state["last_weather"] = None

    logger = logging.getLogger("geocrop.cell")
    out = processor.worker_run(i, coords_row, validated_inputs, config, logger)
    summary = out["summary"]
    daily = out.get("daily")
    result = {"i": int(i), "x": float(coords_row["x"]), "y": float(coords_row["y"]),
              "summary": summary, "seasons": None, "daily": None, "error": None}
    if daily is None or "error" in summary.columns:
        result["error"] = str(summary["error"].iloc[0]) if "error" in summary.columns else "no daily output"
        return result

    weather = _state["last_weather"]
    result["seasons"] = _season_table(summary, daily["water_flux"], weather)

    wf = daily["water_flux"].reset_index(drop=True)
    cg = daily["crop_growth"].reset_index(drop=True)
    n = len(wf)
    series = {}
    for var in DAILY_VARS:
        if var in wf.columns:
            series[var] = wf[var].to_numpy(dtype="float32")
        elif var in cg.columns:
            series[var] = cg[var].to_numpy(dtype="float32")
        elif weather is not None and var in weather.columns and len(weather) >= n:
            series[var] = weather[var].iloc[:n].to_numpy(dtype="float32")
    if weather is not None and len(weather) >= n:
        series["_date0"] = str(pd.Timestamp(weather["Date"].iloc[0]).date())
    series["_season"] = wf["season_counter"].to_numpy(dtype="int16")
    series["_dap"] = wf["dap"].to_numpy(dtype="int16")
    result["daily"] = series
    return result
