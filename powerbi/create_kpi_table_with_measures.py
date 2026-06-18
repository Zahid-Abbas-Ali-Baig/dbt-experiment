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

FO = "'ecommerce_marts fct_orders'"
FOI = "'ecommerce_marts fct_order_items'"
DC = "'ecommerce_marts dim_customers'"

MEASURES = [
    ("Net Revenue", "Revenue", "$#,##0.00", f"CALCULATE(SUM({FO}[net_order_revenue]), {FO}[is_revenue_eligible] = TRUE)"),
    ("Gross Revenue", "Revenue", "$#,##0.00", f"CALCULATE(SUM({FO}[gross_revenue_amount]), {FO}[is_revenue_eligible] = TRUE)"),
    ("Total Refunds", "Revenue", "$#,##0.00", f"SUM({FO}[total_refund_amount])"),
    ("Refund Rate %", "Revenue", "0.00%", "DIVIDE([Total Refunds], [Gross Revenue])"),
    ("Order Count", "Orders", "#,##0", f"CALCULATE(DISTINCTCOUNT({FO}[order_id]), {FO}[is_revenue_eligible] = TRUE)"),
    ("Avg Order Value", "Orders", "$#,##0.00", "DIVIDE([Net Revenue], [Order Count])"),
    ("Units Sold", "Products", "#,##0", f"CALCULATE(SUM({FOI}[quantity]), {FOI}[is_revenue_eligible] = TRUE)"),
    ("Category Net Revenue", "Products", "$#,##0.00", f"CALCULATE(SUM({FOI}[net_line_revenue]), {FOI}[is_revenue_eligible] = TRUE)"),
    ("Customer Count", "Customers", "#,##0", f"DISTINCTCOUNT({DC}[customer_id])"),
    ("Customer Lifetime Net Spend", "Customers", "$#,##0.00", f"SUM({DC}[lifetime_net_spend])"),
    ("Revenue per Customer", "Customers", "$#,##0.00", "DIVIDE([Net Revenue], [Customer Count])"),
    ("Units per Order", "Orders", "0.00", "DIVIDE([Units Sold], [Order Count])"),
]


def run(conn, script):
    AdomdCommand(json.dumps(script), conn).ExecuteNonQuery()


def list_measures(conn):
    reader = AdomdCommand("SELECT [Name] FROM $SYSTEM.TMSCHEMA_MEASURES", conn).ExecuteReader()
    names = []
    while reader.Read():
        names.append(str(reader[0]))
    reader.Close()
    return names


conn = AdomdConnection()
DATABASE = database_name()
CONN_STR = connection_string()
conn.ConnectionString = CONN_STR
conn.Open()

# delete existing KPI table if present
try:
    run(conn, {"delete": {"object": {"database": DATABASE, "table": "_KPI Measures"}}})
    print("Deleted existing _KPI Measures")
except Exception as e:
    print("Delete skip:", str(e)[:120])

measure_defs = [
    {
        "name": name,
        "expression": expr,
        "formatString": fmt,
        "displayFolder": folder,
    }
    for name, folder, fmt, expr in MEASURES
]

create_script = {
    "create": {
        "parentObject": {"database": DATABASE},
        "table": {
            "name": "_KPI Measures",
            "isHidden": True,
            "measures": measure_defs,
            "partitions": [
                {
                    "name": "Partition",
                    "mode": "import",
                    "source": {
                        "type": "calculated",
                        "expression": 'ROW("Placeholder", BLANK())',
                    },
                }
            ],
        },
    }
}

try:
    run(conn, create_script)
    print("Created _KPI Measures with measures")
except Exception as e:
    print("Create failed:", e)

print("Measures:", list_measures(conn))
conn.Close()
