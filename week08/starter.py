from pathlib import Path
import json
import pandas as pd

DATA = Path(__file__).parent / "data"
OUTPUT = Path(__file__).parent / "output"
OUTPUT.mkdir(exist_ok=True)

dq_records = []

def log_dq(step, issue, count):
    dq_records.append({"step": step, "issue": issue, "count": count})

# ==========================================
# TODO 1: Extract ข้อมูลจาก CSV, Excel และ JSON
# ==========================================
print("=== TODO 1: Extract ===")
df_orders_jan = pd.read_csv(DATA / "orders_2026_01.csv")
df_orders_feb = pd.read_csv(DATA / "orders_2026_02.csv")
df_customers = pd.read_csv(DATA / "customers_crm.csv")
df_products = pd.read_excel(DATA / "product_master.xlsx")

with open(DATA / "payments.json", "r", encoding="utf-8") as f:
    payments_data = json.load(f)
df_payments = pd.json_normalize(payments_data)

log_dq("1_Extract", "Raw Orders Jan Count", len(df_orders_jan))
log_dq("1_Extract", "Raw Orders Feb Count", len(df_orders_feb))
log_dq("1_Extract", "Raw Customers Count", len(df_customers))
log_dq("1_Extract", "Raw Products Count", len(df_products))
log_dq("1_Extract", "Raw Payments Count", len(df_payments))

# ==========================================
# TODO 2: Schema Alignment & Concat
# ==========================================
print("=== TODO 2: Schema Alignment & Concat ===")
df_orders_jan.columns = df_orders_jan.columns.str.lower().str.strip()
df_orders_feb.columns = df_orders_feb.columns.str.lower().str.strip()

# Align ชื่อคอลัมน์เดือน ก.พ. ให้ตรงกับ ม.ค.
df_orders_feb = df_orders_feb.rename(columns={
    'ordered_at': 'order_date',
    'qty': 'quantity'
})

discount_col_feb = [col for col in df_orders_feb.columns if 'discount' in col or 'disc' in col]
if discount_col_feb and discount_col_feb[0] != 'discount':
    df_orders_feb = df_orders_feb.rename(columns={discount_col_feb[0]: 'discount'})

# แปลงส่วนลดของทั้งสองเดือนให้เป็น Float อย่างปลอดภัย (รองรับเครื่องหมาย % และข้อความ)
df_orders_jan['discount'] = pd.to_numeric(
    df_orders_jan['discount'].astype(str).str.rstrip('%'), errors='coerce'
).fillna(0)
df_orders_jan['discount'] = df_orders_jan['discount'].apply(lambda x: x / 100.0 if x > 1.0 else x)

df_orders_feb['discount'] = pd.to_numeric(
    df_orders_feb['discount'].astype(str).str.rstrip('%'), errors='coerce'
).fillna(0)
df_orders_feb['discount'] = df_orders_feb['discount'].apply(lambda x: x / 100.0 if x > 1.0 else x)

# รวมตารางคำสั่งซื้อ
df_orders = pd.concat([df_orders_jan, df_orders_feb], ignore_index=True)

# แปลงชนิดข้อมูลตัวเลขให้สมบูรณ์ป้องกัน Type Mismatch
df_orders['quantity'] = pd.to_numeric(df_orders['quantity'], errors='coerce').fillna(0)
df_orders['unit_price'] = pd.to_numeric(df_orders['unit_price'], errors='coerce').fillna(0)

# ==========================================
# TODO 3: Clean, Standardize & Deduplicate
# ==========================================
print("=== TODO 3: Cleaning & Standardization ===")
raw_orders_len = len(df_orders)
df_orders = df_orders.drop_duplicates(subset=["order_id"], keep="last")
log_dq("3_Cleaning", "Duplicate Orders Removed", raw_orders_len - len(df_orders))

df_customers["email"] = df_customers["email"].astype(str).str.lower().str.strip()
df_customers["province"] = df_customers["province"].astype(str).str.strip()

