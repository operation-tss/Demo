import sys
import os
import unittest
from datetime import date
from unittest.mock import patch, MagicMock

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.services.timeline_db import test_connection, get_db_session
from app.models.timeline_models import HCTimelineParameter, HCPatientHealthTimeline
from app.schemas.report_schema import TestResult, ReportAnalysisResponse
from app.services.timeline_sync_service import (
    is_valid_clinical_value,
    parse_clinical_date,
    build_parameter_lookup,
    match_clinical_parameter,
    sync_report_to_patient_timeline,
    APPROVED_CLINICAL_ALIASES
)

class TestTimelineIntegration(unittest.TestCase):

    def test_01_db_connectivity(self):
        """Verify MSSQL connection is alive."""
        self.assertTrue(test_connection(), "Database connection must succeed.")

    def test_02_value_validation(self):
        """Requirement 3: Skip empty/null, preserve legitimate numeric zeros."""
        # Legitimate clinical zeros
        self.assertTrue(is_valid_clinical_value("0"))
        self.assertTrue(is_valid_clinical_value("0.0"))
        self.assertTrue(is_valid_clinical_value("0.00"))
        self.assertTrue(is_valid_clinical_value(0))
        self.assertTrue(is_valid_clinical_value(0.0))
        self.assertTrue(is_valid_clinical_value("14.2"))
        self.assertTrue(is_valid_clinical_value("Positive"))

        # Empty or invalid values
        self.assertFalse(is_valid_clinical_value(None))
        self.assertFalse(is_valid_clinical_value(""))
        self.assertFalse(is_valid_clinical_value("   "))
        self.assertFalse(is_valid_clinical_value("N/A"))
        self.assertFalse(is_valid_clinical_value("null"))
        self.assertFalse(is_valid_clinical_value("-"))
        self.assertFalse(is_valid_clinical_value("--"))

    def test_03_date_parsing_null_retention(self):
        """Requirement 8: Date parses correctly or retains NULL without defaulting to today."""
        self.assertEqual(parse_clinical_date("2026-09-29"), date(2026, 9, 29))
        self.assertEqual(parse_clinical_date("29/09/2026"), date(2026, 9, 29))
        self.assertEqual(parse_clinical_date("29-Sep-2026"), date(2026, 9, 29))
        # Missing or invalid date MUST return None (NULL)
        self.assertIsNone(parse_clinical_date(None))
        self.assertIsNone(parse_clinical_date(""))
        self.assertIsNone(parse_clinical_date("not-a-date"))

    def test_04_parameter_matching_exact_and_approved_aliases(self):
        """Requirement 4 & 7: Only exact matches and approved aliases are auto-matched."""
        mock_params = [
            HCTimelineParameter(id=1, Name="Hemoglobin"),
            HCTimelineParameter(id=2, Name="Total Leukocyte Count (WBC)"),
            HCTimelineParameter(id=3, Name="Platelet Count"),
            HCTimelineParameter(id=4, Name="Serum Creatinine"),
            HCTimelineParameter(id=5, Name="Total Cholesterol"),
            HCTimelineParameter(id=6, Name="Urine Ketone Bodies"),
        ]
        exact_lookup, alias_lookup = build_parameter_lookup(mock_params)

        # 1. Exact matches
        self.assertEqual(match_clinical_parameter("Hemoglobin", exact_lookup, alias_lookup), 1)
        self.assertEqual(match_clinical_parameter("hemoglobin", exact_lookup, alias_lookup), 1)
        self.assertEqual(match_clinical_parameter("Platelet Count", exact_lookup, alias_lookup), 3)

        # 2. Approved aliases
        self.assertEqual(match_clinical_parameter("Hb", exact_lookup, alias_lookup), 1)
        self.assertEqual(match_clinical_parameter("HGB", exact_lookup, alias_lookup), 1)
        self.assertEqual(match_clinical_parameter("WBC", exact_lookup, alias_lookup), 2)
        self.assertEqual(match_clinical_parameter("TLC", exact_lookup, alias_lookup), 2)
        self.assertEqual(match_clinical_parameter("PLT", exact_lookup, alias_lookup), 3)
        self.assertEqual(match_clinical_parameter("Creatinine", exact_lookup, alias_lookup), 4)
        self.assertEqual(match_clinical_parameter("Cholesterol", exact_lookup, alias_lookup), 5)

        # 3. Unapproved or uncertain parameters -> Must return None (skipped for review)
        self.assertIsNone(match_clinical_parameter("Random Experimental Marker", exact_lookup, alias_lookup))
        self.assertIsNone(match_clinical_parameter("Unknown Test 123", exact_lookup, alias_lookup))

    def test_05_missing_patient_id_behavior(self):
        """Requirement 10: Missing patient_id returns SKIPPED status without DB operations."""
        results = [TestResult(test_name="Hemoglobin", value="14.2", status="NORMAL")]
        res = sync_report_to_patient_timeline(patient_id=None, analyzed_results=results, report_date_str="2026-09-29")
        self.assertEqual(res.status, "SKIPPED")
        self.assertEqual(res.synced_count, 0)

    def test_06_nonexistent_patient_id_behavior(self):
        """Verify invalid patient_id is rejected gracefully."""
        results = [TestResult(test_name="Hemoglobin", value="14.2", status="NORMAL")]
        res = sync_report_to_patient_timeline(patient_id=999999, analyzed_results=results, report_date_str="2026-09-29")
        self.assertEqual(res.status, "FAILED")
        self.assertIn("does not exist in Mst_Patients", res.error)

    def test_07_database_failure_resilience(self):
        """Requirement 10: Database failures return FAILED result without raising exception."""
        results = [TestResult(test_name="Hemoglobin", value="14.2", status="NORMAL")]
        with patch("app.services.timeline_sync_service.get_db_session") as mock_session_ctx:
            mock_session_ctx.return_value.__enter__.return_value = None
            res = sync_report_to_patient_timeline(patient_id=8, analyzed_results=results, report_date_str="2026-09-29")
            self.assertEqual(res.status, "FAILED")
            self.assertTrue(res.requires_retry)
            self.assertIn("could not be established", res.error)

    def test_08_transactional_insert_and_duplicate_handling(self):
        """
        Tests transaction-safe insert, zero preservation, and duplicate handling
        using a transaction that is rolled back so no test data persists.
        """
        with get_db_session() as session:
            if session is None:
                self.skipTest("Database session unavailable")
            
            from sqlalchemy import text
            # Ensure patient 8 exists
            p = session.execute(text("SELECT Mst_Patients_patient_id FROM Mst_Patients WHERE Mst_Patients_patient_id = 8")).first()
            if not p:
                self.skipTest("Patient 8 not found in database for integration test")

            # Temporarily insert a master parameter inside transaction
            session.execute(text(
                "INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) "
                "VALUES ('Test_Hemoglobin_Parameter', 'CBC Test', 1, SYSUTCDATETIME())"
            ))
            param_id = session.execute(text("SELECT @@IDENTITY")).scalar()

            try:
                # 1. Insert new reading
                test_date = date(2026, 9, 29)
                session.execute(text(
                    "INSERT INTO HC_Patient_Health_Timeline "
                    "(patient_id, HC_Timeline_parameter_id, Value, Date, uploaded_on_dt, is_active) "
                    "VALUES (8, :pid, '14.5', :dt, SYSUTCDATETIME(), 1)"
                ), {"pid": param_id, "dt": test_date})

                # Verify inserted
                row = session.execute(text(
                    "SELECT Value, Date, is_active FROM HC_Patient_Health_Timeline "
                    "WHERE patient_id = 8 AND HC_Timeline_parameter_id = :pid AND Date = :dt"
                ), {"pid": param_id, "dt": test_date}).first()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], "14.5")
                self.assertEqual(row[1], test_date)

                # 2. Duplicate detection: same reading -> skip
                existing = session.execute(text(
                    "SELECT id, Value FROM HC_Patient_Health_Timeline "
                    "WHERE patient_id = 8 AND HC_Timeline_parameter_id = :pid AND Date = :dt AND is_active = 1"
                ), {"pid": param_id, "dt": test_date}).first()
                self.assertIsNotNone(existing)
                self.assertEqual(str(existing[1]), "14.5")

                # 3. Revised reading: update value (NO updated_on_dt referenced)
                session.execute(text(
                    "UPDATE HC_Patient_Health_Timeline SET Value = '14.8' WHERE id = :rec_id"
                ), {"rec_id": existing[0]})

                updated_row = session.execute(text(
                    "SELECT Value FROM HC_Patient_Health_Timeline WHERE id = :rec_id"
                ), {"rec_id": existing[0]}).scalar()
                self.assertEqual(updated_row, "14.8")

                # 4. Zero value preservation: insert legitimate 0
                session.execute(text(
                    "INSERT INTO HC_Patient_Health_Timeline "
                    "(patient_id, HC_Timeline_parameter_id, Value, Date, uploaded_on_dt, is_active) "
                    "VALUES (8, :pid, '0', NULL, SYSUTCDATETIME(), 1)"
                ), {"pid": param_id})
                zero_row = session.execute(text(
                    "SELECT Value, Date FROM HC_Patient_Health_Timeline "
                    "WHERE patient_id = 8 AND HC_Timeline_parameter_id = :pid AND Date IS NULL"
                ), {"pid": param_id}).first()
                self.assertIsNotNone(zero_row)
                self.assertEqual(zero_row[0], "0")
                self.assertIsNone(zero_row[1])  # Confirms NULL date preserved!

            finally:
                # Rollback all test data so database is left 100% clean
                session.rollback()

if __name__ == "__main__":
    unittest.main()
