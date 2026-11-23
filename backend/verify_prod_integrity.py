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

cursor.execute("SELECT Mst_Patients_patient_id, Mst_Patients_first_name, Mst_Patients_last_name, Mst_Patients_registration_date FROM dbo.Mst_Patients WHERE Mst_Patients_last_name LIKE '%TEST%' OR Mst_Patients_last_name LIKE '%Sharma%'")
for r in cursor.fetchall():
    print(r)

cursor.execute("SELECT Mst_Patients_patient_id, Mst_Patients_first_name, Mst_Patients_last_name FROM dbo.Mst_Patients WHERE Mst_Patients_first_name = 'Rohan' AND Mst_Patients_last_name = 'Sharma TEST'")
rohan_test = cursor.fetchall()
print("Rohan Sharma TEST in prod:", rohan_test)

conn.close()
