-- Analytics Schema for Management Reporting

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key INT PRIMARY KEY, full_date DATE UNIQUE NOT NULL,
    year INT, month INT, month_name VARCHAR(20), week INT,
    day_of_week INT, day_name VARCHAR(20), quarter INT,
    semester VARCHAR(20), academic_year VARCHAR(10),
    is_exam_period BOOLEAN DEFAULT FALSE, is_weekend BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS analytics.dim_academic_hierarchy (
    id SERIAL PRIMARY KEY,
    school_code VARCHAR(10), school_name VARCHAR(200),
    dept_code VARCHAR(10), dept_name VARCHAR(200),
    programme_code VARCHAR(20), programme_name VARCHAR(250),
    programme_level VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS analytics.fact_enrollment (
    id SERIAL PRIMARY KEY,
    school_name VARCHAR(200), dept_name VARCHAR(200), programme_name VARCHAR(250),
    entry_year INT, admission_type VARCHAR(20), gender VARCHAR(10), county VARCHAR(60),
    total_enrolled INT DEFAULT 0, active_count INT DEFAULT 0,
    graduated_count INT DEFAULT 0, deferred_count INT DEFAULT 0,
    snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.fact_academic_performance (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20), course_name VARCHAR(200),
    school_name VARCHAR(200), dept_name VARCHAR(200),
    academic_year VARCHAR(10), semester VARCHAR(20),
    total_students INT DEFAULT 0, avg_total_score DECIMAL(5,2),
    pass_rate_pct DECIMAL(5,2),
    grade_a INT DEFAULT 0, grade_b INT DEFAULT 0, grade_c INT DEFAULT 0,
    grade_d INT DEFAULT 0, grade_e INT DEFAULT 0, grade_f INT DEFAULT 0,
    snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.fact_revenue (
    id SERIAL PRIMARY KEY,
    school_name VARCHAR(200), dept_name VARCHAR(200), programme_name VARCHAR(250),
    academic_year VARCHAR(10), semester VARCHAR(20),
    total_collected DECIMAL(14,2) DEFAULT 0,
    student_count INT DEFAULT 0,
    method_mpesa INT DEFAULT 0, method_bank INT DEFAULT 0, method_helb INT DEFAULT 0,
    method_cash INT DEFAULT 0, method_cheque INT DEFAULT 0, method_bursary INT DEFAULT 0,
    snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.fact_staff_summary (
    id SERIAL PRIMARY KEY,
    school_name VARCHAR(200), dept_name VARCHAR(200), role VARCHAR(30),
    total_staff INT DEFAULT 0, avg_salary DECIMAL(12,2),
    total_payroll DECIMAL(14,2) DEFAULT 0,
    snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.fact_accommodation (
    id SERIAL PRIMARY KEY,
    hostel_name VARCHAR(100), total_capacity INT DEFAULT 0,
    allocated INT DEFAULT 0, available INT DEFAULT 0,
    occupancy_rate_pct DECIMAL(5,2) DEFAULT 0,
    snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.fact_transport (
    id SERIAL PRIMARY KEY,
    vehicle_reg VARCHAR(20), vehicle_type VARCHAR(20),
    total_trips INT DEFAULT 0, total_distance_km DECIMAL(10,2) DEFAULT 0,
    total_fuel_litres DECIMAL(10,2) DEFAULT 0, total_cost DECIMAL(12,2) DEFAULT 0,
    period_month INT, period_year INT,
    snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.fact_procurement (
    id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(200),
    total_orders INT DEFAULT 0, total_value DECIMAL(14,2) DEFAULT 0,
    delivered INT DEFAULT 0, pending INT DEFAULT 0, cancelled INT DEFAULT 0,
    period_year INT, snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.fact_research (
    id SERIAL PRIMARY KEY,
    dept_name VARCHAR(200),
    active_projects INT DEFAULT 0, total_grants DECIMAL(14,2) DEFAULT 0,
    grants_utilized DECIMAL(14,2) DEFAULT 0, utilization_pct DECIMAL(5,2) DEFAULT 0,
    total_publications INT DEFAULT 0,
    snapshot_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS analytics.dq_rejection_log (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(50), record_id VARCHAR(100),
    rejection_reason VARCHAR(300), rejected_at TIMESTAMPTZ DEFAULT NOW()
);
