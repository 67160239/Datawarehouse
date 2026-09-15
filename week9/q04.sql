SELECT
    full_date,
    SUM(amount) AS revenue
FROM sales
WHERE year = 2026
  AND month = '2026-09'
GROUP BY full_date
ORDER BY full_date;
