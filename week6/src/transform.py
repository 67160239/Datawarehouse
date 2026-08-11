import pandas as pd
import numpy as np
from .config import PROVINCE_MAP

def transform_data(raw):
    # ----------------------------------------------------
    # 1. Transform Customers
    # ----------------------------------------------------
    customers = raw["customers"].copy()
    customers = customers.drop_duplicates(subset=["customer_id"], keep="first")
    
    if "province" in customers.columns:
        customers["province"] = customers["province"].astype(str).str.strip().str.lower()
        customers["province"] = customers["province"].map(PROVINCE_MAP).fillna(customers["province"])
    else:
        customers["province"] = "Unknown"

    customers["email"] = customers["email"].fillna("Unknown")
    customers["name"] = customers["name"].fillna("Unknown")
    
    clean_customers = customers[["customer_id", "name", "province", "email"]].copy()

    # ----------------------------------------------------
    # 2. Transform Products (Dynamic Column Matcher)
    # ----------------------------------------------------
    products = raw["products"].copy()
    
    # ค้นหาคอลัมน์จริงจาก DataFrame
    cols = {c.lower(): c for c in products.columns}

    # จับคู่ ID
    id_col = cols.get("product_id") or cols.get("id") or [c for c in products.columns if "id" in c.lower()][0]
    
    # จับคู่ Name
    name_col = cols.get("product_name") or cols.get("name") or [c for c in products.columns if "name" in c.lower()][0]

    # จับคู่ Category
    cat_col = cols.get("category") or cols.get("details.category") or [c for c in products.columns if "cat" in c.lower() or "details" in c.lower()][0]

    # จับคู่ Price
    price_col = cols.get("price") or cols.get("details.price") or [c for c in products.columns if "price" in c.lower() or "cost" in c.lower()][0]

    # สร้าง Clean DataFrame
    clean_products = pd.DataFrame({
        "product_id": products[id_col],
        "product_name": products[name_col],
        "category": products[cat_col].fillna("Unknown"),
        "price": pd.to_numeric(products[price_col], errors="coerce").fillna(0.0)
    }).drop_duplicates(subset=["product_id"])

    # ----------------------------------------------------
    # 3. Transform Orders & Handling Rejects
    # ----------------------------------------------------
    orders = raw["orders"].copy()
    reject_records = []

    orders = orders.drop_duplicates(subset=["order_id"], keep="first")
    orders["status"] = orders["status"].astype(str).str.strip().str.lower()

    parsed_dates = pd.to_datetime(orders["order_date"], errors="coerce", format="mixed")
    invalid_date_mask = parsed_dates.isna()
    orders["order_date_clean"] = parsed_dates.dt.strftime("%Y-%m-%d")

    invalid_qty_mask = orders["qty"] <= 0
    invalid_price_mask = orders["unit_price"] <= 0
    invalid_discount_mask = (orders["discount_pct"] < 0) | (orders["discount_pct"] > 100)

    invalid_orders_mask = invalid_qty_mask | invalid_price_mask | invalid_discount_mask | invalid_date_mask
    
    rejected_orders = orders[invalid_orders_mask].copy()
    rejected_orders["reject_reason"] = "Invalid order attributes (qty, price, discount, or date)"
    reject_records.append(rejected_orders)

    valid_orders = orders[~invalid_orders_mask].copy()
    valid_orders["order_date"] = valid_orders["order_date_clean"]

    valid_status_orders = valid_orders[valid_orders["status"].isin(["paid", "completed"])].copy()

    # ----------------------------------------------------
    # 4. Merge & Check Master References
    # ----------------------------------------------------
    valid_cust_ids = set(clean_customers["customer_id"])
    valid_prod_ids = set(clean_products["product_id"])

    unknown_cust_mask = ~valid_status_orders["customer_id"].isin(valid_cust_ids)
    unknown_prod_mask = ~valid_status_orders["product_id"].isin(valid_prod_ids)

    rejected_master = valid_status_orders[unknown_cust_mask | unknown_prod_mask].copy()
    rejected_master["reject_reason"] = "Unknown customer_id or product_id not in master"
    reject_records.append(rejected_master)

    sales = valid_status_orders[(~unknown_cust_mask) & (~unknown_prod_mask)].copy()

    # ----------------------------------------------------
    # 5. Calculations
    # ----------------------------------------------------
    sales["gross_amount"] = sales["qty"] * sales["unit_price"]
    sales["discount_amount"] = sales["gross_amount"] * sales["discount_pct"] / 100.0
    sales["sales_amount"] = (sales["gross_amount"] - sales["discount_amount"]).round(2)

    sales_clean = sales[[
        "order_id", "customer_id", "product_id", "order_date", 
        "qty", "unit_price", "discount_pct", "sales_amount"
    ]].copy()

    if reject_records:
        rejects_df = pd.concat(reject_records, ignore_index=True)
    else:
        rejects_df = pd.DataFrame()

    return clean_customers, clean_products, sales_clean, rejects_df