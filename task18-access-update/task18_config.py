
# ==========================================================
# PULSEIQ - TASK 18: SELF-SERVICE KPI EXPLORER
# Role Permissions, Metric Allowlist and Privacy Configuration
# ==========================================================

# ------------------------------
# 1. PRIVACY THRESHOLDS
# ------------------------------

MIN_EMPLOYEES = 5
MIN_ATTRITION_EMPLOYEES = 10

MIN_TASKS = 5
MIN_COMPLETED_TASKS = 5
MIN_VALID_CYCLE_TASKS = 5


# ------------------------------
# 2. ROLE PERMISSIONS
# ------------------------------
# These are demo permissions only.
# They are NOT authentication.
# Production access requires verified user identity.

ROLES = {
    "ADMIN": {
        "description": "Approved aggregate metrics across the company",
        "metrics": [
            "M01", "M02", "M03", "M04", "M05", "M06",
            "M07", "M08", "M09", "M10", "M11", "M12",
            "M13", "M14", "M15", "M16", "M17", "M18",
            "M19", "M20", "M22", "M23", "M24", "M25",
        ],
        "dimensions": [
            "Company", "Department", "Team", "Sprint"
        ],
    },

    "HR": {
        "description": "People and payroll aggregates",
        "metrics": [
            "M01", "M02", "M03", "M04", "M05", "M06",
            "M07", "M08", "M09", "M10", "M11", "M12",
            "M13", "M14", "M15",
        ],
        "dimensions": ["Company", "Department"],
    },

    "MANAGER": {
        "description": "Team productivity aggregates",
        "metrics": ["M22", "M23", "M24", "M25"],
        "dimensions": ["Team", "Sprint"],
    },

    "EXECUTIVE": {
        "description": "Company-level workforce and financial KPIs",
        "metrics": [
            "M01", "M04", "M05", "M07", "M09",
            "M13", "M16", "M17", "M18", "M19", "M20",
        ],
        "dimensions": ["Company"],
    },
}


# ------------------------------
# 3. VERIFIED METRIC DEFINITIONS
# ------------------------------
# View names and column names are based on the
# PostgreSQL metadata inspected during Task 18.
#
# SQL identifiers must only come from this allowlist.
# Never use arbitrary user-provided SQL identifiers.

