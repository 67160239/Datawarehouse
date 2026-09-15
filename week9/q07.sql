SELECT
    province,
    SUM(amount) AS revenue
FROM sales
WHERE year = 2026
  AND month = '2026-09'
GROUP BY province
HAVING SUM(amount) > 400
ORDER BY revenue DESC;
