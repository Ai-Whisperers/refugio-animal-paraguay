---
epic: EPIC-4
story: S01
task: T03
title: Implement Audit Logging
status: todo
priority: high
complexity: 6
---

# T03: Implement Audit Logging

## Overview
Implement comprehensive audit logging for all medical records changes, tracking who made what changes when using database triggers and audit tables. This enables compliance, accountability, and change history.

## Acceptance Criteria
- [ ] Audit logs table created with proper schema
- [ ] Triggers created for medical_records, vaccinations, medications, diagnoses, medications inserts/updates/deletes
- [ ] JSON change tracking captures before/after values
- [ ] User attribution tracked (which user made the change)
- [ ] Timestamp logged for all operations
- [ ] RLS policies applied to audit_logs table
- [ ] Query functions created for audit trail retrieval
- [ ] Audit logs for sensitive fields (diagnosis, treatment) flagged

## Technical Implementation

### Audit Logs Table Schema

```sql
-- Create audit_logs table for tracking changes
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  table_name VARCHAR(100) NOT NULL,
  record_id UUID NOT NULL,
  operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
  changed_by UUID NOT NULL REFERENCES auth.users(id),
  changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  old_values JSONB,
  new_values JSONB,
  changes JSONB, -- Specific fields that changed with before/after values
  is_sensitive BOOLEAN DEFAULT FALSE,
  ip_address INET,
  user_agent VARCHAR(500),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for efficient queries
CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_changed_by ON audit_logs(changed_by);
CREATE INDEX idx_audit_logs_changed_at ON audit_logs(changed_at DESC);
CREATE INDEX idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX idx_audit_logs_sensitive ON audit_logs(is_sensitive) WHERE is_sensitive = TRUE;

-- Enable RLS
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
```

### Audit Log Trigger for Medical Records

```sql
-- Function to log medical_records changes
CREATE OR REPLACE FUNCTION log_medical_records_changes()
RETURNS TRIGGER AS $$
DECLARE
  v_changes JSONB;
  v_is_sensitive BOOLEAN := FALSE;
BEGIN
  -- Detect sensitive field changes
  IF TG_OP = 'UPDATE' THEN
    IF OLD.diagnosis IS DISTINCT FROM NEW.diagnosis
       OR OLD.treatment_plan IS DISTINCT FROM NEW.treatment_plan
       OR OLD.notes IS DISTINCT FROM NEW.notes THEN
      v_is_sensitive := TRUE;
    END IF;
  ELSIF TG_OP = 'INSERT' THEN
    IF NEW.diagnosis IS NOT NULL OR NEW.treatment_plan IS NOT NULL THEN
      v_is_sensitive := TRUE;
    END IF;
  END IF;

  -- Build changes object
  IF TG_OP = 'DELETE' THEN
    v_changes := row_to_json(OLD);
  ELSIF TG_OP = 'UPDATE' THEN
    v_changes := jsonb_build_object(
      'visit_date', jsonb_build_object('old', OLD.visit_date, 'new', NEW.visit_date),
      'visit_type', jsonb_build_object('old', OLD.visit_type, 'new', NEW.visit_type),
      'veterinarian_name', jsonb_build_object('old', OLD.veterinarian_name, 'new', NEW.veterinarian_name),
      'diagnosis', jsonb_build_object('old', OLD.diagnosis, 'new', NEW.diagnosis),
      'treatment_plan', jsonb_build_object('old', OLD.treatment_plan, 'new', NEW.treatment_plan),
      'status', jsonb_build_object('old', OLD.status, 'new', NEW.status)
    );
  ELSE
    v_changes := row_to_json(NEW);
  END IF;

  -- Insert audit log
  INSERT INTO audit_logs (
    table_name,
    record_id,
    operation,
    changed_by,
    old_values,
    new_values,
    changes,
    is_sensitive
  ) VALUES (
    'medical_records',
    CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
    TG_OP,
    auth.uid(),
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    CASE WHEN TG_OP = 'INSERT' THEN row_to_json(NEW) ELSE NULL END,
    v_changes,
    v_is_sensitive
  );

  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger
CREATE TRIGGER audit_medical_records_trigger
AFTER INSERT OR UPDATE OR DELETE ON medical_records
FOR EACH ROW
EXECUTE FUNCTION log_medical_records_changes();
```

### Audit Log Triggers for Other Medical Tables

```sql
-- Function to log vaccinations changes
CREATE OR REPLACE FUNCTION log_vaccinations_changes()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_logs (
    table_name,
    record_id,
    operation,
    changed_by,
    old_values,
    new_values,
    changes
  ) VALUES (
    'vaccinations',
    CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
    TG_OP,
    auth.uid(),
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    CASE WHEN TG_OP = 'INSERT' THEN row_to_json(NEW) ELSE NULL END,
    CASE
      WHEN TG_OP = 'DELETE' THEN row_to_json(OLD)
      WHEN TG_OP = 'UPDATE' THEN jsonb_build_object(
        'vaccine_name', jsonb_build_object('old', OLD.vaccine_name, 'new', NEW.vaccine_name),
        'administered_date', jsonb_build_object('old', OLD.administered_date, 'new', NEW.administered_date),
        'expiry_date', jsonb_build_object('old', OLD.expiry_date, 'new', NEW.expiry_date)
      )
      ELSE row_to_json(NEW)
    END
  );
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER audit_vaccinations_trigger
AFTER INSERT OR UPDATE OR DELETE ON vaccinations
FOR EACH ROW
EXECUTE FUNCTION log_vaccinations_changes();

-- Similar triggers for medications, diagnoses
CREATE OR REPLACE FUNCTION log_medications_changes()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_logs (table_name, record_id, operation, changed_by, old_values, new_values, changes)
  VALUES ('medications', CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END, TG_OP, auth.uid(),
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    CASE WHEN TG_OP = 'INSERT' THEN row_to_json(NEW) ELSE NULL END,
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE jsonb_build_object('status', jsonb_build_object('old', OLD.status, 'new', NEW.status)) END);
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER audit_medications_trigger
AFTER INSERT OR UPDATE OR DELETE ON medications
FOR EACH ROW
EXECUTE FUNCTION log_medications_changes();
```

