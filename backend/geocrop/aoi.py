"""Area of interest (AOI) ingestion.

Turns whatever the user provides — a drawn polygon, GeoJSON, KML, KMZ or a
zipped shapefile — into one clean polygon in EPSG:4326, which is what
geoaquacrop_preprocess requires (Polygon/MultiPolygon only, WGS84 declared).

Errors and warnings are carried as message keys (see ``i18n.py``) and
translated at the edge, in the language the interface asked for.
"""
from __future__ import annotations

import io
import json
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union

from .i18n import tr

SUPPORTED = (".geojson", ".json", ".kml", ".kmz", ".zip", ".gpkg")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
# preprocess warns below this extent: coarse climate grids (ET0 at 0.25 deg)
SMALL_EXTENT_DEG = 0.25


class AOIError(ValueError):
    """A problem with the user's area, as a translatable message key."""

    def __init__(self, key: str, **kw):
        super().__init__(tr(key, "en", **kw))
        self.key, self.kw = key, kw

    def text(self, lang: str) -> str:
        return tr(self.key, lang, **self.kw)


# ------------------------------------------------------------------ readers --

def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_kml_coords(text: str):
    pts = []
    for token in (text or "").replace("\n", " ").replace("\t", " ").split():
        parts = token.split(",")
        if len(parts) >= 2:
            try:
                pts.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return pts


def _kml_to_geoms(kml_bytes: bytes):
    """Minimal KML reader: every <Polygon> (with holes), in any folder or
    MultiGeometry. KML is always lon,lat WGS84 by specification."""
    try:
        root = ET.fromstring(kml_bytes)
    except ET.ParseError as exc:
        raise AOIError("aoi.bad_kml", err=str(exc)) from exc
    geoms, names = [], []
    for placemark in root.iter():
        if _strip_ns(placemark.tag) != "Placemark":
            continue
        name = ""
        for child in placemark:
            if _strip_ns(child.tag) == "name":
                name = (child.text or "").strip()
        for poly in placemark.iter():
            if _strip_ns(poly.tag) != "Polygon":
                continue
            shell, holes = None, []
            for boundary in poly:
                kind = _strip_ns(boundary.tag)
                coords = None
                for el in boundary.iter():
                    if _strip_ns(el.tag) == "coordinates":
                        coords = _parse_kml_coords(el.text)
                if not coords or len(coords) < 3:
                    continue
                if kind == "outerBoundaryIs":
                    shell = coords
                elif kind == "innerBoundaryIs":
                    holes.append(coords)
            if shell:
                geoms.append(Polygon(shell, holes))
                names.append(name)
    if not geoms:
        raise AOIError("aoi.kml_no_polygon")
    return geoms, names


def _read_with_geopandas(path: str):
    import geopandas as gpd

    gdf = gpd.read_file(path)
    warnings = []
    if gdf.crs is None:
        warnings.append(("aoi.no_crs", {}))
        gdf = gdf.set_crs(4326)
    elif gdf.crs.to_epsg() != 4326:
        warnings.append(("aoi.reprojected", {"crs": gdf.crs.to_string()}))
        gdf = gdf.to_crs(4326)
    name_col = next((c for c in gdf.columns
                     if str(c).lower() in ("name", "nome", "nm_mun", "nm_uf", "name_1",
                                           "name_2", "label")), None)
    names = [str(v) for v in gdf[name_col]] if name_col else [""] * len(gdf)
    return list(gdf.geometry), names, warnings


def _geojson_to_geoms(data: dict):
    warnings = []
    crs = (data.get("crs") or {}).get("properties", {}).get("name", "")
    if crs and "4326" not in crs and "CRS84" not in crs.upper():
        # rare, legacy GeoJSON with a non-WGS84 crs member: let GDAL handle it
        with tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            return _read_with_geopandas(tmp)
        finally:
            Path(tmp).unlink(missing_ok=True)
    kind = data.get("type")
    if kind == "FeatureCollection":
        feats = data.get("features") or []
    elif kind == "Feature":
        feats = [data]
    elif kind in ("Polygon", "MultiPolygon", "GeometryCollection"):
        feats = [{"type": "Feature", "geometry": data, "properties": {}}]
    else:
        raise AOIError("aoi.geojson_empty")
    geoms, names = [], []
    for feat in feats:
        if not feat or not feat.get("geometry"):
            continue
        geoms.append(shape(feat["geometry"]))
        props = feat.get("properties") or {}
        names.append(str(props.get("name") or props.get("nome") or ""))
    return geoms, names, warnings


