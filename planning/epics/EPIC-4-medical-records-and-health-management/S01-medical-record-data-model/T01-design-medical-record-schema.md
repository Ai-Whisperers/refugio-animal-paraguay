---
epic: EPIC-4
story: S01
task: T01
title: Design Medical Record Schema
status: todo
priority: high
complexity: 8
---

# T01: Design Medical Record Schema

## Overview
Design and document the complete database schema for medical records, including tables for medical visits, vaccinations, medications, diagnoses, and medical documents with proper relationships and constraints.

## Acceptance Criteria
- [ ] Medical records table schema designed with proper foreign keys
- [ ] Vaccination records table with tracking fields
- [ ] Medications table with dosage and frequency tracking
- [ ] Medical documents table linked to records
- [ ] All tables use UUID primary keys
- [ ] Proper indexes defined for query optimization
- [ ] TypeScript interfaces defined for schema validation
- [ ] Schema documented with inline comments

## Technical Implementation

### Database Schema Design

```sql
-- Medical Records Table
CREATE TABLE medical_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  recorded_by UUID NOT NULL REFERENCES auth.users(id),
  visit_date TIMESTAMP WITH TIME ZONE NOT NULL,
  visit_type VARCHAR(50) NOT NULL, -- 'routine', 'emergency', 'surgery', 'checkup'
  veterinarian_name VARCHAR(255),
  clinic_name VARCHAR(255),
  diagnosis TEXT,
  treatment_plan TEXT,
  notes TEXT,
  status VARCHAR(50) DEFAULT 'active', -- 'active', 'resolved', 'archived'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID NOT NULL REFERENCES auth.users(id),
  updated_by UUID NOT NULL REFERENCES auth.users(id)
);

-- Vaccinations Table
CREATE TABLE vaccinations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  vaccine_name VARCHAR(255) NOT NULL,
  vaccine_type VARCHAR(100), -- 'rabies', 'distemper', 'dhpp', 'feline-combo', etc.
  administered_date DATE NOT NULL,
  expiry_date DATE,
  administered_by UUID REFERENCES auth.users(id),
  batch_number VARCHAR(100),
  clinic_name VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medications Table
CREATE TABLE medications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
  medication_name VARCHAR(255) NOT NULL,
  dosage VARCHAR(100) NOT NULL,
  frequency VARCHAR(100) NOT NULL, -- 'once daily', 'twice daily', 'every 12 hours', etc.
  start_date DATE NOT NULL,
  end_date DATE,
  prescriber_name VARCHAR(255),
  indication TEXT, -- Why prescribed
  side_effects TEXT,
  notes TEXT,
  status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'discontinued'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Diagnoses Table
CREATE TABLE diagnoses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
  condition_name VARCHAR(255) NOT NULL,
  icd_code VARCHAR(50), -- International Classification of Diseases
  severity VARCHAR(50), -- 'mild', 'moderate', 'severe'
  diagnosis_date DATE NOT NULL,
  resolved_date DATE,
  description TEXT,
  treatment_plan TEXT,
  status VARCHAR(50) DEFAULT 'active', -- 'active', 'resolved', 'monitoring'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medical Documents Table
CREATE TABLE medical_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
  document_type VARCHAR(100) NOT NULL, -- 'lab_result', 'xray', 'ultrasound', 'prescription', 'vaccine_certificate'
  document_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_size INT,
  mime_type VARCHAR(100),
  uploaded_by UUID NOT NULL REFERENCES auth.users(id),
  upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  document_date DATE,
  description TEXT,
  tags TEXT[], -- Array of tags for categorization
  storage_bucket VARCHAR(100) DEFAULT 'medical-documents',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_medical_records_animal_id ON medical_records(animal_id);
CREATE INDEX idx_medical_records_visit_date ON medical_records(visit_date DESC);
CREATE INDEX idx_medical_records_status ON medical_records(status);
CREATE INDEX idx_vaccinations_animal_id ON vaccinations(animal_id);
CREATE INDEX idx_vaccinations_expiry_date ON vaccinations(expiry_date);
CREATE INDEX idx_medications_animal_id ON medications(animal_id);
CREATE INDEX idx_medications_status ON medications(status);
CREATE INDEX idx_diagnoses_animal_id ON diagnoses(animal_id);
CREATE INDEX idx_diagnoses_status ON diagnoses(status);
CREATE INDEX idx_medical_documents_animal_id ON medical_documents(animal_id);
CREATE INDEX idx_medical_documents_type ON medical_documents(document_type);
```

### TypeScript Type Definitions

```typescript
// Medical Records
export interface MedicalRecord {
  id: string;
  animal_id: string;
  recorded_by: string;
  visit_date: string;
  visit_type: 'routine' | 'emergency' | 'surgery' | 'checkup';
  veterinarian_name?: string;
  clinic_name?: string;
  diagnosis?: string;
  treatment_plan?: string;
  notes?: string;
  status: 'active' | 'resolved' | 'archived';
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
}

// Vaccinations
export interface Vaccination {
  id: string;
  animal_id: string;
  vaccine_name: string;
  vaccine_type?: string;
  administered_date: string;
  expiry_date?: string;
  administered_by?: string;
  batch_number?: string;
  clinic_name?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// Medications
export interface Medication {
  id: string;
  animal_id: string;
  medical_record_id?: string;
  medication_name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date?: string;
  prescriber_name?: string;
  indication?: string;
  side_effects?: string;
  notes?: string;
  status: 'active' | 'completed' | 'discontinued';
  created_at: string;
  updated_at: string;
}

// Diagnoses
export interface Diagnosis {
  id: string;
  animal_id: string;
  medical_record_id?: string;
  condition_name: string;
  icd_code?: string;
  severity?: 'mild' | 'moderate' | 'severe';
  diagnosis_date: string;
  resolved_date?: string;
  description?: string;
  treatment_plan?: string;
  status: 'active' | 'resolved' | 'monitoring';
  created_at: string;
  updated_at: string;
}

// Medical Documents
export interface MedicalDocument {
  id: string;
  animal_id: string;
  medical_record_id?: string;
  document_type: 'lab_result' | 'xray' | 'ultrasound' | 'prescription' | 'vaccine_certificate';
  document_name: string;
  file_path: string;
  file_size?: number;
  mime_type?: string;
  uploaded_by: string;
  upload_date: string;
  document_date?: string;
  description?: string;
  tags?: string[];
  storage_bucket: string;
  created_at: string;
  updated_at: string;
}
```

## RLS Policies

All medical tables require strict Row-Level Security:
- Staff (vet, admin) can view/edit own organization's records
- Veterinarians can view/edit all medical records
- Adopters/Fosters can view records for animals they care for (read-only)
- Volunteers have read-only access to medical summaries

## Deliverables
- Complete SQL schema definition
- TypeScript type definitions
- Database indexes for performance
- RLS policy outline
- Documentation of relationships
