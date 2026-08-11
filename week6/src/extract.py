import json
import sqlite3
import pandas as pd
from .config import RAW_DIR, SOURCE_DB

def extract_data():
    """
    Extract data from:
      - customers.csv
      - orders.csv
      - products.json
      - stores table in store.db
    Return a dictionary of DataFrames.
    """
    # 1. อ่านไฟล์ customers.csv
    customers_df = pd.read_csv(RAW_DIR / "customers.csv")

    # 2. อ่านไฟล์ orders.csv
    orders_df = pd.read_csv(RAW_DIR / "orders.csv")

    # 3. อ่านไฟล์ products.json (flatten nested json)
    with open(RAW_DIR / "products.json", "r", encoding="utf-8") as f:
        products_raw = json.load(f)
    
    # กรณีโครงสร้างเป็น list หรือ dict ที่มี key ย่อย
    if isinstance(products_raw, dict):
        # หากอยู่ใน key เช่น 'products' หรือตัวแปรชั้นนอก ให้ดึงค่าลิสต์ออกมาก่อน
        for k in products_raw:
            if isinstance(products_raw[k], list):
                products_raw = products_raw[k]
                break
    
    products_df = pd.json_normalize(products_raw)

    # 4. อ่านตาราง stores จาก store.db
    conn = sqlite3.connect(SOURCE_DB)
    stores_df = pd.read_sql_query("SELECT * FROM stores", conn)
    conn.close()

    return {
        "customers": customers_df,
        "orders": orders_df,
        "products": products_df,
        "stores": stores_df
    }