
-- ============================================================
-- TASK 12: INVOICES, RECEIVABLES & CASH FLOW
-- PulseIQ Analytics
-- ============================================================

-- 1. OPEN INVOICES
-- Include SENT, OVERDUE, PARTIALLY_PAID only

CREATE OR REPLACE VIEW warehouse.task12_open_invoices AS
SELECT
    record->>'invoice_id' AS invoice_id,
    record->>'invoice_number' AS invoice_number,
    record->>'client_id' AS client_id,
    record->>'status' AS status,
    (record->>'invoice_date')::date AS invoice_date,
    (record->>'due_date')::date AS due_date,
    (record->>'total_amount')::numeric AS total_amount,
    (record->>'amount_paid')::numeric AS amount_paid,
    (record->>'balance_due')::numeric AS balance_due,
    COALESCE(
        (record->>'days_past_due_at_cutoff')::integer, 0
    ) AS days_past_due_at_cutoff
FROM dq_reference.fact_invoice
WHERE record->>'status'
    IN ('SENT', 'OVERDUE', 'PARTIALLY_PAID')
  AND (record->>'balance_due')::numeric > 0;


-- 2. RECEIVABLES AGEING

CREATE OR REPLACE VIEW warehouse.task12_receivables_ageing AS
SELECT
    invoice_id,
    invoice_number,
    client_id,
    status,
    invoice_date,
    due_date,
    total_amount,
    amount_paid,
    balance_due,
    days_past_due_at_cutoff,
    CASE
        WHEN days_past_due_at_cutoff <= 30 THEN '0-30 Days'
        WHEN days_past_due_at_cutoff <= 60 THEN '31-60 Days'
        WHEN days_past_due_at_cutoff <= 90 THEN '61-90 Days'
        ELSE '90+ Days'
    END AS ageing_bucket
FROM warehouse.task12_open_invoices;


-- 3. AGEING SUMMARY

CREATE OR REPLACE VIEW warehouse.task12_ageing_summary AS
SELECT
    ageing_bucket,
    COUNT(*) AS invoice_count,
    SUM(balance_due) AS outstanding_amount
FROM warehouse.task12_receivables_ageing
GROUP BY ageing_bucket;


-- 4. CLIENT OUTSTANDING SUMMARY

CREATE OR REPLACE VIEW warehouse.task12_client_outstanding AS
SELECT
    client_id,
    COUNT(*) AS open_invoice_count,
    SUM(balance_due) AS outstanding_amount,
    MAX(days_past_due_at_cutoff) AS max_days_overdue,
    SUM(
        CASE
            WHEN status = 'OVERDUE' THEN balance_due
            ELSE 0
        END
    ) AS overdue_amount
FROM warehouse.task12_open_invoices
GROUP BY client_id;


-- 5. AVERAGE DAYS TO PAY BY CLIENT

CREATE OR REPLACE VIEW warehouse.task12_avg_days_to_pay AS
SELECT
    record->>'client_id' AS client_id,
    COUNT(*) AS paid_invoice_count,
    ROUND(
        AVG((record->>'days_to_pay')::numeric), 2
    ) AS avg_days_to_pay
FROM dq_reference.fact_invoice
WHERE record->>'status' = 'PAID'
  AND record->>'days_to_pay' IS NOT NULL
GROUP BY record->>'client_id';


-- 6. MONTHLY CASH IN VS CASH OUT
-- Bank Operating Account = 1001

CREATE OR REPLACE VIEW warehouse.task12_monthly_cash_flow AS
WITH ledger AS (
    SELECT
        DATE_TRUNC(
            'month',
            (record->>'entry_date')::date
        )::date AS month,
        (record->>'account_code')::integer AS account_code,
        (record->>'debit')::numeric AS debit,
        (record->>'credit')::numeric AS credit,
        record->>'source_type' AS source_type
    FROM dq_reference.fact_ledger
)
SELECT
    month,
    SUM(
        CASE
            WHEN source_type IN ('INVOICE_PAYMENT', 'INTEREST')
            THEN debit ELSE 0
        END
    ) AS cash_in,
    SUM(
        CASE
            WHEN source_type IN (
                'EXPENSE_PAYMENT',
                'SALARY_PAYMENT',
                'GST_SETTLEMENT',
                'STATUTORY_REMITTANCE',
                'BANK_CHARGES'
            )
            THEN credit ELSE 0
        END
    ) AS cash_out,
    SUM(
        CASE
            WHEN source_type IN ('INVOICE_PAYMENT', 'INTEREST')
            THEN debit
            WHEN source_type IN (
                'EXPENSE_PAYMENT',
                'SALARY_PAYMENT',
                'GST_SETTLEMENT',
                'STATUTORY_REMITTANCE',
                'BANK_CHARGES'
            )
            THEN -credit
            ELSE 0
        END
    ) AS net_cash_flow
FROM ledger
WHERE account_code = 1001
  AND source_type <> 'OPENING'
GROUP BY month;


-- 7. RECEIVABLES RECONCILIATION

CREATE OR REPLACE VIEW warehouse.task12_receivables_reconciliation AS
SELECT
    (SELECT COUNT(*)
     FROM warehouse.task12_open_invoices)
        AS open_invoice_count,

    (SELECT COALESCE(SUM(balance_due), 0)
     FROM warehouse.task12_open_invoices)
        AS total_open_receivables,

    (SELECT COALESCE(SUM(outstanding_amount), 0)
     FROM warehouse.task12_ageing_summary)
        AS ageing_bucket_total,

    (SELECT COALESCE(SUM(balance_due), 0)
     FROM warehouse.task12_open_invoices)
    -
    (SELECT COALESCE(SUM(outstanding_amount), 0)
     FROM warehouse.task12_ageing_summary)
        AS reconciliation_difference;