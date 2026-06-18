"""
Safely add named report pages to a .pbix.

IMPORTANT: Preserves original zip compression (DataModel must stay STORED).

Usage (from project root):
  python powerbi/inject_report.py
  python powerbi/inject_report.py powerbi/shopsphere.pbix
"""
from __future__ import annotations

import json
import secrets
import shutil
import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PBIX = SCRIPT_DIR / "shopsphere.pbix"
DEFAULT_OUTPUT = SCRIPT_DIR / "generated_report_layout.json"

PAGE_WIDTH = 1280
PAGE_HEIGHT = 720

PAGE_NAMES = [
    "Executive Dashboard",
    "Geographic Performance",
    "Customer Intelligence",
    "Products and Categories",
    "Marketing and Acquisition",
    "Revenue and Refunds",
    "Order Operations",
    "Semantic Model Health",
]


def section_name() -> str:
    return secrets.token_hex(10)


def read_layout_from_zip(zin: zipfile.ZipFile) -> dict:
    raw = zin.read("Report/Layout")
    return json.loads(raw.decode("utf-16-le"))


def build_sections() -> list[dict]:
    return [
        {
            "id": i,
            "name": section_name(),
            "displayName": display_name,
            "filters": "[]",
            "ordinal": i,
            "visualContainers": [],
            "config": "{}",
            "displayOption": 1,
            "width": PAGE_WIDTH,
            "height": PAGE_HEIGHT,
        }
        for i, display_name in enumerate(PAGE_NAMES)
    ]


def merge_layout(base: dict) -> dict:
    merged = dict(base)
    merged["sections"] = build_sections()
    merged.pop("pods", None)
    return merged


def write_pbix_layout(pbix_path: Path, layout: dict) -> None:
    backup = pbix_path.with_suffix(".pbix.bak")
    shutil.copy2(pbix_path, backup)
    layout_bytes = json.dumps(layout, indent=2).encode("utf-16-le")

    tmp_path = pbix_path.with_suffix(".pbix.tmp")
    with zipfile.ZipFile(pbix_path, "r") as zin, zipfile.ZipFile(
        tmp_path, "w"
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "Report/Layout":
                data = layout_bytes

            new_item = zipfile.ZipInfo(
                filename=item.filename,
                date_time=item.date_time,
            )
            new_item.compress_type = item.compress_type
            new_item.external_attr = item.external_attr
            new_item.flag_bits = item.flag_bits
            new_item.create_system = item.create_system
            new_item.create_version = item.create_version
            new_item.extract_version = item.extract_version
            zout.writestr(new_item, data, compress_type=item.compress_type)

    tmp_path.replace(pbix_path)
    print(f"Backup: {backup}")
    print(f"Updated layout in: {pbix_path}")


def inject_pbix(pbix_path: Path) -> None:
    with zipfile.ZipFile(pbix_path, "r") as zin:
        base = read_layout_from_zip(zin)
    layout = merge_layout(base)
    write_pbix_layout(pbix_path, layout)
    print(f"Added {len(layout['sections'])} empty pages.")


def main(argv: list[str]) -> int:
    pbix = Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_PBIX
    if not pbix.exists():
        print(f"File not found: {pbix}")
        return 1

    with zipfile.ZipFile(pbix, "r") as zin:
        base = read_layout_from_zip(zin)
    layout = merge_layout(base)
    DEFAULT_OUTPUT.write_text(json.dumps(layout, indent=2), encoding="utf-8")

    inject_pbix(pbix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