# Map ชื่อจังหวัดมาตรฐาน (รองรับ TH/EN)
province_map = {
    "BKK": "กรุงเทพมหานคร", "กรุงเทพ": "กรุงเทพมหานคร", "กรุงเทพฯ": "กรุงเทพมหานคร", "Bangkok": "กรุงเทพมหานคร", "กทม.": "กรุงเทพมหานคร",
    "CMM": "เชียงใหม่", "Chiang Mai": "เชียงใหม่", "Chiangmai": "เชียงใหม่",
    "PKT": "ภูเก็ต", "Phuket": "ภูเก็ต",
    "ชลบุรี": "ชลบุรี", "Chonburi": "ชลบุรี", "Chon Buri": "ชลบุรี",
    "ระยอง": "ระยอง", "Rayong": "ระยอง",
    "ขอนแก่น": "ขอนแก่น", "ขอนเเก่น": "ขอนแก่น",
    "นนทบุรี": "นนทบุรี", "Nonthaburi": "นนทบุรี",
    "สมุทรปราการ": "สมุทรปราการ", "Samut Prakan": "สมุทรปราการ", "Samutprakan": "สมุทรปราการ",
    "ปทุมธานี": "ปทุมธานี", "Pathum Thani": "ปทุมธานี", "Pathumthani": "ปทุมธานี"
}
df_customers["province"] = df_customers["province"].replace(province_map)
df_customers = df_customers.drop_duplicates(subset=["customer_id"], keep="last")

df_payments = df_payments.drop_duplicates(subset=["order_id"], keep="last")

# ==========================================
# TODO 4: Data Integration (Merge)
# ==========================================
print("=== TODO 4: Data Integration (Merge) ===")
merged = pd.merge(df_orders, df_payments, on="order_id", how="left", indicator="_merge_payment")
log_dq("4_Merge", "Orders without Payment Record", (merged["_merge_payment"] != "both").sum())

merged = pd.merge(merged, df_customers, on="customer_id", how="left", indicator="_merge_cust")
unmatched_cust = (merged["_merge_cust"] != "both").sum()
log_dq("4_Merge", "Orders with Unmatched Customer ID", unmatched_cust)

merged = pd.merge(merged, df_products, on="product_id", how="left", indicator="_merge_prod")
unmatched_prod = (merged["_merge_prod"] != "both").sum()
log_dq("4_Merge", "Orders with Unmatched Product ID", unmatched_prod)

# ==========================================
# TODO 5: Business Rules Validation
# ==========================================
print("=== TODO 5: Business Rules Validation ===")
valid_mask = (
    (merged["quantity"] > 0) & 
    (merged["unit_price"] > 0) & 
    (merged["discount"] >= 0) & 
    (merged["discount"] <= 1) & 
    (merged["payment.status"].astype(str).str.upper() == "PAID") &
    (merged["_merge_cust"] == "both") &
    (merged["_merge_prod"] == "both")
)
log_dq("5_Validation", "Filtered Non-Paid or Invalid Value Orders", (~valid_mask).sum())
fact_df = merged[valid_mask].copy()

fact_df["net_sales"] = fact_df["quantity"] * fact_df["unit_price"] * (1 - fact_df["discount"])

# ==========================================
# TODO 6: Export Master & Fact Tables
# ==========================================
print("=== TODO 6: Export Master & Fact Tables ===")
df_customers[["customer_id", "full_name", "email", "province"]].to_csv(
    OUTPUT / "dim_customer.csv", index=False, encoding="utf-8-sig"
)

prod_cols = ["product_id", "product_name", "category"]
if "standard_price" in df_products.columns:
    prod_cols.append("standard_price")
elif "price" in df_products.columns:
    prod_cols.append("price")
df_products[prod_cols].to_csv(
    OUTPUT / "dim_product.csv", index=False, encoding="utf-8-sig"
)

if "payment.method" in fact_df.columns:
    fact_df = fact_df.rename(columns={"payment.method": "payment_method"})

fact_cols = ["order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price", "discount", "net_sales", "payment_method"]
available_fact_cols = [c for c in fact_cols if c in fact_df.columns]

# Export fact_sales แบบ utf-8-sig
fact_df[available_fact_cols].to_csv(
    OUTPUT / "fact_sales.csv", index=False, encoding="utf-8-sig"
)

# Export data_quality_report แบบ utf-8-sig
pd.DataFrame(dq_records).to_csv(
    OUTPUT / "data_quality_report.csv", index=False, encoding="utf-8-sig"
)

# ==========================================
# TODO 7: Export Summary Tables
# ==========================================
print("=== TODO 7: Export Summary Tables ===")
summary_province = (
    fact_df.groupby("province", as_index=False)["net_sales"]
    .agg(total_net_sales="sum", transaction_count="count")
)
summary_province.to_csv(
    OUTPUT / "summary_by_province.csv", index=False, encoding="utf-8-sig"
)

summary_category = (
    fact_df.groupby("category", as_index=False)["net_sales"]
    .agg(total_net_sales="sum", transaction_count="count")
)
summary_category.to_csv(
    OUTPUT / "summary_by_category.csv", index=False, encoding="utf-8-sig"
)

print("\nกระบวนการ Data Integration เสร็จสิ้นสมบูรณ์!")