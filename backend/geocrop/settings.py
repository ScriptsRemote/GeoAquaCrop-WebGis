"""Runtime settings for the GeoAquaCrop WebGIS.

Values come, in order of precedence, from environment variables
(``GEOCROP_*``), then ``config.json`` at the project root, then the defaults
below. Nothing here is required for the demo mode; the CDS token is only
needed for real runs over past years (AgERA5).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    data_dir: Path = PROJECT_ROOT / "data"
    # Copernicus CDS token (AgERA5). Can also be typed in the interface per run.
    cds_api_token: str = ""
    # Optional Google Maps JS API key: enables the official Google satellite layer.
    google_maps_api_key: str = ""
    # Worker processes for the per-cell AquaCrop runs (0 = cpu_count - 1).
    workers: int = 0
    # Refuse real runs above this many grid cells (protects the machine).
    max_cells: int = 20000
    # Keep the processed (clipped, harmonised) inputs of each area for reuse.
    keep_area_cache: bool = True
    # Contact sent in the User-Agent to Nominatim (their usage policy asks for one).
    nominatim_contact: str = "geocrop-local"
    host: str = "127.0.0.1"
    port: int = 8050
    extra: dict = field(default_factory=dict)

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def global_cache_dir(self) -> Path:
        """Global, area-independent downloads (SPAM, GGCMI) kept across runs."""
        return self.cache_dir / "global"

    @property
    def area_cache_dir(self) -> Path:
        """Processed inputs per area/period, reused when only the crop changes."""
        return self.cache_dir / "areas"

    @property
    def tmp_dir(self) -> Path:
        return self.data_dir / "tmp"


def _coerce(value: str, current):
    if isinstance(current, bool):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(current, int):
        return int(value)
    if isinstance(current, Path):
        return Path(value)
    return value


def load_settings() -> Settings:
    s = Settings()
    cfg_file = PROJECT_ROOT / "config.json"
    if cfg_file.exists():
        try:
            raw = json.loads(cfg_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"config.json is not valid JSON: {exc}") from exc
        for key, value in raw.items():
            if key.startswith("_"):
                continue
            if hasattr(s, key) and key != "extra":
                setattr(s, key, _coerce(str(value), getattr(s, key))
                        if not isinstance(value, type(getattr(s, key))) else value)
            else:
                s.extra[key] = value
    for key in list(vars(s)):
        env = os.environ.get(f"GEOCROP_{key.upper()}")
        if env is not None and key != "extra":
            setattr(s, key, _coerce(env, getattr(s, key)))
    if isinstance(s.data_dir, str):
        s.data_dir = Path(s.data_dir)
    if not s.data_dir.is_absolute():
        s.data_dir = PROJECT_ROOT / s.data_dir
    for d in (s.jobs_dir, s.global_cache_dir, s.area_cache_dir, s.tmp_dir):
        d.mkdir(parents=True, exist_ok=True)
    return s


settings = load_settings()
