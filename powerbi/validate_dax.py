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

from pbi_connection import connection_string

QUERIES = {
    "kpi_totals": """
EVALUATE ROW(
    "Net Revenue", [Net Revenue],
    "Gross Revenue", [Gross Revenue],
    "Total Refunds", [Total Refunds],
    "Order Count", [Order Count],
    "Customer Count", [Customer Count],
    "Units Sold", [Units Sold]
)""",
    "geo_country": """
EVALUATE
SUMMARIZECOLUMNS(
    'ecommerce_marts dim_customers'[country],
    "Net Revenue", [Net Revenue],
    "Customer Count", [Customer Count]
)
ORDER BY [Net Revenue] DESC""",
    "geo_city": """
EVALUATE
TOPN(
    10,
    SUMMARIZECOLUMNS(
        'ecommerce_marts dim_customers'[country],
        'ecommerce_marts dim_customers'[city],
        "Net Revenue", [Net Revenue],
        "Customers", [Customer Count]
    ),
    [Net Revenue], DESC
)""",
}

conn = AdomdConnection()
conn.ConnectionString = connection_string()
conn.Open()

for name, dax in QUERIES.items():
    print(f"\n=== {name} ===")
    cmd = AdomdCommand(dax, conn)
    reader = cmd.ExecuteReader()
    cols = [reader.GetName(i) for i in range(reader.FieldCount)]
    print(cols)
    while reader.Read():
        print([reader[i] for i in range(reader.FieldCount)])
    reader.Close()

conn.Close()
