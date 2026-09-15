SELECT
    category,
    province,
    SUM(amount) AS revenue
FROM sales
WHERE year = 2026
  AND month = '2026-09'
  AND category = 'Drink'
  AND province IN ('Bangkok', 'Chonburi')
GROUP BY category, province
ORDER BY province;
