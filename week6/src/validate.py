import sqlite3
from .config import WAREHOUSE_DB

def validate_data(source_sales):
    """
    Validate data loaded into SQLite Warehouse.
    """
    conn = sqlite3.connect(WAREHOUSE_DB)
    cursor = conn.cursor()

    # Query counts and total sales from warehouse
    cursor.execute("SELECT COUNT(*), SUM(sales_amount) FROM fact_sales")
    wh_row = cursor.fetchone()
    warehouse_rows = wh_row[0] if wh_row[0] else 0
    warehouse_total_sales = round(wh_row[1], 2) if wh_row[1] else 0.0

    # Query duplicate orders in warehouse
    cursor.execute("""
        SELECT COUNT(order_id) - COUNT(DISTINCT order_id) FROM fact_sales
    """)
    duplicate_order_ids = cursor.fetchone()[0]

    conn.close()

    # Source transformed data metrics
    source_valid_rows = len(source_sales)
    source_total_sales = round(source_sales["sales_amount"].sum(), 2)

    # Status check
    is_rows_match = source_valid_rows == warehouse_rows
    is_sales_match = abs(source_total_sales - warehouse_total_sales) < 1e-2
    is_no_duplicates = duplicate_order_ids == 0

    status = "PASS" if (is_rows_match and is_sales_match and is_no_duplicates) else "FAIL"

    return {
        "source_valid_rows": source_valid_rows,
        "warehouse_rows": warehouse_rows,
        "duplicate_order_ids": duplicate_order_ids,
        "source_total_sales": source_total_sales,
        "warehouse_total_sales": warehouse_total_sales,
        "status": status
    }