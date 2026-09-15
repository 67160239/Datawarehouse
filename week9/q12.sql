SELECT
    order_id,
    line_no,
    product_name,
    quantity,
    amount
FROM sales
WHERE year = 2026
  AND month = '2026-09'
  AND province = 'Bangkok'
ORDER BY order_id, line_no;
