"""Run with:  python -m pytest -q   (from the project folder)"""
import io
import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


@pytest.fixture(scope="session", autouse=True)
def _data_dir(tmp_path_factory):
    os.environ["GEOCROP_DATA_DIR"] = str(tmp_path_factory.mktemp("data"))


SQUARE = {"type": "Polygon", "coordinates": [[[-52, -25], [-51.5, -25], [-51.5, -24.6], [-52, -24.6], [-52, -25]]]}
KML = b"""<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>T1</name>
<Polygon><outerBoundaryIs><LinearRing><coordinates>-52,-25,0 -51.5,-25,0 -51.5,-24.6,0 -52,-24.6,0 -52,-25,0
</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>"""


def test_geojson_upload():
    from geocrop.aoi import normalise, read_upload
    fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "A"}, "geometry": SQUARE}]}
    aoi = normalise(*read_upload("a.geojson", json.dumps(fc).encode()))
    assert aoi["name"] == "A" and 2000 < aoi["area_km2"] < 2500


def test_kml_and_kmz():
    from geocrop.aoi import normalise, read_upload
    a = normalise(*read_upload("a.kml", KML))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("doc.kml", KML)
    b = normalise(*read_upload("a.kmz", buf.getvalue()))
    assert a["area_km2"] == b["area_km2"] and a["name"] == "T1"


def test_shapefile_zip_is_reprojected(tmp_path):
    import geopandas as gpd
    from shapely.geometry import shape
    from geocrop.aoi import normalise, read_upload
    gpd.GeoDataFrame({"nome": ["x"]}, geometry=[shape(SQUARE)], crs=4326).to_crs(31982).to_file(tmp_path / "a.shp")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in tmp_path.glob("a.*"):
            z.write(f, f.name)
    aoi = normalise(*read_upload("a.zip", buf.getvalue()))
    assert any(w["key"] == "aoi.reprojected" for w in aoi["warning_keys"])
    en = normalise(*read_upload("a.zip", buf.getvalue()), lang="en")
    assert en["warnings"][0].startswith("Reprojected")
    assert abs(aoi["bbox"][0] - -52) < 1e-3


def test_rejects_lines():
    from geocrop.aoi import AOIError, normalise
    from shapely.geometry import LineString
    with pytest.raises(AOIError):
        normalise([LineString([(0, 0), (1, 1)])])


def test_demo_job_end_to_end():
    from geocrop.aoi import normalise
    from geocrop.jobs import Job, Step, step_label
    from geocrop.pipeline import plan_steps, run_job
    from shapely.geometry import shape
    aoi = normalise([shape(SQUARE)], ["Teste"])
    p = dict(aoi=aoi, mode="demo", crop="Soybean", irrigation="rainfed", start_year=2018, end_year=2020,
             resolution=0.25, climate={}, patches={"soil_profile": True}, keep_area_cache=False,
             lang="en")
    job = Job(id="t-demo", params=p, created="now")
    job.steps = [Step(k, step_label(k, p["lang"])) for k in plan_steps(p)]
    run_job(job)
    assert all(s.status == "done" for s in job.steps)
    res = job.result
    assert res["n_ok"] > 0 and res["years"]
    first = res["by_year"][0]
    assert first["yield_dry"]["mean"] > 0
    # per-season ET must be a single season, well below a whole multi-year total
    assert first["et_mm"]["mean"] < 1200
    out = job.dir / "results"
    for f in ("seasons.csv", "map.json", "yield_grid.nc", "cells.geojson", "daily.nc"):
        assert (out / f).exists(), f
    from geocrop.daily_store import read_cell
    cell = read_cell(out / "daily.nc", json.loads((out / "map.json").read_text())["cells"][0][0])
    assert cell and len(cell["series"]["canopy_cover"]) == cell["n_days"]


def test_messages_both_languages():
    from geocrop.i18n import M, tr
    for key, (pt, en) in M.items():
        assert pt and en, key
    assert tr("err.no_aoi", "en") == "Define the area of interest."
    assert tr("err.no_aoi", "pt-BR").startswith("Defina")
    # every step message renders in both languages without missing placeholders
    from geocrop.jobs import Job, Step
    for lang in ("pt", "en"):
        j = Job(id="x", params={"lang": lang}, created="now")
        j.steps = [Step("simulate", "s")]
        j._set_msg(j.steps[0], ("msg.sim_progress", {"done": 3, "n": 10, "eta": 75}))
        assert "{" not in j.steps[0].message and "1min 15s" in j.steps[0].message
