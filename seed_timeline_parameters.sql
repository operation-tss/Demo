-- =========================================================================================
-- Healthcare Connect: Master Clinical Parameters Seed Script
-- Target Table: HC_Timeline_Parameters
-- Parameters: Exactly 63 Supported Laboratory Tests
-- Idempotency: Individual IF NOT EXISTS checks per parameter Name
-- Safety: Enclosed in BEGIN TRANSACTION / TRY...CATCH with automatic rollback on error
-- =========================================================================================

USE HealthCare_connect;
GO

SET NOCOUNT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- 1. Complete Blood Count (CBC) - 14 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Hemoglobin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Hemoglobin', 'CBC - Red blood cell oxygen-carrying protein (g/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Total RBC Count')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Total RBC Count', 'CBC - Total erythrocyte count (mil/uL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Packed Cell Volume (PCV)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Packed Cell Volume (PCV)', 'CBC - Percentage of blood volume occupied by erythrocytes (%)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'MCV')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('MCV', 'CBC - Mean corpuscular volume (fL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'MCH')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('MCH', 'CBC - Mean corpuscular hemoglobin (pg)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'MCHC')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('MCHC', 'CBC - Mean corpuscular hemoglobin concentration (g/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'RDW')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('RDW', 'CBC - Red cell distribution width (%)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Total Leukocyte Count (WBC)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Total Leukocyte Count (WBC)', 'CBC - Total white blood cell count (/uL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Neutrophils')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Neutrophils', 'CBC - Granulocytic neutrophils differential (%)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Lymphocytes')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Lymphocytes', 'CBC - Agranulocytic lymphocytes differential (%)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Monocytes')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Monocytes', 'CBC - Monocyte differential (%)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Eosinophils')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Eosinophils', 'CBC - Eosinophil differential (%)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Basophils')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Basophils', 'CBC - Basophil differential (%)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Platelet Count')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Platelet Count', 'CBC - Thrombocyte count (/uL)', 1, SYSUTCDATETIME());

    -- 2. Liver Function Test (LFT) - 11 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Total Bilirubin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Total Bilirubin', 'LFT - Serum total bilirubin (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Direct Bilirubin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Direct Bilirubin', 'LFT - Conjugated direct bilirubin (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Indirect Bilirubin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Indirect Bilirubin', 'LFT - Unconjugated indirect bilirubin (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'SGOT / AST')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('SGOT / AST', 'LFT - Aspartate aminotransferase (U/L)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'SGPT / ALT')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('SGPT / ALT', 'LFT - Alanine aminotransferase (U/L)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Alkaline Phosphatase (ALP)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Alkaline Phosphatase (ALP)', 'LFT - Serum alkaline phosphatase (U/L)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Total Protein')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Total Protein', 'LFT - Serum total protein (g/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Albumin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Albumin', 'LFT - Serum albumin level (g/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Globulin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Globulin', 'LFT - Serum globulin level (g/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'A/G Ratio')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('A/G Ratio', 'LFT - Albumin to globulin ratio (ratio)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'GGT')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('GGT', 'LFT - Gamma-glutamyl transferase (U/L)', 1, SYSUTCDATETIME());

    -- 3. Kidney Function Test (KFT) - 5 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Blood Urea')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Blood Urea', 'KFT - Serum urea concentration (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Blood Urea Nitrogen (BUN)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Blood Urea Nitrogen (BUN)', 'KFT - Blood urea nitrogen (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Serum Creatinine')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Serum Creatinine', 'KFT - Serum creatinine level (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Uric Acid')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Uric Acid', 'KFT - Serum uric acid (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'eGFR')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('eGFR', 'KFT - Estimated glomerular filtration rate (mL/min/1.73m2)', 1, SYSUTCDATETIME());

    -- 4. Lipid Profile - 6 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Total Cholesterol')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Total Cholesterol', 'Lipid - Total serum cholesterol (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Triglycerides')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Triglycerides', 'Lipid - Serum triglycerides (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'HDL Cholesterol')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('HDL Cholesterol', 'Lipid - High-density lipoprotein cholesterol (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'LDL Cholesterol')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('LDL Cholesterol', 'Lipid - Low-density lipoprotein cholesterol (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'VLDL Cholesterol')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('VLDL Cholesterol', 'Lipid - Very low-density lipoprotein cholesterol (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'TC / HDL Ratio')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('TC / HDL Ratio', 'Lipid - Total cholesterol to HDL ratio (ratio)', 1, SYSUTCDATETIME());

    -- 5. Thyroid Profile - 5 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'TSH')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('TSH', 'Thyroid - Thyroid stimulating hormone (uIU/mL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Free T3')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Free T3', 'Thyroid - Free triiodothyronine (pg/mL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Free T4')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Free T4', 'Thyroid - Free thyroxine (ng/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Total T3')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Total T3', 'Thyroid - Total triiodothyronine (ng/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Total T4')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Total T4', 'Thyroid - Total thyroxine (ug/dL)', 1, SYSUTCDATETIME());

    -- 6. Blood Glucose & Diabetes - 4 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Fasting Blood Sugar (FBS)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Fasting Blood Sugar (FBS)', 'Diabetes - Fasting plasma glucose (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Post Prandial Blood Sugar (PPBS)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Post Prandial Blood Sugar (PPBS)', 'Diabetes - Postprandial plasma glucose (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Random Blood Sugar (RBS)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Random Blood Sugar (RBS)', 'Diabetes - Random plasma glucose (mg/dL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'HbA1c')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('HbA1c', 'Diabetes - Glycated hemoglobin (%)', 1, SYSUTCDATETIME());

    -- 7. Nutritional Vitamins - 2 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Vitamin B12')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Vitamin B12', 'Vitamins - Serum cobalamin level (pg/mL)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Vitamin D (25-OH)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Vitamin D (25-OH)', 'Vitamins - 25-hydroxy vitamin D (ng/mL)', 1, SYSUTCDATETIME());

    -- 8. Serum Electrolytes & Minerals - 4 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Serum Sodium')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Serum Sodium', 'Electrolytes - Serum sodium cation (mEq/L)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Serum Potassium')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Serum Potassium', 'Electrolytes - Serum potassium cation (mEq/L)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Serum Chloride')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Serum Chloride', 'Electrolytes - Serum chloride anion (mEq/L)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Serum Calcium')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Serum Calcium', 'Minerals - Total serum calcium (mg/dL)', 1, SYSUTCDATETIME());

    -- 9. Urine Routine Examination - 9 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine Specific Gravity')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine Specific Gravity', 'Urine - Physical specific gravity / concentration', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine pH / Reaction')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine pH / Reaction', 'Urine - Chemical acidity/alkalinity reaction', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine Protein / Albumin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine Protein / Albumin', 'Urine - Qualitative protein/albumin screen', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine Glucose / Sugar')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine Glucose / Sugar', 'Urine - Qualitative glucose/sugar screen', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine Ketone Bodies')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine Ketone Bodies', 'Urine - Qualitative ketone bodies screen', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine Pus Cells (WBC)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine Pus Cells (WBC)', 'Urine Microscopy - Leukocytes / pus cells (/HPF)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine RBCs')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine RBCs', 'Urine Microscopy - Red blood cells (/HPF)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urine Epithelial Cells')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urine Epithelial Cells', 'Urine Microscopy - Squamous epithelial cells (/HPF)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Urobilinogen')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Urobilinogen', 'Urine - Biliary metabolite excretion (mg/dL)', 1, SYSUTCDATETIME());

    -- 10. Inflammatory & Routine Serology - 3 Parameters
    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'ESR (Erythrocyte Sedimentation Rate)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('ESR (Erythrocyte Sedimentation Rate)', 'Hematology - Erythrocyte sedimentation rate (mm/hr)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'C-Reactive Protein (CRP)')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('C-Reactive Protein (CRP)', 'Serology - C-reactive protein acute inflammation (mg/L)', 1, SYSUTCDATETIME());

    IF NOT EXISTS (SELECT 1 FROM HC_Timeline_Parameters WHERE Name = 'Serum Ferritin')
        INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt) VALUES ('Serum Ferritin', 'Iron Studies - Serum ferritin iron store level (ng/mL)', 1, SYSUTCDATETIME());

    COMMIT TRANSACTION;
    PRINT 'SUCCESS: 63 master clinical parameters processed idempotently into HC_Timeline_Parameters.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @ErrSeverity INT = ERROR_SEVERITY();
    RAISERROR(@ErrMsg, @ErrSeverity, 1);
END CATCH;
GO
