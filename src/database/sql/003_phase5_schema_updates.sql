-- 003_phase5_schema_updates.sql

-- Add status column to expenses to support void workflow
ALTER TABLE expenses ADD COLUMN status TEXT NOT NULL DEFAULT 'Completed' CHECK (status IN ('Completed', 'Voided'));

-- Prevent deletion of expenses to maintain audit trail
CREATE TRIGGER prevent_expense_delete
BEFORE DELETE ON expenses
BEGIN
    SELECT RAISE(ABORT, 'Cannot delete expenses, use void instead');
END;
