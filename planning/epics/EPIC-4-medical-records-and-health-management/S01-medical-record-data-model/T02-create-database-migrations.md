---
epic: EPIC-4
story: S01
task: T02
title: Create Database Migrations
status: todo
priority: high
complexity: 7
---

# T02: Create Database Migrations

## Overview
Create Supabase migrations for all medical record schema tables, including versioned migration files, rollback support, and seed data for testing.

## Acceptance Criteria
- [ ] Migration files created with proper naming convention
- [ ] All DDL statements properly formatted and documented
- [ ] Rollback migrations (down) created for all changes
- [ ] Migration executes without errors
- [ ] Seed data created for testing medical records workflow
- [ ] RLS policies applied in migration
- [ ] Index creation included in migration
- [ ] Documentation of migration changes

## Technical Implementation

### Migration File Structure

Supabase migrations use timestamp-based naming:
```
supabase/migrations/
├── 20260325_init_medical_records.sql
├── 20260325_add_vaccinations_table.sql
├── 20260325_add_medications_table.sql
├── 20260325_add_diagnoses_table.sql
├── 20260325_add_medical_documents_table.sql
├── 20260325_create_medical_indexes.sql
├── 20260325_enable_rls_medical_records.sql
└── 20260325_seed_test_medical_data.sql
```

### Main Migration: 20260325_init_medical_records.sql

```sql
-- Create medical_records table
CREATE TABLE IF NOT EXISTS medical_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  recorded_by UUID NOT NULL REFERENCES auth.users(id),
  visit_date TIMESTAMP WITH TIME ZONE NOT NULL,
  visit_type VARCHAR(50) NOT NULL CHECK (visit_type IN ('routine', 'emergency', 'surgery', 'checkup')),
  veterinarian_name VARCHAR(255),
  clinic_name VARCHAR(255),
  diagnosis TEXT,
  treatment_plan TEXT,
  notes TEXT,
  status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'archived')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID NOT NULL REFERENCES auth.users(id),
  updated_by UUID NOT NULL REFERENCES auth.users(id)
);

-- Create vaccinations table
CREATE TABLE IF NOT EXISTS vaccinations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  vaccine_name VARCHAR(255) NOT NULL,
  vaccine_type VARCHAR(100),
  administered_date DATE NOT NULL,
  expiry_date DATE,
  administered_by UUID REFERENCES auth.users(id),
  batch_number VARCHAR(100),
  clinic_name VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create medications table
CREATE TABLE IF NOT EXISTS medications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
  medication_name VARCHAR(255) NOT NULL,
  dosage VARCHAR(100) NOT NULL,
  frequency VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE,
  prescriber_name VARCHAR(255),
  indication TEXT,
  side_effects TEXT,
  notes TEXT,
  status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'discontinued')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create diagnoses table
CREATE TABLE IF NOT EXISTS diagnoses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
  condition_name VARCHAR(255) NOT NULL,
  icd_code VARCHAR(50),
  severity VARCHAR(50) CHECK (severity IN ('mild', 'moderate', 'severe')),
  diagnosis_date DATE NOT NULL,
  resolved_date DATE,
  description TEXT,
  treatment_plan TEXT,
  status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'monitoring')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create medical_documents table
CREATE TABLE IF NOT EXISTS medical_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
  document_type VARCHAR(100) NOT NULL CHECK (document_type IN ('lab_result', 'xray', 'ultrasound', 'prescription', 'vaccine_certificate')),
  document_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_size INT,
  mime_type VARCHAR(100),
  uploaded_by UUID NOT NULL REFERENCES auth.users(id),
  upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  document_date DATE,
  description TEXT,
  tags TEXT[],
  storage_bucket VARCHAR(100) DEFAULT 'medical-documents',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE medical_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE vaccinations ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_documents ENABLE ROW LEVEL SECURITY;

-- Create indexes for performance
CREATE INDEX idx_medical_records_animal_id ON medical_records(animal_id);
CREATE INDEX idx_medical_records_visit_date ON medical_records(visit_date DESC);
CREATE INDEX idx_medical_records_status ON medical_records(status);
CREATE INDEX idx_medical_records_created_by ON medical_records(created_by);

CREATE INDEX idx_vaccinations_animal_id ON vaccinations(animal_id);
CREATE INDEX idx_vaccinations_expiry_date ON vaccinations(expiry_date);
CREATE INDEX idx_vaccinations_vaccine_type ON vaccinations(vaccine_type);

CREATE INDEX idx_medications_animal_id ON medications(animal_id);
CREATE INDEX idx_medications_status ON medications(status);
CREATE INDEX idx_medications_start_date ON medications(start_date);

CREATE INDEX idx_diagnoses_animal_id ON diagnoses(animal_id);
CREATE INDEX idx_diagnoses_status ON diagnoses(status);
CREATE INDEX idx_diagnoses_condition ON diagnoses(condition_name);

CREATE INDEX idx_medical_documents_animal_id ON medical_documents(animal_id);
CREATE INDEX idx_medical_documents_type ON medical_documents(document_type);
CREATE INDEX idx_medical_documents_uploaded_by ON medical_documents(uploaded_by);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_medical_records_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  NEW.updated_by = auth.uid();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER medical_records_updated_at_trigger
BEFORE UPDATE ON medical_records
FOR EACH ROW
EXECUTE FUNCTION update_medical_records_updated_at();

CREATE OR REPLACE FUNCTION update_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER vaccinations_updated_at_trigger
BEFORE UPDATE ON vaccinations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();

CREATE TRIGGER medications_updated_at_trigger
BEFORE UPDATE ON medications
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();

CREATE TRIGGER diagnoses_updated_at_trigger
BEFORE UPDATE ON diagnoses
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();

CREATE TRIGGER medical_documents_updated_at_trigger
BEFORE UPDATE ON medical_documents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();
```

