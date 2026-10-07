"""Compact on-disk store for the daily series of every simulated cell.

One NetCDF file, dimensions (cell, time), variables packed as int16 with a
scale factor and zlib compression, written cell by cell as results arrive so
memory stays flat however large the domain.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np

# name -> (scale_factor, units, long name)
PACKING = {
    "canopy_cover": (1e-4, "1", "Canopy cover"),
    "biomass": (1.0, "g m-2", "Above-ground biomass"),
    "z_root": (1e-3, "m", "Effective rooting depth"),
    "Wr": (0.1, "mm", "Root-zone water"),
    "Tr": (0.01, "mm", "Transpiration"),
    "Es": (0.01, "mm", "Soil evaporation"),
    "Runoff": (0.02, "mm", "Surface runoff"),
    "DeepPerc": (0.02, "mm", "Deep percolation"),
    "IrrDay": (0.02, "mm", "Irrigation"),
    "Precipitation": (0.02, "mm", "Precipitation"),
    "ReferenceET": (0.01, "mm", "Reference evapotranspiration (ET0)"),
    "MinTemp": (0.01, "degC", "Minimum temperature"),
    "MaxTemp": (0.01, "degC", "Maximum temperature"),
}
FILL = np.int16(-32768)


class DailyWriter:
    def __init__(self, path: Path, start: dt.date, n_days: int):
        import netCDF4

        self.path = Path(path)
        self.n_days = n_days
        self.ds = netCDF4.Dataset(self.path, "w")
        self.ds.createDimension("cell", None)
        self.ds.createDimension("time", n_days)
        t = self.ds.createVariable("time", "i4", ("time",))
        t.units = f"days since {start.isoformat()}"
        t.calendar = "standard"
        t[:] = np.arange(n_days)
        for name, dtype in (("cell_id", "i4"), ("x", "f8"), ("y", "f8")):
            self.ds.createVariable(name, dtype, ("cell",))
        self.ds.createVariable("season", "i2", ("cell", "time"), zlib=True, complevel=4,
                               chunksizes=(1, n_days), fill_value=np.int16(-9))
        self.ds.createVariable("dap", "i2", ("cell", "time"), zlib=True, complevel=4,
                               chunksizes=(1, n_days), fill_value=np.int16(-9))
        for name, (scale, units, long_name) in PACKING.items():
            v = self.ds.createVariable(name, "i2", ("cell", "time"), zlib=True, complevel=4,
                                       chunksizes=(1, n_days), fill_value=FILL)
            v.scale_factor = scale
            v.add_offset = 0.0
            v.units = units
            v.long_name = long_name
        self.k = 0

    def _fit(self, arr):
        out = np.full(self.n_days, np.nan, dtype="float32")
        if arr is None:
            return out
        n = min(len(arr), self.n_days)
        out[:n] = arr[:n]
        return out

    def add(self, cell_id, x, y, series: dict):
        k = self.k
        self.ds["cell_id"][k] = cell_id
        self.ds["x"][k] = x
        self.ds["y"][k] = y
        for name in ("season", "dap"):
            a = self._fit(series.get(f"_{name}"))
            self.ds[name][k, :] = np.where(np.isnan(a), -9, a).astype("int16")
        for name, (scale, _, _) in PACKING.items():
            a = self._fit(series.get(name))
            limit = 32767 * scale
            a = np.clip(a, -limit, limit)
            self.ds[name][k, :] = np.ma.masked_invalid(a)
        self.k += 1

    def close(self):
        if self.ds is not None and self.ds.isopen():
            self.ds.close()


def read_cell(path: Path, cell_id: int) -> dict | None:
    import netCDF4

    with netCDF4.Dataset(path) as ds:
        ids = ds["cell_id"][:]
        hit = np.nonzero(np.asarray(ids) == cell_id)[0]
        if len(hit) == 0:
            return None
        k = int(hit[0])
        start = dt.date.fromisoformat(ds["time"].units.split("since ")[1][:10])
        n = ds.dimensions["time"].size
        out = {"cell_id": int(cell_id), "x": float(ds["x"][k]), "y": float(ds["y"][k]),
               "start": start.isoformat(), "n_days": n, "series": {}, "units": {}}
        for name in ["season", "dap", *PACKING]:
            arr = np.ma.filled(ds[name][k, :].astype("float64"), np.nan)
            out["series"][name] = [None if np.isnan(v) else round(float(v), 4) for v in arr]
            if name in PACKING:
                out["units"][name] = PACKING[name][1]
        return out