### RLS Policies for Audit Logs

```sql
-- Only admins can view all audit logs
CREATE POLICY "Admins view all audit logs" ON audit_logs
  FOR SELECT USING (
    auth.jwt() -> 'user_metadata' ->> 'role' = 'admin'
  );

-- Staff can view audit logs for their organization
CREATE POLICY "Staff view org audit logs" ON audit_logs
  FOR SELECT USING (
    auth.jwt() -> 'user_metadata' ->> 'role' IN ('staff', 'vet', 'admin')
    AND changed_by IN (
      SELECT id FROM auth.users
      WHERE raw_user_meta_data ->> 'organization_id' =
            (SELECT raw_user_meta_data ->> 'organization_id' FROM auth.users WHERE id = auth.uid())
    )
  );

-- Users can view audit logs for changes they made (limited fields)
CREATE POLICY "Users view own changes" ON audit_logs
  FOR SELECT USING (
    changed_by = auth.uid()
  ) WITH CHECK (
    changed_by = auth.uid()
  );
```

### Query Functions for Audit Trails

```sql
-- Get audit trail for a specific record
CREATE OR REPLACE FUNCTION get_audit_trail(
  p_table_name VARCHAR,
  p_record_id UUID,
  p_limit INT DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  operation VARCHAR,
  changed_by UUID,
  changed_at TIMESTAMP WITH TIME ZONE,
  changes JSONB,
  user_email VARCHAR
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    al.id,
    al.operation,
    al.changed_by,
    al.changed_at,
    al.changes,
    au.email::VARCHAR
  FROM audit_logs al
  LEFT JOIN auth.users au ON al.changed_by = au.id
  WHERE al.table_name = p_table_name
    AND al.record_id = p_record_id
  ORDER BY al.changed_at DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Get all changes by a user
CREATE OR REPLACE FUNCTION get_user_changes(
  p_user_id UUID,
  p_days INT DEFAULT 7
)
RETURNS TABLE (
  id UUID,
  table_name VARCHAR,
  record_id UUID,
  operation VARCHAR,
  changed_at TIMESTAMP WITH TIME ZONE,
  changes JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    al.id,
    al.table_name,
    al.record_id,
    al.operation,
    al.changed_at,
    al.changes
  FROM audit_logs al
  WHERE al.changed_by = p_user_id
    AND al.changed_at >= NOW() - (p_days || ' days')::INTERVAL
  ORDER BY al.changed_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Get sensitive field changes
CREATE OR REPLACE FUNCTION get_sensitive_changes(
  p_days INT DEFAULT 30
)
RETURNS TABLE (
  id UUID,
  table_name VARCHAR,
  record_id UUID,
  changed_by UUID,
  changed_at TIMESTAMP WITH TIME ZONE,
  changes JSONB,
  user_email VARCHAR
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    al.id,
    al.table_name,
    al.record_id,
    al.changed_by,
    al.changed_at,
    al.changes,
    au.email::VARCHAR
  FROM audit_logs al
  LEFT JOIN auth.users au ON al.changed_by = au.id
  WHERE al.is_sensitive = TRUE
    AND al.changed_at >= NOW() - (p_days || ' days')::INTERVAL
  ORDER BY al.changed_at DESC;
END;
$$ LANGUAGE plpgsql;
```

### TypeScript Interface for Audit Logs

```typescript
export interface AuditLog {
  id: string;
  table_name: string;
  record_id: string;
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  changed_by: string;
  changed_at: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  changes?: Record<string, any>;
  is_sensitive: boolean;
  ip_address?: string;
  user_agent?: string;
  notes?: string;
  created_at: string;
}

export interface AuditTrail {
  record_id: string;
  table_name: string;
  logs: AuditLog[];
  total_changes: number;
  first_change: string;
  last_change: string;
}
```

## Compliance Considerations

- Audit logs cannot be modified after creation (triggers only allow insert)
- Sensitive fields (diagnosis, treatment) marked for enhanced access control
- All user actions attributed via auth.uid()
- Timestamp precision to milliseconds for ordering
- JSONB storage allows schema flexibility without migrations
- Change tracking enables compliance reporting

## Migration File: 20260325_add_audit_logging.sql

```sql
-- Add audit logging infrastructure
CREATE TABLE IF NOT EXISTS audit_logs (...);
CREATE INDEX idx_audit_logs_table_record ON audit_logs(...);
-- ... all trigger functions
-- ... all triggers
-- ... all RLS policies
-- ... all query functions
```

## Deliverables
- Audit logs table schema with proper indexing
- Trigger functions for all medical tables (medical_records, vaccinations, medications, diagnoses)
- RLS policies for audit log access control
- Query functions for audit trail retrieval (get_audit_trail, get_user_changes, get_sensitive_changes)
- TypeScript interfaces for audit data
- Documentation of audit logging architecture
- Compliance notes for regulatory adherence
