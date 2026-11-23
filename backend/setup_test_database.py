import pyodbc
import sys

def main():
    print("--- 1. Connecting to SQL Server master database ---")
    conn_master_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.;"
        "DATABASE=master;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    
    try:
        conn_master = pyodbc.connect(conn_master_str, autocommit=True)
        cursor_master = conn_master.cursor()
        
        cursor_master.execute("SELECT name FROM sys.databases WHERE name = 'HealthCare_connect_test'")
        exists = cursor_master.fetchone()
        if not exists:
            print("Creating database HealthCare_connect_test...")
            cursor_master.execute("CREATE DATABASE HealthCare_connect_test")
            print("Successfully created database HealthCare_connect_test!")
        else:
            print("Database HealthCare_connect_test already exists.")
        conn_master.close()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to create HealthCare_connect_test: {e}")
        sys.exit(1)

    print("\n--- 2. Connecting to HealthCare_connect_test ---")
    conn_test_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.;"
        "DATABASE=HealthCare_connect_test;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    conn_test = pyodbc.connect(conn_test_str, autocommit=True)
    cursor_test = conn_test.cursor()

    # Get all tables from production HealthCare_connect
    conn_prod_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.;"
        "DATABASE=HealthCare_connect;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    conn_prod = pyodbc.connect(conn_prod_str)
    cursor_prod = conn_prod.cursor()
    cursor_prod.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")
    prod_tables = [r[0] for r in cursor_prod.fetchall()]
    conn_prod.close()

    print(f"Cloning schemas for {len(prod_tables)} tables from HealthCare_connect to HealthCare_connect_test...")
    cloned_count = 0
    for tbl in prod_tables:
        cursor_test.execute(f"SELECT OBJECT_ID(N'dbo.[{tbl}]')")
        if cursor_test.fetchone()[0] is None:
            sql = f"SELECT * INTO HealthCare_connect_test.dbo.[{tbl}] FROM HealthCare_connect.dbo.[{tbl}] WHERE 1=0"
            cursor_test.execute(sql)
            cloned_count += 1

    print(f"Cloned {cloned_count} tables into HealthCare_connect_test.")

    # Copy HC_Timeline_Parameters metadata
    cursor_test.execute("SELECT COUNT(*) FROM HealthCare_connect_test.dbo.HC_Timeline_Parameters")
    param_count = cursor_test.fetchone()[0]
    if param_count == 0:
        print("Copying HC_Timeline_Parameters master catalog...")
        cursor_test.execute("SET IDENTITY_INSERT HealthCare_connect_test.dbo.HC_Timeline_Parameters ON")
        cursor_test.execute("""
            INSERT INTO HealthCare_connect_test.dbo.HC_Timeline_Parameters 
            (id, Name, [Desc], is_active, created_on_dt, updated_on_dt)
            SELECT id, Name, [Desc], is_active, created_on_dt, updated_on_dt
            FROM HealthCare_connect.dbo.HC_Timeline_Parameters
        """)
        cursor_test.execute("SET IDENTITY_INSERT HealthCare_connect_test.dbo.HC_Timeline_Parameters OFF")
        cursor_test.execute("SELECT COUNT(*) FROM HealthCare_connect_test.dbo.HC_Timeline_Parameters")
        new_param_count = cursor_test.fetchone()[0]
        print(f"Copied {new_param_count} standard parameter definitions.")
    else:
        print(f"HC_Timeline_Parameters already has {param_count} parameter rows.")

    conn_test.close()
    print("Database setup completed successfully.")

if __name__ == '__main__':
    main()