### RLS Policies Migration: 20260325_enable_rls_medical_records.sql

```sql
-- Medical Records RLS Policies
CREATE POLICY "Staff can view all records" ON medical_records
  FOR SELECT USING (
    auth.jwt() -> 'user_metadata' ->> 'role' IN ('admin', 'staff', 'vet')
  );

CREATE POLICY "Vets can manage all records" ON medical_records
  FOR ALL USING (
    auth.jwt() -> 'user_metadata' ->> 'role' = 'vet'
  );

CREATE POLICY "Adopters view only own animals" ON medical_records
  FOR SELECT USING (
    animal_id IN (
      SELECT animal_id FROM adoptions
      WHERE adopter_id = auth.uid() AND status = 'active'
    )
  );

CREATE POLICY "Fosters view own animals" ON medical_records
  FOR SELECT USING (
    animal_id IN (
      SELECT animal_id FROM foster_assignments
      WHERE foster_id = auth.uid() AND status = 'active'
    )
  );

CREATE POLICY "Volunteers view summary only" ON medical_records
  FOR SELECT USING (
    auth.jwt() -> 'user_metadata' ->> 'role' = 'volunteer'
  );

-- Apply similar policies to vaccinations, medications, diagnoses, medical_documents
-- ... (same pattern for each table)
```

### Seed Data Migration: 20260325_seed_test_medical_data.sql

```sql
-- Insert test data for development and testing
INSERT INTO medical_records (animal_id, recorded_by, visit_date, visit_type, veterinarian_name, clinic_name, diagnosis, treatment_plan, status, created_by, updated_by)
SELECT
  id,
  (SELECT id FROM auth.users LIMIT 1),
  NOW() - INTERVAL '30 days',
  'routine',
  'Dr. Garcia',
  'Clinica Veterinaria Central',
  'Checkup - All healthy',
  'Continue regular diet',
  'active',
  (SELECT id FROM auth.users LIMIT 1),
  (SELECT id FROM auth.users LIMIT 1)
FROM animals
WHERE status = 'active'
LIMIT 10;

INSERT INTO vaccinations (animal_id, vaccine_name, vaccine_type, administered_date, expiry_date, clinic_name)
SELECT
  id,
  'DHPP Vaccine',
  'dhpp',
  NOW() - INTERVAL '365 days',
  NOW() + INTERVAL '365 days',
  'Clinica Veterinaria Central'
FROM animals
WHERE status = 'active'
LIMIT 10;
```

## Migration Steps in Supabase Dashboard

1. Navigate to SQL Editor in Supabase
2. Create new query for each migration
3. Run migrations in order
4. Verify table creation with `\dt` command
5. Check RLS policies with `SELECT * FROM pg_policies`
6. Run seed data for testing

## Rollback Strategy

Create corresponding `.down.sql` files for each migration to safely revert changes:

```sql
-- 20260325_init_medical_records.down.sql
DROP TABLE IF EXISTS medical_documents;
DROP TABLE IF EXISTS diagnoses;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS vaccinations;
DROP TABLE IF EXISTS medical_records;
DROP TRIGGER IF EXISTS medical_records_updated_at_trigger;
DROP FUNCTION IF EXISTS update_medical_records_updated_at();
```

## Deliverables
- Migration files created in Supabase
- RLS policies applied
- Indexes created for query optimization
- Seed data for testing populated
- Rollback migrations documented
- Migration execution verified
