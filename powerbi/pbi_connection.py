"""Shared Power BI Desktop XMLA connection settings."""
from __future__ import annotations

import json
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "connection.json"


def load_config() -> dict:
    if not CONFIG.exists():
        raise RuntimeError(
            "Missing powerbi/connection.json. Open shopsphere.pbix in Power BI Desktop, "
            "then run: python powerbi/discover_pbi.py"
        )
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def connection_string() -> str:
    cfg = load_config()
    return f"Data Source=localhost:{cfg['port']};Initial Catalog={cfg['database']};"


def database_name() -> str:
    return load_config()["database"]
