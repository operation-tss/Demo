import os
import sys
from datetime import date, timedelta
from sqlalchemy import text

sys.path.insert(0, os.path.abspath('.'))
os.environ['USE_TEST_DB'] = '1'
os.environ['DATABASE_NAME'] = 'HealthCare_connect_test'

from backend.app.services.timeline_db import get_engine, reset_engine

reset_engine()
engine = get_engine()

with engine.connect() as conn:
    db_name = conn.execute(text("SELECT DB_NAME()")).scalar()
    print(f"Connecting to database: {db_name}")
    assert db_name == "HealthCare_connect_test", f"SAFETY CHECK FAILED: Expected HealthCare_connect_test, got {db_name}!"

    # Verify patient 1 is indeed the synthetic test patient
    p_info = conn.execute(text("""
        SELECT Mst_Patients_patient_id, Mst_Patients_health_id, 
               CONCAT(Mst_Patients_first_name, ' ', Mst_Patients_last_name) AS name
        FROM Mst_Patients WHERE Mst_Patients_patient_id = 1
    """)).first()
    print(f"Target Patient: {p_info}")
    assert "TEST" in str(p_info[1]) or "TEST" in str(p_info[2]), "SAFETY CHECK FAILED: Patient is not a TEST patient!"

    # Check Hemoglobin param ID
    hb_param = conn.execute(text("SELECT id, Name FROM HC_Timeline_Parameters WHERE Name = 'Hemoglobin' AND is_active = 1")).first()
    param_id = hb_param[0]
    print(f"Hemoglobin parameter id: {param_id}")

    # Generate 95 dates from 2025-01-01 onwards
    start_dt = date(2025, 1, 1)
    values_cycle = [
        13.8, 14.1, 14.2, 14.0, 14.3, 14.5, 14.4, 14.6, 14.8, 14.7,
        14.9, 15.0, 15.1, 14.9, 14.8, 14.6, 14.5, 14.3, 14.1, 14.0,
        13.9, 14.0, 14.2, 14.4, 14.5, 14.7, 14.9, 15.1, 15.2, 15.0,
        14.8, 14.6, 14.4, 14.3, 14.1, 14.0, 13.9, 13.8, 13.9, 14.1
    ]

    inserted_count = 0
    # Specifically include 2025-01-08
    # Days 0 to 94 (95 distinct days)
    for i in range(95):
        r_date = start_dt + timedelta(days=i)
        val = values_cycle[i % len(values_cycle)]

        # Check if already exists
        exists = conn.execute(text("""
            SELECT id FROM HC_Patient_Health_Timeline
            WHERE patient_id = 1 AND HC_Timeline_parameter_id = :pid AND Date = :r_date
        """), {"pid": param_id, "r_date": r_date}).first()

        if not exists:
            # Notice: r_date is in 2025 (e.g. 2025-01-08)
            # uploaded_on_dt is SYSUTCDATETIME() (current timestamp in 2026)
            conn.execute(text("""
                INSERT INTO HC_Patient_Health_Timeline
                (patient_id, HC_Timeline_parameter_id, Value, Date, uploaded_on_dt, is_active)
                VALUES (1, :pid, :val, :r_date, SYSUTCDATETIME(), 1)
            """), {
                "pid": param_id,
                "val": str(val),
                "r_date": r_date
            })
            inserted_count += 1

    conn.commit()
    print(f"Successfully inserted {inserted_count} historical readings for Hemoglobin.")

    # Check total Hemoglobin readings
    total_hb = conn.execute(text("SELECT COUNT(*) FROM HC_Patient_Health_Timeline WHERE patient_id = 1 AND HC_Timeline_parameter_id = :pid"), {"pid": param_id}).scalar()
    print(f"Total Hemoglobin readings for patient 1: {total_hb}")

    # Verify report dated 2025-01-08 has distinct upload date
    sample_rec = conn.execute(text("""
        SELECT id, Date, uploaded_on_dt, Value FROM HC_Patient_Health_Timeline
        WHERE patient_id = 1 AND HC_Timeline_parameter_id = :pid AND Date = '2025-01-08'
    """), {"pid": param_id}).first()
    print(f"Verified sample record (2025-01-08): Date={sample_rec[1]}, uploaded_on_dt={sample_rec[2]}, Value={sample_rec[3]}")
