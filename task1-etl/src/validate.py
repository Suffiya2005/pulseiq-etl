
"""Pandera validation schemas for PulseIQ datasets."""

import pandera.pandas as pa
from pandera import Check

def payroll_schema():
    return pa.DataFrameSchema(
        {
            "payroll_item_id": pa.Column(nullable=False, unique=True),
            "monthly_fixed_gross": pa.Column(
                float, Check.ge(0), nullable=False, coerce=True
            ),
            "gross_pay": pa.Column(
                float, Check.ge(0), nullable=False, coerce=True
            ),
            "net_pay": pa.Column(
                float, Check.ge(0), nullable=False, coerce=True
            ),
        },
        strict=False,
        coerce=True,
    )


def validate_payroll(df):
    return payroll_schema().validate(df, lazy=True)

def employee_schema():
    return pa.DataFrameSchema(
        {
            "employee_key": pa.Column(nullable=False, unique=True),
            "hire_date": pa.Column(object, nullable=False, coerce=True),
            "exit_date": pa.Column(object, nullable=True, coerce=True),
        },
        strict=False,
        coerce=True,
    )


def validate_employees(df):
    return employee_schema().validate(df, lazy=True)