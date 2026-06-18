import json
import os
import sys

ADOMD_DIR = r"C:\Program Files\Microsoft.NET\ADOMD.NET\110"
sys.path.insert(0, ADOMD_DIR)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
os.add_dll_directory(ADOMD_DIR)

import clr  # type: ignore

clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
from Microsoft.AnalysisServices.AdomdClient import AdomdConnection, AdomdCommand  # type: ignore

from pbi_connection import connection_string, database_name

TABLE = "ecommerce_marts dim_customers"

conn = AdomdConnection()
DATABASE = database_name()
conn.ConnectionString = connection_string()
conn.Open()

script = {
    "alter": {
        "object": {"database": DATABASE, "table": TABLE},
        "table": {
            "name": TABLE,
            "columns": [
                {"name": "country", "dataCategory": "Country", "description": "Customer country for geographic segmentation."},
                {"name": "city", "dataCategory": "City", "description": "Customer city for geographic segmentation."},
                {
                    "name": "geo_location",
                    "dataType": "string",
                    "dataCategory": "Place",
                    "type": "calculated",
                    "expression": '[city] & ", " & [country]',
                    "summarizeBy": "none",
                    "description": "City and country combined for map geocoding.",
                },
            ],
        },
    }
}

AdomdCommand(json.dumps(script), conn).ExecuteNonQuery()
print("geo metadata applied")
conn.Close()
