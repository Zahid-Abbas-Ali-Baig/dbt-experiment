"""
ShopSphere Power BI model setup (measures + geo metadata via XMLA).

Run from ANY directory. Requires shopsphere.pbix OPEN in Power BI Desktop.

Usage:
  python c:\\wamp64\\www\\dbt-experiment-v3\\powerbi\\setup_all.py
  python powerbi/setup_all.py          (from project root)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def run(script: str) -> None:
    path = SCRIPT_DIR / script
    print(f"\n>> {path}")
    subprocess.check_call([sys.executable, str(path)], cwd=str(PROJECT_ROOT))


def main() -> int:
    print(f"Project root: {PROJECT_ROOT}")
    print("Step 1: Open shopsphere.pbix in Power BI Desktop.")

    config = SCRIPT_DIR / "connection.json"
    if config.exists():
        print(f"Step 2: Using existing {config}")
    else:
        print("Step 2: Discovering XMLA connection...\n")
        subprocess.check_call(
            [sys.executable, str(SCRIPT_DIR / "discover_pbi.py")],
            cwd=str(PROJECT_ROOT),
        )

    run("create_kpi_table_with_measures.py")
    run("apply_all_metadata.py")
    run("apply_geo_metadata.py")
    run("validate_dax.py")

    if "--inject-pages" in sys.argv:
        pbix = Path(sys.argv[sys.argv.index("--inject-pages") + 1]).resolve() if (
            len(sys.argv) > sys.argv.index("--inject-pages") + 1
            and not sys.argv[sys.argv.index("--inject-pages") + 1].startswith("-")
        ) else SCRIPT_DIR / "shopsphere.pbix"
        if pbix.exists():
            subprocess.check_call(
                [sys.executable, str(SCRIPT_DIR / "inject_report.py"), str(pbix)],
                cwd=str(PROJECT_ROOT),
            )
        else:
            print(f"PBIX not found for inject: {pbix}")

    print("\nSetup complete.")
    print("In Power BI Desktop: File > Save to persist model changes.")
    print("Build report visuals using powerbi/REPORT_PAGES.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
