
CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_department (
    department_id TEXT PRIMARY KEY,
    department_name TEXT,
    cost_center TEXT,
    description TEXT,
    is_leadership BOOLEAN
);

CREATE TABLE IF NOT EXISTS warehouse.dim_role (
    role_id TEXT PRIMARY KEY,
    department_id TEXT,
    role_title TEXT,
    level TEXT,
    grade TEXT,
    band_min_annual NUMERIC(14,2),
    band_mid_annual NUMERIC(14,2),
    band_max_annual NUMERIC(14,2),
    overtime_eligible BOOLEAN,
    band_reference_year INTEGER
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month_number INTEGER,
    month_name TEXT,
    year_month TEXT,
    week_of_year INTEGER,
    day_of_week INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    is_working_day BOOLEAN,
    financial_year TEXT,
    fiscal_quarter TEXT,
    fiscal_month_number INTEGER,
    is_month_end BOOLEAN,
    month_start_date DATE,
    month_end_date DATE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_leave_type (
    leave_type_code TEXT PRIMARY KEY,
    leave_type_name TEXT,
    pay_type TEXT,
    annual_quota_days NUMERIC(8,2),
    prorated_for_joiners BOOLEAN,
    carry_forward_allowed BOOLEAN,
    max_carry_forward_days NUMERIC(8,2),
    policy_note TEXT
);

CREATE TABLE IF NOT EXISTS warehouse.dim_employee (
    employee_key TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    department_id TEXT,
    role_id TEXT,
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    change_reason TEXT
);

CREATE TABLE IF NOT EXISTS warehouse.fact_payroll (
    payroll_item_id TEXT PRIMARY KEY,
    run_id TEXT,
    employee_id TEXT,
    date_key INTEGER,
    employee_key TEXT,
    period_end_date DATE,
    department_id TEXT,
    role_id TEXT,
    payable_days NUMERIC(8,2),
    lop_days NUMERIC(8,2),
    overtime_hours_paid NUMERIC(10,2),
    variable_pay_type TEXT,
    monthly_fixed_gross NUMERIC(14,2),
    basic NUMERIC(14,2),
    hra NUMERIC(14,2),
    conveyance NUMERIC(14,2),
    medical NUMERIC(14,2),
    special_allowance NUMERIC(14,2),
    earned_fixed_pay NUMERIC(14,2),
    overtime_pay NUMERIC(14,2),
    variable_pay NUMERIC(14,2),
    gross_pay NUMERIC(14,2),
    pf_employee NUMERIC(14,2),
    esi_employee NUMERIC(14,2),
    professional_tax NUMERIC(14,2),
    tds NUMERIC(14,2),
    other_deductions NUMERIC(14,2),
    total_deductions NUMERIC(14,2),
    net_pay NUMERIC(14,2),
    pf_employer NUMERIC(14,2),
    esi_employer NUMERIC(14,2),
    employer_cost NUMERIC(14,2),
    headcount_flag INTEGER
);

CREATE TABLE IF NOT EXISTS warehouse.fact_attendance_monthly (
    attendance_fact_id TEXT PRIMARY KEY,
    employee_id TEXT,
    date_key INTEGER,
    employee_key TEXT,
    department_id TEXT,
    scheduled_days NUMERIC(8,2),
    present_days NUMERIC(8,2),
    wfh_days NUMERIC(8,2),
    half_days_unpaid NUMERIC(8,2),
    paid_leave_days NUMERIC(8,2),
    unpaid_absence_days NUMERIC(8,2),
    late_arrivals INTEGER,
    avg_hours_worked NUMERIC(8,2),
    overtime_hours NUMERIC(8,2),
    attendance_rate NUMERIC(8,4),
    period_end_date DATE
);

CREATE TABLE IF NOT EXISTS warehouse.fact_leave (
    leave_request_id TEXT PRIMARY KEY,
    employee_id TEXT,
    employee_key TEXT,
    leave_type_code TEXT,
    start_date_key INTEGER,
    end_date_key INTEGER,
    start_date DATE,
    end_date DATE,
    days NUMERIC(8,2),
    status TEXT,
    applied_on DATE,
    decided_on DATE,
    approver_id TEXT,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS warehouse.fact_headcount_monthly (
    date_key INTEGER,
    month_start_date DATE,
    department_id TEXT,
    headcount_start INTEGER,
    hires INTEGER,
    exits INTEGER,
    voluntary_exits INTEGER,
    transfers_in INTEGER,
    transfers_out INTEGER,
    headcount_end INTEGER,
    attrition_rate_monthly_pct NUMERIC(8,4),
    PRIMARY KEY (date_key, department_id)
);

CREATE INDEX IF NOT EXISTS idx_payroll_date
    ON warehouse.fact_payroll(date_key);

CREATE INDEX IF NOT EXISTS idx_payroll_department
    ON warehouse.fact_payroll(department_id);

CREATE INDEX IF NOT EXISTS idx_payroll_employee
    ON warehouse.fact_payroll(employee_key);

CREATE INDEX IF NOT EXISTS idx_attendance_date
    ON warehouse.fact_attendance_monthly(date_key);

CREATE INDEX IF NOT EXISTS idx_attendance_employee
    ON warehouse.fact_attendance_monthly(employee_key);

CREATE INDEX IF NOT EXISTS idx_leave_employee
    ON warehouse.fact_leave(employee_key);

CREATE INDEX IF NOT EXISTS idx_leave_start_date
    ON warehouse.fact_leave(start_date_key);

CREATE INDEX IF NOT EXISTS idx_headcount_department
    ON warehouse.fact_headcount_monthly(department_id);
