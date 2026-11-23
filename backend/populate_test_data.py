import pyodbc
from datetime import datetime, date

def populate_test_data():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.;"
        "DATABASE=HealthCare_connect_test;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    
    # SAFETY CHECK: Verify we are strictly connected to HealthCare_connect_test
    cursor.execute("SELECT DB_NAME()")
    current_db = cursor.fetchone()[0]
    if current_db != "HealthCare_connect_test":
        raise RuntimeError(f"FATAL SAFETY ABORT: Connected to '{current_db}' instead of 'HealthCare_connect_test'!")
    print(f"Safety verified: Working strictly in isolated database '{current_db}'.")

    # 1. Check or insert synthetic test patient: Rohan Sharma TEST
    cursor.execute("SELECT Mst_Patients_patient_id FROM dbo.Mst_Patients WHERE Mst_Patients_last_name = 'Sharma TEST'")
    existing_patient = cursor.fetchone()
    
    if existing_patient:
        patient_id = existing_patient[0]
        print(f"Found existing synthetic test patient with ID: {patient_id}")
    else:
        cursor.execute("""
            INSERT INTO dbo.Mst_Patients (
                Mst_Patients_health_id,
                Mst_Patients_aadhar_number,
                Mst_Patients_first_name,
                Mst_Patients_last_name,
                Mst_Patients_date_of_birth,
                Mst_Patients_gender,
                Mst_Patients_blood_group,
                Mst_Patients_phone_primary,
                Mst_Patients_phone_secondary,
                Mst_Patients_email,
                Mst_Patients_address_line1,
                Mst_Patients_address_line2,
                Mst_Patients_city,
                Mst_Patients_state,
                Mst_Patients_pincode,
                Mst_Patients_registration_date,
                Mst_Patients_CreateonDateUTC,
                Mst_Patients_updatedonDateUTC,
                Mst_Patients_is_active
            )
            OUTPUT INSERTED.Mst_Patients_patient_id
            VALUES (
                'HC-TEST-ROHAN-1',
                '000000000001',
                'Rohan',
                'Sharma TEST',
                '1995-05-15',
                'Male',
                'B+',
                '9999999999',
                '9999999998',
                'rohan.test@healthcareconnect.local',
                'Synthetic Test Laboratory Suite 101',
                'Isolated Testing Zone',
                'TestCity',
                'TestState',
                '110001',
                GETUTCDATE(),
                GETUTCDATE(),
                GETUTCDATE(),
                1
            )
        """)
        patient_id = cursor.fetchone()[0]
        print(f"Inserted synthetic test patient 'Rohan Sharma TEST' with ID: {patient_id}")

    # 2. 10 Chronological Dates
    test_dates = [
        "2026-11-01",
        "2026-11-03",
        "2026-11-05",
        "2026-11-07",
        "2026-11-09",
        "2026-11-11",
        "2026-11-13",
        "2026-11-15",
        "2026-11-17",
        "2026-11-19",
    ]

    # Map parameter names to ID
    cursor.execute("SELECT id, Name FROM dbo.HC_Timeline_Parameters")
    param_map = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"Loaded {len(param_map)} parameter mappings from test catalog.")

    # Parameters to test with 10 values each
    parameters_data = {
        "Hemoglobin": {
            "id": param_map.get("Hemoglobin", 5),
            "values": ["13.2", "13.5", "13.8", "14.1", "14.0", "14.4", "14.2", "14.7", "14.5", "14.8"]
        },
        "Total RBC Count": {
            "id": param_map.get("Total RBC Count", 6),
            "values": ["4.30", "4.45", "4.60", "4.70", "4.65", "4.80", "4.75", "4.90", "4.85", "5.00"]
        },
        "Total Leukocyte Count (WBC)": {
            "id": param_map.get("Total Leukocyte Count (WBC)", 12),
            "values": ["6200", "6500", "6800", "7100", "6900", "7300", "7150", "7500", "7400", "7600"]
        },
        "MCV": {
            "id": param_map.get("MCV", 8),
            "values": ["84.0", "84.8", "85.5", "86.2", "86.0", "87.1", "86.8", "87.5", "87.2", "88.0"]
        },
        "MCH": {
            "id": param_map.get("MCH", 9),
            "values": ["28.2", "28.7", "29.1", "29.5", "29.3", "30.0", "29.8", "30.2", "30.1", "30.5"]
        },
        "Platelet Count": {
            "id": param_map.get("Platelet Count", 18),
            "values": ["220000", "230000", "240000", "250000", "245000", "260000", "255000", "270000", "265000", "280000"]
        },
        "Packed Cell Volume (PCV)": {
            "id": param_map.get("Packed Cell Volume (PCV)", 7),
            "values": ["39.5", "40.2", "41.0", "42.1", "41.8", "43.0", "42.6", "43.5", "43.2", "44.0"]
        }
    }

    # Clean existing timeline entries for this test patient in test db
    cursor.execute("DELETE FROM dbo.HC_Patient_Health_Timeline WHERE patient_id = ?", patient_id)
    cursor.execute("DELETE FROM dbo.Mst_PatientReports WHERE Mst_PatientReports_patient_id = ?", patient_id)

    # 3. Insert 10 chronological readings for each parameter
    timeline_inserted = 0
    for param_name, info in parameters_data.items():
        param_id = info["id"]
        vals = info["values"]
        for dt, val in zip(test_dates, vals):
            cursor.execute("""
                INSERT INTO dbo.HC_Patient_Health_Timeline (
                    patient_id,
                    HC_Timeline_parameter_id,
                    Value,
                    Date,
                    uploaded_on_dt,
                    is_active
                ) VALUES (?, ?, ?, ?, GETUTCDATE(), 1)
            """, (patient_id, param_id, val, dt))
            timeline_inserted += 1

    print(f"Inserted {timeline_inserted} synthetic parameter timeline records across {len(test_dates)} dates.")

    # 4. Insert 10 synthetic medical reports corresponding to each date
    reports_inserted = 0
    for dt in test_dates:
        formatted_date = datetime.strptime(dt, "%Y-%m-%d").strftime("%d%b%Y")
        cursor.execute("""
            INSERT INTO dbo.Mst_PatientReports (
                Mst_PatientReports_patient_id,
                Mst_PatientReports_report_type,
                Mst_PatientReports_report_category,
                Mst_PatientReports_report_date,
                Mst_PatientReports_report_title,
                Mst_PatientReports_report_description,
                Mst_PatientReports_findings,
                Mst_PatientReports_report_file_path,
                Mst_PatientReports_file_type,
                Mst_PatientReports_uploaded_by,
                Mst_PatientReports_CreateonDateUTC,
                Mst_PatientReports_is_critical
            ) VALUES (
                ?,
                'Lab Report',
                'Complete Blood Count',
                ?,
                ?,
                'Synthetic Automated Test Report for Timeline Graph Verification',
                'All hematological indices within synthetic test tolerances.',
                ?,
                'pdf',
                'System Automated Test Runner',
                GETUTCDATE(),
                0
            )
        """, (
            patient_id,
            dt,
            f"CBC Lab Report - {formatted_date}",
            f"uploads/reports/synthetic_cbc_{dt}.pdf"
        ))
        reports_inserted += 1

    print(f"Inserted {reports_inserted} synthetic report document records for test dates.")

    # 5. Summary verification count
    cursor.execute("SELECT COUNT(*) FROM dbo.Mst_Patients WHERE Mst_Patients_is_active = 1")
    total_pts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dbo.HC_Patient_Health_Timeline WHERE is_active = 1")
    total_tl = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dbo.Mst_PatientReports")
    total_reps = cursor.fetchone()[0]

    print("\n--- ISOLATED TEST DATABASE SUMMARY ---")
    print(f"Database: HealthCare_connect_test")
    print(f"Test Patient ID: {patient_id} ('Rohan Sharma TEST')")
    print(f"Total Active Patients: {total_pts}")
    print(f"Total Timeline Records: {total_tl}")
    print(f"Total Patient Reports: {total_reps}")
    print(f"Dates Count: {len(test_dates)}")
    print("--------------------------------------\n")

    conn.close()

if __name__ == '__main__':
    populate_test_data()
