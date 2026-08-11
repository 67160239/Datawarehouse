import sqlite3
from .config import WAREHOUSE_DB

def load_data(customers, products, sales):
    """
    Create/load tables into warehouse.db with UPSERT / INSERT OR IGNORE logic
    to prevent duplication upon rerun.
    """
    WAREHOUSE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(WAREHOUSE_DB)
    cursor = conn.cursor()

    # 1. Create Tables with UNIQUE / PRIMARY KEY constraints
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_id TEXT PRIMARY KEY,
        name TEXT,
        province TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_product (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        category TEXT,
        price REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_sales (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        product_id TEXT,
        order_date TEXT,
        qty INTEGER,
        unit_price REAL,
        discount_pct REAL,
        sales_amount REAL,
        FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),
        FOREIGN KEY (product_id) REFERENCES dim_product (product_id)
    )
    """)

    # 2. Insert or Replace / Ignore Data
    cursor.executemany("""
    INSERT OR REPLACE INTO dim_customer (customer_id, name, province, email)
    VALUES (?, ?, ?, ?)
    """, customers[["customer_id", "name", "province", "email"]].to_numpy().tolist())

    cursor.executemany("""
    INSERT OR REPLACE INTO dim_product (product_id, product_name, category, price)
    VALUES (?, ?, ?, ?)
    """, products[["product_id", "product_name", "category", "price"]].to_numpy().tolist())

    cursor.executemany("""
    INSERT OR IGNORE INTO fact_sales (order_id, customer_id, product_id, order_date, qty, unit_price, discount_pct, sales_amount)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sales[["order_id", "customer_id", "product_id", "order_date", "qty", "unit_price", "discount_pct", "sales_amount"]].to_numpy().tolist())

    conn.commit()
    conn.close()