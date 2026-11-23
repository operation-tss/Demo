import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.;"
    "DATABASE=HealthCare_connect;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("\n--- HC_Timeline_Parameters ALL ROWS ---")
cursor.execute("SELECT id, Name, [Desc], is_active FROM dbo.HC_Timeline_Parameters")
for r in cursor.fetchall():
    print(f"  ID={r[0]}: Name='{r[1]}' | Desc='{r[2]}' | active={r[3]}")

conn.close()