def read_upload(filename: str, payload: bytes):
    """Read an uploaded file into (geoms, names, warnings)."""
    if len(payload) > MAX_UPLOAD_BYTES:
        raise AOIError("aoi.too_big")
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise AOIError("aoi.unsupported", ext=suffix or "(?)")

    if suffix in (".geojson", ".json"):
        try:
            data = json.loads(payload.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AOIError("aoi.bad_geojson", err=str(exc)) from exc
        return _geojson_to_geoms(data)

    if suffix == ".kml":
        geoms, names = _kml_to_geoms(payload)
        return geoms, names, []

    if suffix == ".kmz":
        try:
            zf = zipfile.ZipFile(io.BytesIO(payload))
        except zipfile.BadZipFile as exc:
            raise AOIError("aoi.bad_kmz") from exc
        kmls = [n for n in zf.namelist() if n.lower().endswith(".kml")]
        if not kmls:
            raise AOIError("aoi.kmz_no_kml")
        main = "doc.kml" if "doc.kml" in kmls else kmls[0]
        geoms, names = _kml_to_geoms(zf.read(main))
        return geoms, names, []

    # .zip (shapefile) and .gpkg go through GDAL
    with tempfile.TemporaryDirectory() as tmp:
        if suffix == ".zip":
            try:
                zf = zipfile.ZipFile(io.BytesIO(payload))
            except zipfile.BadZipFile as exc:
                raise AOIError("aoi.bad_zip") from exc
            for member in zf.namelist():           # guard against path traversal
                target = (Path(tmp) / member).resolve()
                if not str(target).startswith(str(Path(tmp).resolve())):
                    raise AOIError("aoi.zip_paths")
            zf.extractall(tmp)
            shps = sorted(Path(tmp).rglob("*.shp"))
            if not shps:
                inner = [p for p in Path(tmp).rglob("*") if p.suffix.lower()
                         in (".geojson", ".json", ".kml", ".gpkg")]
                if inner:
                    return read_upload(inner[0].name, inner[0].read_bytes())
                raise AOIError("aoi.zip_no_shp")
            shp = shps[0]
            missing = [ext for ext in (".shx", ".dbf") if not shp.with_suffix(ext).exists()
                       and not shp.with_suffix(ext.upper()).exists()]
            if missing:
                raise AOIError("aoi.shp_incomplete", missing=", ".join(missing))
            src = str(shp)
        else:
            src = str(Path(tmp) / "upload.gpkg")
            Path(src).write_bytes(payload)
        try:
            return _read_with_geopandas(src)
        except AOIError:
            raise
        except Exception as exc:  # GDAL errors are not user-friendly; summarise
            raise AOIError("aoi.unreadable", err=str(exc)) from exc


# ------------------------------------------------------------- normalising --

def _polygonal(geom):
    """Keep only the polygonal parts of any geometry; drop Z."""
    if geom is None or geom.is_empty:
        return []
    geom = shapely.force_2d(geom)
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    if hasattr(geom, "geoms"):
        out = []
        for g in geom.geoms:
            out.extend(_polygonal(g))
        return out
    return []


def normalise(geoms, names=None, warnings=None, source="upload", lang="pt"):
    """Validate, repair and dissolve geometries into one AOI description.

    ``warnings`` are (key, kwargs) pairs; they come back translated into
    ``lang`` in the result, alongside their keys (``warning_keys``) so the
    interface can re-translate them when the language changes.
    """
    warnings = list(warnings or [])
    polys, dropped = [], 0
    for g in geoms:
        parts = _polygonal(g)
        if not parts:
            dropped += 1
        polys.extend(parts)
    if dropped:
        warnings.append(("aoi.dropped", {"n": dropped}))
    if not polys:
        raise AOIError("aoi.no_polygon")

    fixed = []
    repaired = False
    for p in polys:
        if not p.is_valid:
            fixed.extend(_polygonal(shapely.make_valid(p)))
            repaired = True
        else:
            fixed.append(p)
    if repaired:
        warnings.append(("aoi.fixed", {}))
    domain = unary_union(fixed)
    if domain.is_empty:
        raise AOIError("aoi.empty")

    minx, miny, maxx, maxy = domain.bounds
    if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
        raise AOIError("aoi.not_degrees")
    if (maxx - minx) < SMALL_EXTENT_DEG or (maxy - miny) < SMALL_EXTENT_DEG:
        warnings.append(("aoi.small", {}))

    nverts = shapely.get_num_coordinates(domain)
    if nverts > 20000:
        domain = domain.simplify(0.001, preserve_topology=True)
        warnings.append(("aoi.simplified", {"n": f"{nverts:,}"}))

    if isinstance(domain, (Polygon, MultiPolygon)):
        domain_out = domain
    else:
        domain_out = MultiPolygon(_polygonal(domain))

    label = ", ".join(n for n in (names or []) if n)[:120]
    return {
        "geometry": mapping(domain_out),
        "bbox": [round(v, 6) for v in (minx, miny, maxx, maxy)],
        "area_km2": round(geodesic_area_km2(domain_out), 1),
        "n_parts": len(_polygonal(domain_out)),
        "name": label,
        "source": source,
        "warnings": [tr(k, lang, **kw) for k, kw in warnings],
        "warning_keys": [{"key": k, "args": kw} for k, kw in warnings],
    }


def geodesic_area_km2(geom) -> float:
    from pyproj import Geod

    area, _ = Geod(ellps="WGS84").geometry_area_perimeter(geom)
    return abs(area) / 1e6


def to_feature_collection(aoi: dict) -> dict:
    """The AOI as the single-feature GeoJSON that preprocess reads (EPSG:4326)."""
    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
        "features": [{"type": "Feature", "properties": {"name": aoi.get("name") or "AOI"},
                      "geometry": aoi["geometry"]}],
    }


def grid_cells(geometry: dict, resolution: float):
    """Centres of the grid cells whose centre lies inside the AOI.

    Mirrors the preprocess template grid: bounds snapped outwards to the
    resolution, cells inside the polygon kept. Used for estimates and for the
    synthetic demo inputs.
    """
    geom = shape(geometry)
    minx, miny, maxx, maxy = geom.bounds
    r = resolution
    xmin, ymin = np.floor(minx / r) * r, np.floor(miny / r) * r
    xmax, ymax = np.ceil(maxx / r) * r, np.ceil(maxy / r) * r
    xs = np.round(np.arange(xmin + r / 2, xmax, r), 6)
    ys = np.round(np.arange(ymax - r / 2, ymin, -r), 6)   # descending, like preprocess
    gx, gy = np.meshgrid(xs, ys)
    inside = shapely.contains_xy(geom, gx, gy)
    return xs, ys, inside


def estimate_cells(geometry: dict, resolution: float) -> int:
    _, _, inside = grid_cells(geometry, resolution)
    n = int(inside.sum())
    return max(n, 1)
