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


def run(conn, script):
    AdomdCommand(json.dumps(script), conn).ExecuteNonQuery()


def alter_table_columns(conn, table: str, columns: list) -> None:
    run(
        conn,
        {
            "alter": {
                "object": {"database": DATABASE, "table": table},
                "table": {"name": table, "columns": columns},
            }
        },
    )
    print(f"Updated {table}: {[c['name'] for c in columns]}")


conn = AdomdConnection()
DATABASE = database_name()
conn.ConnectionString = connection_string()
conn.Open()

alter_table_columns(
    conn,
    "ecommerce_marts dim_customers",
    [
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
        {"name": "lifetime_net_spend", "formatString": "$#,##0.00"},
    ],
)

alter_table_columns(
    conn,
    "ecommerce_marts fct_order_items",
    [
        {"name": "order_item_id", "summarizeBy": "none"},
        {"name": "net_line_revenue", "formatString": "$#,##0.00"},
        {"name": "line_revenue_amount", "formatString": "$#,##0.00"},
    ],
)

alter_table_columns(
    conn,
    "ecommerce_marts fct_orders",
    [
        {"name": "net_order_revenue", "formatString": "$#,##0.00"},
        {"name": "gross_revenue_amount", "formatString": "$#,##0.00"},
        {"name": "total_refund_amount", "formatString": "$#,##0.00"},
    ],
)

print("All metadata updates applied.")
conn.Close()
