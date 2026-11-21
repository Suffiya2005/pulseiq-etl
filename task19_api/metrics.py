from task18_config import METRICS, get_metric_config

API_METRIC_IDS = ("M16", "M17", "M18", "M19", "M20")

METRIC_DETAILS = {
    "M16": {
        "definition": "Total booked revenue excluding GST.",
        "formula": "Negative sum of signed ledger amounts for revenue accounts 4001–4004.",
        "source": "dq_reference.fact_ledger",
        "lineage": [
            "dq_reference.fact_ledger",
            "ETL / reference-data loading",
            "warehouse.metric_m16_revenue",
            "Revenue KPI",
            "PulseIQ dashboard",
        ],
    },
    "M17": {
        "definition": "Net profit calculated from ledger revenue and expense accounts.",
        "formula": "Negative sum of signed ledger amounts for accounts 4000–4999 and 5000–5999.",
        "source": "dq_reference.fact_ledger",
        "lineage": [
            "dq_reference.fact_ledger",
            "ETL / reference-data loading",
            "warehouse.metric_m17_net_profit",
            "Net Profit KPI",
            "PulseIQ dashboard",
        ],
    },
    "M18": {
        "definition": "Operating margin expressed as a percentage of revenue.",
        "formula": "Net profit / revenue × 100.",
        "source": "warehouse.metric_m17_net_profit + warehouse.metric_m16_revenue",
        "lineage": [
            "dq_reference.fact_ledger",
            "ETL / reference-data loading",
            "M16 Revenue + M17 Net Profit",
            "warehouse.metric_m18_operating_margin",
            "Operating Margin KPI",
            "PulseIQ dashboard",
        ],
    },
    "M19": {
        "definition": "Ledger payroll cost as a percentage of revenue.",
        "formula": "Ledger payroll cost / revenue × 100.",
        "source": "dq_reference.fact_ledger + warehouse.metric_m16_revenue",
        "lineage": [
            "dq_reference.fact_ledger",
            "ETL / reference-data loading",
            "M16 Revenue + payroll ledger accounts",
            "warehouse.metric_m19_payroll_as_revenue_pct",
            "Payroll % Revenue KPI",
            "PulseIQ dashboard",
        ],
    },
    "M20": {
        "definition": "Days sales outstanding based on closing receivables and recent invoice revenue.",
        "formula": "Closing receivables / last 90-day invoice revenue including GST × 90.",
        "source": "dq_reference.fact_invoice + warehouse.fact_headcount_monthly",
        "lineage": [
            "dq_reference.fact_invoice",
            "Invoice reference-data loading",
            "warehouse.metric_m20_days_sales_outstanding",
            "DSO KPI",
            "PulseIQ dashboard",
        ],
    },
}


def get_api_metric(metric_id: str, role: str):
    if metric_id not in API_METRIC_IDS:
        return None

    config = get_metric_config(metric_id, role)
    if not config or config.get("privacy_type") != "company_only":
        return None

    return {
        **config,
        **METRIC_DETAILS[metric_id],
        "metric_id": metric_id,
    }
