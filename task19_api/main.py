from datetime import date, datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg import sql

from task19_api.auth import (
    authenticate_user,
    create_access_token,
    require_api_user,
)
from task19_api.database import get_connection
from task19_api.metrics import API_METRIC_IDS, get_api_metric


app = FastAPI(
    title="PulseIQ Metrics API",
    description=(
        "Authenticated, read-only API for approved company financial KPIs. "
        "Available metrics: M16–M20."
    ),
    version="1.0.0",
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=256)


def json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


@app.get("/")
def root():
    return {
        "service": "PulseIQ Metrics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "pulseiq-metrics-api"}


@app.post("/auth/token")
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1800,
        "role": user["role"],
    }


@app.get("/metrics")
def list_metrics(user: dict = Depends(require_api_user)):
    permitted = [
        metric_id
        for metric_id in API_METRIC_IDS
        if get_api_metric(metric_id, user["role"]) is not None
    ]

    return {
        "role": user["role"],
        "metrics": [
            {
                "metric_id": metric_id,
                "name": get_api_metric(metric_id, user["role"])["name"],
                "unit": get_api_metric(metric_id, user["role"])["unit"],
            }
            for metric_id in permitted
        ],
    }


@app.get("/metrics/{metric_id}")
def read_metric(
    metric_id: str,
    user: dict = Depends(require_api_user),
):
    metric_id = metric_id.upper()
    config = get_api_metric(metric_id, user["role"])

    if config is None:
        raise HTTPException(
            status_code=403,
            detail="Metric is unavailable or your role is not permitted to access it.",
        )

    query = sql.SQL(
        """
        SELECT {date_column}, {value_column}
        FROM {schema}.{view}
        ORDER BY {date_column} ASC
        """
    ).format(
        date_column=sql.Identifier(config["date_column"]),
        value_column=sql.Identifier(config["value_column"]),
        schema=sql.Identifier("warehouse"),
        view=sql.Identifier(config["view"]),
    )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="The metrics database is temporarily unavailable.",
        )

    data = [
        {
            "reporting_period": json_value(row[0]),
            "value": json_value(row[1]),
        }
        for row in rows
    ]

    latest = data[-1] if data else None

    return {
        "metric_id": metric_id,
        "name": config["name"],
        "definition": config["definition"],
        "formula": config["formula"],
        "unit": config["unit"],
        "source": config["source"],
        "reporting_date_column": config["date_column"],
        "latest": latest,
        "data": data,
        "last_refresh": None,
        "freshness_status": "unverified",
        "freshness_note": (
            "The refresh timestamp for the underlying financial reference "
            "feed has not yet been verified."
        ),
        "lineage": config["lineage"],
    }


@app.get("/freshness")
def freshness(user: dict = Depends(require_api_user)):
    return {
        "pipeline_status": "not_checked",
        "financial_feed_status": "unverified",
        "last_refresh": None,
        "source_refresh_metadata_available": False,
        "message": (
            "The API cannot currently verify the latest financial feed refresh."
        ),
        "reason": (
            "Source-level refresh metadata for dq_reference.fact_ledger "
            "and dq_reference.fact_invoice is not available to the API. "
            "The general ETL run summary does not verify these financial feeds."
        ),
    }