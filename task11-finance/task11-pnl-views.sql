
-- ============================================================
-- TASK 11: PROFIT & LOSS AND EXPENSE ANALYTICS
-- ============================================================

-- View 1: Monthly Revenue
-- Group accounts excluded to prevent double counting.
-- Revenue credit balances are negative in debit-positive format.

CREATE OR REPLACE VIEW warehouse.task11_monthly_revenue AS
SELECT
    l.posting_period AS month,
    SUM(-l.signed_amount_debit_positive) AS revenue
FROM warehouse.fact_ledger l
JOIN warehouse.dim_account a
    ON l.account_code = a.account_code
WHERE a.account_type = 'INCOME'
  AND a.is_group = 'N'
  AND l.source_type <> 'OPENING'
GROUP BY l.posting_period;


-- View 2: Monthly Expenses
-- Expense debit balances are positive.

CREATE OR REPLACE VIEW warehouse.task11_monthly_expenses AS
SELECT
    l.posting_period AS month,
    SUM(l.signed_amount_debit_positive) AS expenses
FROM warehouse.fact_ledger l
JOIN warehouse.dim_account a
    ON l.account_code = a.account_code
WHERE a.account_type = 'EXPENSE'
  AND a.is_group = 'N'
  AND l.source_type <> 'OPENING'
GROUP BY l.posting_period;


-- View 3: Monthly Profit and Loss
-- Profit = Revenue - Expenses
-- Margin = Profit / Revenue * 100

CREATE OR REPLACE VIEW warehouse.task11_monthly_pnl AS
SELECT
    r.month,
    r.revenue,
    COALESCE(e.expenses, 0) AS expenses,
    r.revenue - COALESCE(e.expenses, 0) AS net_profit,
    CASE
        WHEN r.revenue <> 0
        THEN ROUND(
            ((r.revenue - COALESCE(e.expenses, 0))
             / r.revenue) * 100,
            2
        )
        ELSE 0
    END AS profit_margin_pct
FROM warehouse.task11_monthly_revenue r
LEFT JOIN warehouse.task11_monthly_expenses e
    ON r.month = e.month;


-- View 4: Expense by Category
-- Uses expense amounts excluding GST.

CREATE OR REPLACE VIEW warehouse.task11_expense_by_category AS
SELECT
    e.category_account AS account_code,
    a.account_name AS expense_category,
    SUM(e.amount_excl_gst) AS total_expense,
    COUNT(*) AS expense_count
FROM warehouse.fact_expense e
JOIN warehouse.dim_account a
    ON e.category_account = a.account_code
WHERE a.account_type = 'EXPENSE'
  AND a.is_group = 'N'
GROUP BY e.category_account, a.account_name;


-- View 5: Top 10 Vendors by Expense

CREATE OR REPLACE VIEW warehouse.task11_top10_vendors AS
SELECT
    v.vendor_id,
    v.vendor_name,
    SUM(e.amount_excl_gst) AS total_expense,
    COUNT(*) AS expense_count
FROM warehouse.fact_expense e
JOIN warehouse.dim_vendor v
    ON e.vendor_id = v.vendor_id
GROUP BY v.vendor_id, v.vendor_name
ORDER BY total_expense DESC
LIMIT 10;