"""Department-scoped Manager KPI loader for PulseIQ Task 18."""
import re
MANAGER_METRICS = {"M22", "M23", "M24", "M25"}

BASE_CTE = """
WITH task_records AS (
    SELECT
        source_row,
        record ->> 'assignee_employee_id' AS employee_id,
        record ->> 'team_id' AS team_id,
        record ->> 'sprint_id' AS sprint_id,
        record ->> 'status' AS status,
        record ->> 'completed_on_time' AS completed_on_time,
        NULLIF(record ->> 'started_date', '')::timestamp AS started_at,
        NULLIF(record ->> 'completed_date', '')::timestamp AS completed_at,
        NULLIF(record ->> 'story_points', '')::numeric AS story_points
    FROM dq_reference.fact_task
),
history_matches AS (
    SELECT
        t.*,
        e.department_id,
        COUNT(*) OVER (
            PARTITION BY t.source_row
        ) AS history_match_count
    FROM task_records t
    JOIN warehouse.dim_employee e
      ON e.employee_id = t.employee_id
     AND t.started_at IS NOT NULL
     AND t.started_at::date >= e.valid_from
     AND (
          e.valid_to IS NULL
          OR t.started_at::date <= e.valid_to
     )
),
authorized_tasks AS (
    SELECT *
    FROM history_matches
    WHERE history_match_count = 1
      AND department_id = ANY(%s)
)
"""

MANAGER_QUERIES = {
    "M22": BASE_CTE + """
        SELECT
            sprint_id AS reporting_period,
            team_id AS dimension_value,
            sprint_id AS group_name,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'Done'
                )::numeric
                / NULLIF(
                    COUNT(*) FILTER (
                        WHERE COALESCE(status, '') <> 'Cancelled'
                    ), 0
                ),
                4
            ) AS metric_value,
            COUNT(*) FILTER (
                WHERE COALESCE(status, '') <> 'Cancelled'
            ) AS privacy_count
        FROM authorized_tasks
        WHERE team_id IS NOT NULL AND sprint_id IS NOT NULL
        GROUP BY sprint_id, team_id
        ORDER BY sprint_id, team_id
    """,

    "M23": BASE_CTE + """
        SELECT
            sprint_id AS reporting_period,
            team_id AS dimension_value,
            sprint_id AS group_name,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'Done'
                      AND completed_on_time = 'Y'
                )::numeric
                / NULLIF(
                    COUNT(*) FILTER (WHERE status = 'Done'), 0
                ),
                4
            ) AS metric_value,
            COUNT(*) FILTER (
                WHERE status = 'Done'
            ) AS privacy_count
        FROM authorized_tasks
        WHERE team_id IS NOT NULL AND sprint_id IS NOT NULL
        GROUP BY sprint_id, team_id
        ORDER BY sprint_id, team_id
    """,

    "M24": BASE_CTE + """
        SELECT
            sprint_id AS reporting_period,
            team_id AS dimension_value,
            sprint_id AS group_name,
            SUM(story_points) FILTER (
                WHERE status = 'Done'
            ) AS metric_value,
            COUNT(*) FILTER (
    WHERE status = 'Done'
) AS privacy_count
        FROM authorized_tasks
        WHERE team_id IS NOT NULL AND sprint_id IS NOT NULL
        GROUP BY sprint_id, team_id
        ORDER BY sprint_id, team_id
    """,

    "M25": BASE_CTE + """
        SELECT
            sprint_id AS reporting_period,
            team_id AS dimension_value,
            sprint_id AS group_name,
            AVG(
                EXTRACT(EPOCH FROM (completed_at - started_at))
                / 86400.0
            ) FILTER (
                WHERE status = 'Done'
                  AND started_at IS NOT NULL
                  AND completed_at IS NOT NULL
                  AND completed_at >= started_at
            ) AS metric_value,
           COUNT(*) FILTER (
    WHERE status = 'Done'
      AND started_at IS NOT NULL
      AND completed_at IS NOT NULL
      AND completed_at >= started_at
) AS privacy_count
        FROM authorized_tasks
        WHERE team_id IS NOT NULL AND sprint_id IS NOT NULL
        GROUP BY sprint_id, team_id
        ORDER BY sprint_id, team_id
    """,
}


def load_manager_metric(
    metric_id,
    department_ids,
    query_runner,
    suppress_fn,
    metric_config,
):
    """Load one approved KPI within the authenticated department scope."""

    if metric_id not in MANAGER_METRICS:
        raise PermissionError("This KPI is not approved for Manager access.")

    if not isinstance(department_ids, (list, tuple)):
        raise PermissionError("Invalid Manager department assignment.")

    departments = list(dict.fromkeys(
        value.strip()
        for value in department_ids
        if isinstance(value, str) and value.strip()
    ))

    if not departments:
        raise PermissionError("No authorized department is assigned.")

    if any(
        not re.fullmatch(r"D\d{2}", department_id)
        for department_id in departments
    ):
        raise PermissionError("Invalid Manager department assignment.")

    if not callable(query_runner) or not callable(suppress_fn):
        raise TypeError("Required database or privacy function is unavailable.")
    if not metric_config or metric_config.get("privacy_type") != "task_count":
        raise PermissionError("This KPI is not approved for task aggregation.")

    minimum = metric_config.get("minimum")

    if not isinstance(minimum, int) or minimum < 5:
        raise ValueError("Manager privacy threshold must be at least five.")

    query = MANAGER_QUERIES[metric_id]

    result = query_runner(query, params=[departments])

    if result is None or result.empty:
        return result

    result = suppress_fn(
        result,
        count_column="privacy_count",
        minimum=minimum,
    )

    # Hide the duplicate sprint label for suppressed groups as well.
    suppressed = result["privacy_status"].eq("Suppressed")
    result.loc[suppressed, "reporting_period"] = None

    return result