"""Choices offered by the interface, with the rules behind them."""
from __future__ import annotations

import datetime as dt

CROPS = [
    ("Maize", "Milho"), ("Soybean", "Soja"), ("Wheat_winter", "Trigo de inverno"),
    ("Wheat_summer", "Trigo de primavera"), ("Barley", "Cevada"), ("Sorghum", "Sorgo"),
    ("Cotton", "Algodão"), ("DryBean", "Feijão"), ("PaddyRice1", "Arroz (1ª safra)"),
    ("PaddyRice2", "Arroz (2ª safra)"), ("Potato", "Batata"), ("Cassava", "Mandioca"),
    ("SugarCane", "Cana-de-açúcar"), ("SugarBeet", "Beterraba açucareira"),
    ("Sunflower", "Girassol"),
]

NEX_MODELS = [
    ("GFDL-CM4", "r1i1p1f1"), ("GFDL-ESM4", "r1i1p1f1"), ("ACCESS-CM2", "r1i1p1f1"),
    ("CanESM5", "r1i1p1f1"), ("EC-Earth3", "r1i1p1f1"), ("IPSL-CM6A-LR", "r1i1p1f1"),
    ("MIROC6", "r1i1p1f1"), ("MPI-ESM1-2-HR", "r1i1p1f1"), ("MRI-ESM2-0", "r1i1p1f1"),
    ("NorESM2-MM", "r1i1p1f1"), ("UKESM1-0-LL", "r1i1p1f2"),
]
SSPS = [("ssp126", "SSP1-2.6 (baixas emissões)"), ("ssp245", "SSP2-4.5 (intermediário)"),
        ("ssp370", "SSP3-7.0 (altas emissões)"), ("ssp585", "SSP5-8.5 (muito altas)")]
# AquaCrop-OSPy 3.1 ships CO2 trajectories for these SSPs.
CO2_SCENARIOS = ["ssp126", "ssp245", "ssp370", "ssp585"]
RESOLUTIONS = [0.05, 0.1, 0.25, 0.5]

# seconds of AquaCrop per cell per simulated year on one core (measured ~0.2 s)
SECONDS_PER_CELL_YEAR = 0.25


def year_limits() -> dict:
    current = dt.date.today().year
    return {"agera5": [1979, current - 1], "nex": [1950, 2100], "current": current}
