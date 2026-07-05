"""Configuration file loading and path utilities for ddgo-search."""

import os
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    # Fallback for Python < 3.11 (even though Python >= 3.11 is required by project metadata)
    import tomli as tomllib  # type: ignore


def get_default_config_path() -> Path:
    """Get the default configuration file path (~/.ddgo-search.toml)."""
    return Path("~").expanduser() / ".ddgo-search.toml"


def load_config_file(path: Path) -> Dict[str, Any]:
    """Load configuration from a TOML file."""
    if not path.exists():
        return {}

    config_data: Dict[str, Any] = {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
            # Populate flat config from root-level keys
            config_data.update(data)
            # Also support settings grouped inside specific sections
            for section in ["settings", "default", "ddgo-search"]:
                if section in data and isinstance(data[section], dict):
                    config_data.update(data[section])
    except Exception:
        # Gracefully handle file reading/parsing errors by returning empty config
        pass

    return config_data
