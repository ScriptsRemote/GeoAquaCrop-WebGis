"""Place search through OpenStreetMap Nominatim, returning boundaries.

Proxied by the backend so the request carries an identifying User-Agent and is
throttled to one request per second, as the Nominatim usage policy requires.
Boundaries (municipalities, states, countries, protected areas…) come back as
polygons that can be used directly as the area of interest.
"""
from __future__ import annotations

import threading
import time

import httpx

from .settings import settings

NOMINATIM = "https://nominatim.openstreetmap.org/search"
_lock = threading.Lock()
_last = [0.0]
_cache: dict[str, list] = {}


def search_places(q: str, limit: int = 8, lang: str = "pt") -> list[dict]:
    q = q.strip()
    if len(q) < 2:
        return []
    key = f"{lang}|{q.lower()}"
    if key in _cache:
        return _cache[key]
    with _lock:
        wait = 1.05 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        r = httpx.get(NOMINATIM, timeout=20, params={
            "q": q, "format": "jsonv2", "polygon_geojson": 1, "polygon_threshold": 0.002,
            "limit": limit, "addressdetails": 0,
        }, headers={"User-Agent": f"GeoAquaCrop-WebGIS/0.1 ({settings.nominatim_contact})",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.6" if lang == "pt" else "en;q=1.0,pt;q=0.5"})
    r.raise_for_status()
    out = []
    for item in r.json():
        geo = item.get("geojson") or {}
        bbox = item.get("boundingbox")  # [south, north, west, east] as strings
        out.append({
            "name": item.get("display_name", ""),
            "kind": f"{item.get('category', '')}/{item.get('type', '')}",
            "lat": float(item["lat"]), "lon": float(item["lon"]),
            "bbox": [float(bbox[2]), float(bbox[0]), float(bbox[3]), float(bbox[1])] if bbox else None,
            "geometry": geo if geo.get("type") in ("Polygon", "MultiPolygon") else None,
        })
    _cache[key] = out
    return out
