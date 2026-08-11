import pandas as pd
import numpy as np
from .config import PROVINCE_MAP

def transform_data(raw):
    # ----------------------------------------------------
    # 1. Transform Customers
    # ----------------------------------------------------
    customers = raw["customers"].copy()
    
    # ลบข้อมูลที่ดูลบ duplicate customer_id
    customers = customers.drop_duplicates(subset=["customer_id"], keep="first")
    
    # Standardize province
    if "province" in customers.columns:
        customers["province"] = customers["province"].astype(str).str.strip().str.lower()
        customers["province"] = customers["province"].map(PROVINCE_MAP).fillna(customers["province"])
    else:
        customers["province"] = "Unknown"

    # Fill Missing values
    customers["email"] = customers["email"].fillna("Unknown")
    customers["name"] = customers["name"].fillna("Unknown")
    
    clean_customers = customers[["customer_id", "name", "province", "email"]].copy()

    # ----------------------------------------------------
    # 2. Transform Products
    # ----------------------------------------------------
    products = raw["products"].copy()
    
    # Map Column Name ให้เป็นมาตรฐานง่ายต่อการใช้งาน
    col_map = {
        "id": "product_id",
        "product_id": "product_id",
        "name": "product_name",
        "product_name": "product_name",
        "details.category": "category",
        "category": "category",
        "details.price": "price",
        "price": "price"
    }
    products = products.rename(columns=col_map)
    
    # Convert price to numeric
    products["price"] = pd.to_numeric(products["price"], errors="coerce").fillna(0.0)
    
    # Fill missing category
    if "category" in products.columns:
        products["category"] = products["category"].fillna("Unknown")
    else:
        products["category"] = "Unknown"

    clean_products = products[["product_id", "product_name", "category", "price"]].drop_duplicates(subset=["product_id"])

    # ----------------------------------------------------
    # 3. Transform Orders & Handling Rejects
    # ----------------------------------------------------
    orders = raw["orders"].copy()
    reject_records = []

    # Drop duplicate order_id
    orders = orders.drop_duplicates(subset=["order_id"], keep="first")

    # Normalize status -> lowercase
    orders["status"] = orders["status"].astype(str).str.strip().str.lower()

    # Parse mixed date formats
    parsed_dates = pd.to_datetime(orders["order_date"], errors="coerce", format="mixed")
    invalid_date_mask = parsed_dates.isna()
    orders["order_date_clean"] = parsed_dates.dt.strftime("%Y-%m-%d")

    # Validation Rules for Orders
    invalid_qty_mask = orders["qty"] <= 0
    invalid_price_mask = orders["unit_price"] <= 0
    invalid_discount_mask = (orders["discount_pct"] < 0) | (orders["discount_pct"] > 100)

    # Collect invalid orders
    invalid_orders_mask = invalid_qty_mask | invalid_price_mask | invalid_discount_mask | invalid_date_mask
    
    rejected_orders = orders[invalid_orders_mask].copy()
    rejected_orders["reject_reason"] = "Invalid order attributes (qty, price, discount, or date)"
    reject_records.append(rejected_orders)

    # Valid Orders Base
    valid_orders = orders[~invalid_orders_mask].copy()
    valid_orders["order_date"] = valid_orders["order_date_clean"]

    # Filter status: paid/completed orders only
    valid_status_orders = valid_orders[valid_orders["status"].isin(["paid", "completed"])].copy()

    # ----------------------------------------------------
    # 4. Merge & Check Master References (Customers / Products)
    # ----------------------------------------------------
    valid_cust_ids = set(clean_customers["customer_id"])
    valid_prod_ids = set(clean_products["product_id"])

    unknown_cust_mask = ~valid_status_orders["customer_id"].isin(valid_cust_ids)
    unknown_prod_mask = ~valid_status_orders["product_id"].isin(valid_prod_ids)

    # Reject Unknown Customer or Product
    rejected_master = valid_status_orders[unknown_cust_mask | unknown_prod_mask].copy()
    rejected_master["reject_reason"] = "Unknown customer_id or product_id not in master"
    reject_records.append(rejected_master)

    # Final Valid Sales
    sales = valid_status_orders[(~unknown_cust_mask) & (~unknown_prod_mask)].copy()

    # ----------------------------------------------------
    # 5. Calculations
    # ----------------------------------------------------
    sales["gross_amount"] = sales["qty"] * sales["unit_price"]
    sales["discount_amount"] = sales["gross_amount"] * sales["discount_pct"] / 100.0
    sales["sales_amount"] = (sales["gross_amount"] - sales["discount_amount"]).round(2)

    # Select final sales columns
    sales_clean = sales[[
        "order_id", "customer_id", "product_id", "order_date", 
        "qty", "unit_price", "discount_pct", "sales_amount"
    ]].copy()

    # Concatenate all rejected records
    if reject_records:
        rejects_df = pd.concat(reject_records, ignore_index=True)
    else:
        rejects_df = pd.DataFrame()

    return clean_customers, clean_products, sales_clean, rejects_df