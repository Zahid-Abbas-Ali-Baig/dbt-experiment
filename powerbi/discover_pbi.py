"""Discover Power BI Desktop XMLA port/database and save powerbi/connection.json."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ADOMD_DIR = r"C:\Program Files\Microsoft.NET\ADOMD.NET\110"
sys.path.insert(0, ADOMD_DIR)
os.add_dll_directory(ADOMD_DIR)

import clr  # type: ignore

clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
from Microsoft.AnalysisServices.AdomdClient import AdomdConnection, AdomdCommand  # type: ignore

CONFIG = Path(__file__).resolve().parent / "connection.json"


def pbi_pids() -> set[int]:
    out = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", "(Get-Process PBIDesktop -ErrorAction SilentlyContinue).Id"],
        text=True,
    )
    return {int(x.strip()) for x in out.splitlines() if x.strip().isdigit()}


def listening_local_ports() -> list[int]:
    out = subprocess.check_output(["netstat", "-ano"], text=True, errors="replace")
    pids = pbi_pids()
    ports: set[int] = set()
    for line in out.splitlines():
        if "LISTENING" not in line or "127.0.0.1:" not in line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        if pid not in pids:
            continue
        local = parts[1]
        port = int(local.rsplit(":", 1)[-1])
        ports.add(port)
    return sorted(ports)


def try_connect(port: int) -> tuple[str, str] | None:
    conn = AdomdConnection()
    conn.ConnectionString = f"Data Source=localhost:{port};"
    try:
        conn.Open()
        reader = AdomdCommand("SELECT [Name] FROM $SYSTEM.TMSCHEMA_DATABASES", conn).ExecuteReader()
        databases: list[str] = []
        while reader.Read():
            databases.append(str(reader[0]))
        reader.Close()
        conn.Close()
        if databases:
            return str(port), databases[0]
    except Exception:
        pass
    return None


def main() -> int:
    if not pbi_pids():
        print("ERROR: Power BI Desktop is not running. Open shopsphere.pbix first.")
        return 1

    for port in listening_local_ports():
        result = try_connect(port)
        if result:
            port_s, database = result
            CONFIG.write_text(json.dumps({"port": int(port_s), "database": database}, indent=2))
            print(f"Saved {CONFIG}")
            print(f"  port={port_s}  database={database}")
            return 0

    print("ERROR: Could not find Power BI XMLA endpoint. Open shopsphere.pbix and retry.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