METRICS = {

    # WORKFORCE METRICS

    "M01": {
        "name": "Headcount",
        "view": "metric_m01_headcount",
        "value_column": "headcount",
        "date_column": "month_start_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "employees",
        "privacy_type": "employee_count",
    },

    "M02": {
        "name": "Hires",
        "view": "metric_m02_hires",
        "value_column": "hires",
        "date_column": "month_start_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "employees",
        "privacy_type": "employee_count",
    },

    "M03": {
        "name": "Exits",
        "view": "metric_m03_exits",
        "value_column": "exits",
        "date_column": "month_start_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "employees",
        "privacy_type": "employee_count",
    },

    "M04": {
        "name": "Monthly attrition",
        "view": "metric_m04_monthly_attrition_rate",
        "value_column": "attrition_rate_monthly_pct",
        "date_column": "month_start_date",
        "dimension": "department_id",
        "minimum": 10,
        "unit": "%",
        "privacy_type": "employee_count",
    },

    "M05": {
        "name": "Rolling 12-month attrition",
        "view": "metric_m05_attrition_rate_rolling_12m",
        "value_column": "attrition_rate_rolling_12m_pct",
        "date_column": "month_start_date",
        "dimension": "department_id",
        "minimum": 10,
        "unit": "%",
        "privacy_type": "employee_count",
    },

    "M06": {
        "name": "Voluntary attrition",
        "view": "metric_m06_voluntary_attrition_rate",
        "value_column": "voluntary_attrition_rate_pct",
        "date_column": "month_start_date",
        "dimension": "department_id",
        "minimum": 10,
        "unit": "%",
        "privacy_type": "employee_count",
    },


    # PAYROLL METRICS

    "M07": {
        "name": "Gross pay",
        "view": "metric_m07_gross_pay",
        "value_column": "gross_pay",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "currency",
        "privacy_type": "employee_count",
    },

    "M08": {
        "name": "Net pay",
        "view": "metric_m08_net_pay",
        "value_column": "net_pay",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "currency",
        "privacy_type": "employee_count",
    },

    "M09": {
        "name": "Payroll cost",
        "view": "metric_m09_payroll_cost",
        "value_column": "payroll_cost",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "currency",
        "privacy_type": "employee_count",
    },

    "M10": {
        "name": "Cost per head",
        "view": "metric_m10_cost_per_head",
        "value_column": "cost_per_head",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "currency",
        "privacy_type": "employee_count",
    },

    "M11": {
        "name": "Overtime share",
        "view": "metric_m11_overtime_share",
        "value_column": "overtime_share_pct",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "%",
        "privacy_type": "employee_count",
    },

    "M12": {
        "name": "Variable pay share",
        "view": "metric_m12_variable_pay_share",
        "value_column": "variable_pay_share_pct",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "%",
        "privacy_type": "employee_count",
    },


    # ATTENDANCE AND LEAVE METRICS

    "M13": {
        "name": "Attendance rate",
        "view": "metric_m13_attendance_rate",
        "value_column": "attendance_rate",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "%",
        "privacy_type": "employee_count",
    },

    "M14": {
        "name": "Late arrival rate",
        "view": "metric_m14_late_arrival_rate",
        "value_column": "late_arrival_rate",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "%",
        "privacy_type": "employee_count",
    },

    "M15": {
        "name": "Leave without pay days",
        "view": "metric_m15_leave_without_pay_days",
        "value_column": "leave_without_pay_days",
        "date_column": "period_end_date",
        "dimension": "department_id",
        "minimum": 5,
        "unit": "days",
        "privacy_type": "employee_count",
    },


    # FINANCIAL METRICS

    "M16": {
        "name": "Revenue",
        "view": "metric_m16_revenue",
        "value_column": "revenue",
        "date_column": "posting_period",
        "dimension": None,
        "minimum": None,
        "unit": "currency",
        "privacy_type": "company_only",
    },

    "M17": {
        "name": "Net profit",
        "view": "metric_m17_net_profit",
        "value_column": "net_profit",
        "date_column": "posting_period",
        "dimension": None,
        "minimum": None,
        "unit": "currency",
        "privacy_type": "company_only",
    },

    "M18": {
        "name": "Operating margin",
        "view": "metric_m18_operating_margin",
        "value_column": "operating_margin_pct",
        "date_column": "posting_period",
        "dimension": None,
        "minimum": None,
        "unit": "%",
        "privacy_type": "company_only",
    },

    "M19": {
        "name": "Payroll as % revenue",
        "view": "metric_m19_payroll_as_revenue_pct",
        "value_column": "payroll_as_revenue_pct",
        "date_column": "posting_period",
        "dimension": None,
        "minimum": None,
        "unit": "%",
        "privacy_type": "company_only",
    },

    "M20": {
        "name": "Days sales outstanding",
        "view": "metric_m20_days_sales_outstanding",
        "value_column": "dso_days",
        "date_column": "as_of_date",
        "dimension": None,
        "minimum": None,
        "unit": "days",
        "privacy_type": "company_only",
    },


    # TASK AND TEAM METRICS

    "M22": {
        "name": "Task completion rate",
        "view": "metric_m22_task_completion_rate",
        "value_column": "task_completion_rate_pct",
        "date_column": "sprint_id",
        "dimension": "team_id",
        "minimum": 5,
        "count_column": "planned_non_cancelled_tasks",
        "unit": "%",
        "privacy_type": "task_count",
    },

    "M23": {
        "name": "On-time delivery rate",
        "view": "metric_m23_on_time_delivery_rate",
        "value_column": "on_time_delivery_rate_pct",
        "date_column": "sprint_id",
        "dimension": "team_id",
        "minimum": 5,
        "count_column": "done_tasks",
        "unit": "%",
        "privacy_type": "task_count",
    },

    "M24": {
        "name": "Team velocity",
        "view": "metric_m24_velocity",
        "value_column": "velocity_story_points",
        "date_column": "sprint_id",
        "dimension": "team_id",
        "minimum": 5,
        "count_column": "completed_tasks",
        "unit": "story points",
        "privacy_type": "task_count",
    },

    "M25": {
        "name": "Average cycle time",
        "view": "metric_m25_average_cycle_time",
        "value_column": "average_cycle_time_days",
        "date_column": "sprint_id",
        "dimension": "team_id",
        "minimum": 5,
        "count_column": "valid_completed_tasks",
        "unit": "days",
        "privacy_type": "task_count",
    },
}


# ------------------------------
# 4. RESTRICTED METRICS
# ------------------------------
# Not available until dedicated safe aggregation
# and suppression logic has been implemented.

RESTRICTED_METRICS = [
    "M21",  # Client-level overdue receivables
    "M26",  # Anomaly flag rate
    "M27",  # High-risk share
    "M28",  # Forecast error MAPE
]


# ------------------------------
# 5. DIMENSION ALLOWLIST
# ------------------------------

DIMENSIONS = {
    "Company": None,
    "Department": "department_id",
    "Team": "team_id",
    "Sprint": "sprint_id",
}


# ------------------------------
# 6. METRIC VALIDATION
# ------------------------------

def get_allowed_metrics(role):
    """Return metrics permitted for a configured role."""
    if role not in ROLES:
        return []

    return [
        metric_id
        for metric_id in ROLES[role]["metrics"]
        if metric_id in METRICS
        and metric_id not in RESTRICTED_METRICS
    ]


def get_allowed_dimensions(role):
    """Return dimensions permitted for a configured role."""
    if role not in ROLES:
        return []

    return ROLES[role]["dimensions"]


def get_metric_config(metric_id, role):
    """Return a metric only when the role is allowed to access it."""
    if metric_id not in get_allowed_metrics(role):
        return None

    return METRICS.get(metric_id)