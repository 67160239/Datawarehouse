SELECT
    'BEFORE_JOIN' AS stage,
    COUNT(*) AS row_count,
    SUM(quantity * unit_price) AS revenue
FROM fact_sales

UNION ALL

SELECT
    'AFTER_JOIN' AS stage,
    COUNT(*) AS row_count,
    SUM(amount) AS revenue
FROM sales;
