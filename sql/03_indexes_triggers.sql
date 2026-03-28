-- Indexes
CREATE INDEX IF NOT EXISTS idx_student_programme ON student(programme_id);
CREATE INDEX IF NOT EXISTS idx_student_status ON student(status);
CREATE INDEX IF NOT EXISTS idx_student_county ON student(county);
CREATE INDEX IF NOT EXISTS idx_course_reg_student ON course_registration(student_id);
CREATE INDEX IF NOT EXISTS idx_course_reg_semester ON course_registration(semester_id);
CREATE INDEX IF NOT EXISTS idx_result_reg ON result(reg_id);
CREATE INDEX IF NOT EXISTS idx_payment_student ON payment(student_id);
CREATE INDEX IF NOT EXISTS idx_payment_date ON payment(payment_date);
CREATE INDEX IF NOT EXISTS idx_payroll_staff ON payroll(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_dept ON staff(dept_id);
CREATE INDEX IF NOT EXISTS idx_trip_vehicle ON trip(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_order(supplier_id);
CREATE INDEX IF NOT EXISTS idx_stock_item ON stock(item_id);
CREATE INDEX IF NOT EXISTS idx_room_alloc_student ON room_allocation(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

DO $$ DECLARE t TEXT;
BEGIN FOR t IN SELECT unnest(ARRAY['student','school','department','programme','staff']) LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_ts ON %I; CREATE TRIGGER trg_ts BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_timestamp();', t, t);
END LOOP; END $$;
