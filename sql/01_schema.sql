-- ============================================================
-- CAMPUS MANAGEMENT REPORT
-- Kenyatta University Integrated Information System
-- Transactional Schema — 35 tables across 9 domains
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum types
DO $$ BEGIN CREATE TYPE gender_enum AS ENUM ('Male','Female','Other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE admission_enum AS ENUM ('Government','Self-Sponsored'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE student_status_enum AS ENUM ('Active','Deferred','Suspended','Graduated','Withdrawn','Deleted'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE programme_level_enum AS ENUM ('Certificate','Diploma','Bachelors','Masters','PhD'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE semester_term_enum AS ENUM ('Semester 1','Semester 2','Semester 3'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE reg_status_enum AS ENUM ('Registered','Dropped','Deferred'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE payment_method_enum AS ENUM ('M-Pesa','Bank Transfer','Cash','Cheque','HELB','Bursary'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE staff_role_enum AS ENUM ('Academic','Administrative','Technical','Support'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE vehicle_type_enum AS ENUM ('Bus','Van','Truck','Sedan','SUV'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE po_status_enum AS ENUM ('Draft','Submitted','Approved','Delivered','Cancelled'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE project_status_enum AS ENUM ('Proposal','Active','Completed','Suspended'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- A. ACADEMIC STRUCTURE
CREATE TABLE IF NOT EXISTS school (
    school_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_code VARCHAR(10) UNIQUE NOT NULL,
    school_name VARCHAR(200) NOT NULL,
    dean_name VARCHAR(120),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS department (
    dept_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dept_code VARCHAR(10) UNIQUE NOT NULL,
    dept_name VARCHAR(200) NOT NULL,
    school_id UUID NOT NULL REFERENCES school(school_id) ON DELETE RESTRICT,
    hod_name VARCHAR(120),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS programme (
    programme_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    programme_code VARCHAR(20) UNIQUE NOT NULL,
    programme_name VARCHAR(250) NOT NULL,
    level programme_level_enum NOT NULL DEFAULT 'Bachelors',
    dept_id UUID NOT NULL REFERENCES department(dept_id) ON DELETE RESTRICT,
    duration_years INT NOT NULL DEFAULT 4,
    fee_per_semester DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS course_unit (
    course_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    credit_hours INT NOT NULL DEFAULT 3,
    dept_id UUID REFERENCES department(dept_id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS curriculum (
    curriculum_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    programme_id UUID NOT NULL REFERENCES programme(programme_id) ON DELETE RESTRICT,
    course_id UUID NOT NULL REFERENCES course_unit(course_id) ON DELETE RESTRICT,
    year_of_study INT NOT NULL,
    semester semester_term_enum NOT NULL,
    UNIQUE(programme_id, course_id)
);

CREATE TABLE IF NOT EXISTS semester (
    semester_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year INT NOT NULL,
    term semester_term_enum NOT NULL,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    UNIQUE(year, term)
);

-- B. STUDENT DOMAIN
CREATE TABLE IF NOT EXISTS student (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admission_no VARCHAR(30) UNIQUE NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    gender gender_enum NOT NULL,
    date_of_birth DATE,
    nationality VARCHAR(60) DEFAULT 'Kenyan',
    national_id VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(120),
    county VARCHAR(60),
    admission_type admission_enum NOT NULL,
    programme_id UUID REFERENCES programme(programme_id) ON DELETE RESTRICT,
    entry_year INT,
    status student_status_enum DEFAULT 'Active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS next_of_kin (
    kin_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    relationship VARCHAR(40),
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- C. REGISTRATION & TEACHING
CREATE TABLE IF NOT EXISTS course_registration (
    reg_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES student(student_id) ON DELETE RESTRICT,
    course_id UUID NOT NULL REFERENCES course_unit(course_id) ON DELETE RESTRICT,
    semester_id UUID NOT NULL REFERENCES semester(semester_id) ON DELETE RESTRICT,
    status reg_status_enum DEFAULT 'Registered',
    registration_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- D. STAFF & HR
CREATE TABLE IF NOT EXISTS staff (
    staff_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staff_no VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    gender gender_enum,
    role staff_role_enum NOT NULL DEFAULT 'Academic',
    dept_id UUID REFERENCES department(dept_id) ON DELETE RESTRICT,
    employment_date DATE,
    phone VARCHAR(20),
    email VARCHAR(120),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lecturer (
    lecturer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staff_id UUID UNIQUE NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT,
    specialization VARCHAR(200),
    qualification VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS teaching_allocation (
    allocation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lecturer_id UUID NOT NULL REFERENCES lecturer(lecturer_id) ON DELETE RESTRICT,
    course_id UUID NOT NULL REFERENCES course_unit(course_id) ON DELETE RESTRICT,
    semester_id UUID NOT NULL REFERENCES semester(semester_id) ON DELETE RESTRICT,
    UNIQUE(lecturer_id, course_id, semester_id)
);

-- E. ACADEMIC PERFORMANCE
CREATE TABLE IF NOT EXISTS result (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reg_id UUID UNIQUE NOT NULL REFERENCES course_registration(reg_id) ON DELETE RESTRICT,
    cat_score DECIMAL(5,2) CHECK (cat_score >= 0 AND cat_score <= 30),
    exam_score DECIMAL(5,2) CHECK (exam_score >= 0 AND exam_score <= 70),
    total_score DECIMAL(5,2) GENERATED ALWAYS AS (COALESCE(cat_score,0) + COALESCE(exam_score,0)) STORED,
    grade VARCHAR(2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- F. PAYROLL & LEAVE
CREATE TABLE IF NOT EXISTS payroll (
    payroll_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staff_id UUID NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT,
    basic_salary DECIMAL(12,2) NOT NULL CHECK (basic_salary >= 0),
    allowances DECIMAL(12,2) DEFAULT 0 CHECK (allowances >= 0),
    deductions DECIMAL(12,2) DEFAULT 0 CHECK (deductions >= 0),
    net_salary DECIMAL(12,2) GENERATED ALWAYS AS (basic_salary + COALESCE(allowances,0) - COALESCE(deductions,0)) STORED,
    pay_date DATE NOT NULL,
    pay_month INT,
    pay_year INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staff_leave (
    leave_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staff_id UUID NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT,
    leave_type VARCHAR(40) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days INT,
    status VARCHAR(20) DEFAULT 'Pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- G. FINANCE
CREATE TABLE IF NOT EXISTS fee_structure (
    fee_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    programme_id UUID NOT NULL REFERENCES programme(programme_id) ON DELETE RESTRICT,
    semester_id UUID REFERENCES semester(semester_id),
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    sponsor_type admission_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS payment (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES student(student_id) ON DELETE RESTRICT,
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    method payment_method_enum NOT NULL,
    receipt_no VARCHAR(50),
    semester_id UUID REFERENCES semester(semester_id),
    academic_year VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget (
    budget_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dept_id UUID REFERENCES department(dept_id),
    fiscal_year VARCHAR(10) NOT NULL,
    budget_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    actual_spent DECIMAL(14,2) DEFAULT 0,
    variance DECIMAL(14,2) GENERATED ALWAYS AS (budget_amount - COALESCE(actual_spent,0)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- H. ACCOMMODATION
CREATE TABLE IF NOT EXISTS hostel (
    hostel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hostel_name VARCHAR(100) NOT NULL,
    capacity INT NOT NULL DEFAULT 0,
    gender_restriction gender_enum,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS room (
    room_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hostel_id UUID NOT NULL REFERENCES hostel(hostel_id) ON DELETE RESTRICT,
    room_number VARCHAR(20) NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    is_available BOOLEAN DEFAULT TRUE,
    UNIQUE(hostel_id, room_number)
);

CREATE TABLE IF NOT EXISTS room_allocation (
    allocation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES student(student_id) ON DELETE RESTRICT,
    room_id UUID NOT NULL REFERENCES room(room_id) ON DELETE RESTRICT,
    semester_id UUID NOT NULL REFERENCES semester(semester_id) ON DELETE RESTRICT,
    check_in_date DATE,
    check_out_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- I. TRANSPORT
CREATE TABLE IF NOT EXISTS vehicle (
    vehicle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    registration_no VARCHAR(20) UNIQUE NOT NULL,
    type vehicle_type_enum NOT NULL,
    capacity INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS driver (
    driver_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staff_id UUID UNIQUE NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT,
    license_no VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS trip (
    trip_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID NOT NULL REFERENCES vehicle(vehicle_id) ON DELETE RESTRICT,
    driver_id UUID NOT NULL REFERENCES driver(driver_id) ON DELETE RESTRICT,
    trip_date DATE NOT NULL,
    destination VARCHAR(200),
    purpose VARCHAR(300),
    distance_km DECIMAL(8,2),
    fuel_litres DECIMAL(8,2),
    cost DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- J. PROCUREMENT & INVENTORY
CREATE TABLE IF NOT EXISTS supplier (
    supplier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(120),
    phone VARCHAR(20),
    email VARCHAR(120),
    rating DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS item (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(80),
    unit_of_measure VARCHAR(30),
    unit_price DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchase_order (
    po_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES supplier(supplier_id) ON DELETE RESTRICT,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_amount DECIMAL(14,2) DEFAULT 0,
    status po_status_enum DEFAULT 'Draft',
    approved_by VARCHAR(120),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS po_line (
    line_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id UUID NOT NULL REFERENCES purchase_order(po_id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES item(item_id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE TABLE IF NOT EXISTS stock (
    stock_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID UNIQUE NOT NULL REFERENCES item(item_id) ON DELETE RESTRICT,
    quantity_available INT DEFAULT 0 CHECK (quantity_available >= 0),
    reorder_level INT DEFAULT 10,
    last_restocked DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- K. RESEARCH
CREATE TABLE IF NOT EXISTS research_project (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(300) NOT NULL,
    principal_investigator UUID REFERENCES staff(staff_id),
    dept_id UUID REFERENCES department(dept_id),
    funding_source VARCHAR(150),
    grant_amount DECIMAL(14,2) DEFAULT 0,
    amount_utilized DECIMAL(14,2) DEFAULT 0,
    start_date DATE,
    end_date DATE,
    status project_status_enum DEFAULT 'Proposal',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS publication (
    publication_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(400) NOT NULL,
    authors TEXT,
    dept_id UUID REFERENCES department(dept_id),
    journal VARCHAR(200),
    publication_date DATE,
    doi VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SYSTEM TABLES
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id VARCHAR(50) DEFAULT 'system',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS etl_run_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(50) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running',
    records_processed INT DEFAULT 0,
    errors TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(30) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
