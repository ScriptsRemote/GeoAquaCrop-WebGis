# GeoAquaCrop — WebGIS

A local WebGIS that runs **GeoAquaCrop** (gridded AquaCrop-OSPy) over an area drawn on the map
or uploaded as a file, and lets you explore the results as maps and charts. The interface is in
**English and Portuguese** (PT/EN switch at the top of the left panel).
*Versão em português: [README.md](README.md).*

This is the web interface for GeoAquaCrop, developed by **Christopher (Chris) Bowden**
(University of Manchester), Josias Láng-Ritter, Seyed Hossein Hosseini (Aalto University),
E. Alkio, Henrikki Tenkanen (Aalto University) and Timothy (Tim) Foster (University of Manchester).
See [Credits](#credits).

```
browser (Leaflet + Chart.js)            local server (FastAPI, Python)
┌─────────────┬──────────┬──────────┐    ┌──────────────────────────────────────────┐
│ guided      │  map     │ results   │◀──▶│ area → geoaquacrop_preprocess (per step)  │
│ steps,      │ (draw,   │ KPIs,     │    │      → geoaquacrop_simulate (per cell)    │
│ period,     │  search, │ charts,   │    │      → results (CSV, NetCDF, GeoJSON)     │
│ run         │  grid)   │ modal     │    │ queue, progress, cache, temporary files   │
└─────────────┴──────────┴──────────┘    └──────────────────────────────────────────┘
```

## Install (Windows)

Needs Python 3.11, 3.12 or 3.13.

**Option A — venv (simplest):** double-click `instalar_geocrop.bat`.

**Option B — conda (if option A fails on rasterio/GDAL):**

```bat
conda env create -f environment.yml
conda activate geocrop
```

## Run

Double-click `iniciar_geocrop.bat` (or `python run.py`). The browser opens at
<http://127.0.0.1:8050>. The server only listens on this machine.

For a quick test without downloading anything, choose **Demo** in step 4.

## Workflow

1. **Area of interest** — draw a polygon or rectangle, upload GeoJSON, KML, KMZ, GeoPackage or a
   zipped shapefile (drag-and-drop onto the map works too), or search for a municipality, state or
   basin and use its boundary. Everything becomes one EPSG:4326 polygon; other coordinate systems are
   reprojected, invalid geometries repaired, and you are warned when the area is too small for the
   climate data (< 0.25°).
2. **Crop and management** — the toolchain's 15 crops; rainfed or irrigated.
3. **Period, climate and grid** — start and end year. The climate source follows the GeoAquaCrop rule:
   AgERA5 (1979 to last year, needs a Copernicus CDS token) or NASA NEX-GDDP-CMIP6 (periods reaching the
   current year or the future; model and SSP chosen here). Grid resolution with a cell and time estimate.
4. **Run** — per-step progress, detailed log and cancel.

The right panel shows the selected variable on the map (per season or mean), KPIs, yield per season,
water balance, distribution across cells and, when you click a cell, its daily series (canopy, biomass,
rain vs ET, root-zone water). Every chart opens in a modal with a table and CSV. **Download** gives:

| File | Contents |
|---|---|
| `seasons.csv` | One row per cell and season: yields, rain, ET, Tr, Es, runoff, percolation, irrigation, WP |
| `yield_grid.nc` | (year, y, x) grid of the main variables, for GIS |
| `cells.geojson` | Cells as polygons with per-year attributes (opens directly in QGIS) |
| `daily.nc` | Daily series of every cell (packed int16) |
| `aoi.geojson` | The exact polygon used |
| `model/summary_results_*.pkl` | The toolchain's own format (`gac.simulate.load_results`, visualize) |

## Downloads, cache and temporary files

* Every download goes to `data/tmp/<analysis>` and that folder **is deleted at the end of each
  analysis**, whether it succeeds, fails or is cancelled.
* Kept on purpose:
  - `data/cache/global` — the global SPAM and GGCMI archives, identical for any area (hundreds of MB;
    downloading them every time is what would make the tool slow);
  - `data/cache/areas/<area>` — each area's **processed** clips (small), so changing only the crop,
    regime or options runs with no new download. Can be switched off per analysis.
* The **Cache** button (below the history) shows the size of each part and clears it.

## Scientific options (step 3 → Advanced options)

Off by default, to reproduce the original toolchain:

* **2 m soil profile** — the toolchain builds the soil on AquaCrop-OSPy's 12 × 0.1 m compartments
  (1.2 m), which shifts the SoilGrids layers and drops the 100–200 cm one. The option uses
  compartments aligned to the six layers (2.0 m).
* **CO₂ from the SSP scenario** — without it, AquaCrop uses the Mauna Loa + A1B series for any
  scenario. Only affects projections.

Regardless of options, the interface recomputes rain, ET, Tr, Es, runoff, percolation and water productivity
**per season** from the daily output (planting to maturity). The toolchain's `seasonal_et_mm` and
`seasonal_precip_mm` columns sum the whole period and repeat that total for every season, which
distorts WP.

## Configuration (optional)

Copy `config.example.json` to `config.json`:

| Key | Use |
|---|---|
| `cds_api_token` | Copernicus CDS token, so you don't type it for every analysis |
| `google_maps_api_key` | Enables Google satellite through the official Maps JavaScript API. Without a key, Esri is used. Using Google tiles outside the API breaches its terms of use |
| `workers` | Simulation processes (0 = cores − 1) |
| `max_cells` | Cell limit per real analysis (default 20,000) |
| `nominatim_contact` | E-mail sent to the OpenStreetMap search, as its usage policy asks |

`GEOCROP_<KEY>` environment variables also work (e.g. `GEOCROP_CDS_API_TOKEN`).

## Known limitations

* **Time**: AgERA5 depends on the Copernicus CDS queue (minutes to hours). The first analysis downloads
  the global SPAM and GGCMI; later ones reuse them.
* **Cancel** stops between steps and between cells; a preprocessing download in progress finishes first.
  The toolchain's `download_url` retries indefinitely when the network drops, so a long outage keeps the
  step waiting.
* Seasons that do not finish by 31 Dec of the last year are not simulated; each season is dated by its
  harvest (in the southern hemisphere the first harvest usually falls in the year after the start).
* The demo uses **invented** climate, soil, calendar and crop area: it tests the workflow, it does not
  describe the region.
* Basemaps and search need internet; everything else (libraries, fonts) ships in `frontend/vendor` and
  works offline.

## Credits

Preprocessing and simulation come from the **GeoAquaCrop** packages, developed by:

| Author | Institution |
|---|---|
| **Christopher (Chris) Bowden** — maintainer of `geoaquacrop_simulate` | University of Manchester |
| Josias Láng-Ritter | Aalto University |
| Seyed Hossein Hosseini | Aalto University |
| E. Alkio | |
| Henrikki Tenkanen | Aalto University |
| Timothy (Tim) Foster | University of Manchester |

**How to cite.** When publishing results, cite GeoAquaCrop and AquaCrop-OSPy. Until the preprint is
out, the authors ask for:

> Láng-Ritter, J., Bowden, C., Hosseini, S., Alkio, E., Tenkanen, H. & Foster, T. GeoAquaCrop:
> Large-scale agricultural crop modelling using open global data (preprint in preparation).
>
> Kelly, T. D. & Foster, T. (2021). AquaCrop-OSPy: Bridging the gap between research and practice in
> crop-water modelling. *Agricultural Water Management* 254, 106976. doi:10.1016/j.agwat.2021.106976

**Model:** AquaCrop (FAO; Steduto, Hsiao, Raes & Fereres, 2009), AquaCrop-OS (Foster et al., 2017),
AquaCrop-OSPy (Kelly & Foster, 2021).

**Data:** AgERA5 (Copernicus C3S, Boogaard et al. 2020), NASA NEX-GDDP-CMIP6 (Thrasher et al. 2022),
SoilGrids 2.0 (ISRIC, Poggio et al. 2021), GGCMI phase 3 (Jägermeyr et al. 2021), MARC (Zhao et al. 2024),
SPAM (IFPRI, Yu et al. 2020). Please cite the data sources used too.

**Map and software:** Esri, OpenStreetMap, CARTO, OpenStreetMap Nominatim; Leaflet, Leaflet.draw,
Chart.js, FastAPI, Public Sans typeface. GeoAquaCrop and AquaCrop-OSPy are licensed Apache-2.0.

The same credits appear in the interface (**Credits** link at the bottom of the left panel).
