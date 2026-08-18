import os
import sqlite3
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# Task 1: Pipeline Configuration
# ==========================================
@dataclass
class PipelineConfig:
    excel_file_path: str = "Python_Data_Pipeline_Lab_Dataset (1).xlsx"
    db_path: str = "retail_dw.db"
    quarantine_path: str = "quarantine.csv"
    run_log_path: str = "pipeline_run_log.csv"
    batch_list: List[str] = field(default_factory=lambda: ["orders_batch_1", "orders_batch_2", "orders_batch_3"])
    error_mode: str = "quarantine"  # 'quarantine' or 'fail'

# ==========================================
# Database Initialization (Star Schema)
# ==========================================
def init_db(db_path: str):
    """Initialize SQLite Star Schema database tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Task 3: Star Schema Tables Creation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        province TEXT,
        segment TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_product (
        product_key INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE NOT NULL,
        product_name TEXT,
        category TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_date (
        date_key INTEGER PRIMARY KEY,
        full_date TEXT UNIQUE NOT NULL,
        day INTEGER,
        month INTEGER,
        quarter INTEGER,
        year INTEGER
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_sales (
        order_id TEXT PRIMARY KEY,
        date_key INTEGER,
        customer_key INTEGER,
        product_key INTEGER,
        quantity INTEGER,
        unit_price REAL,
        discount_pct REAL,
        gross_amount REAL,
        net_amount REAL,
        payment_method TEXT,
        sales_channel TEXT,
        updated_at TEXT,
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
        FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
        FOREIGN KEY (product_key) REFERENCES dim_product(product_key)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_run_log (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch TEXT,
        started_at TEXT,
        ended_at TEXT,
        rows_read INTEGER,
        rows_valid INTEGER,
        rows_quarantine INTEGER,
        rows_loaded INTEGER,
        status TEXT
    )""")

    conn.commit()
    conn.close()

# ==========================================
# Task 1, 2, 3 & 4: Pipeline Execution
# ==========================================
def load_dimensions(excel_path: str, conn: sqlite3.Connection):
    """Load and upsert dimension tables from customers and products sheets"""
    xls = pd.ExcelFile(excel_path)
    
    if 'customers' in xls.sheet_names:
        cust_df = pd.read_excel(xls, 'customers')
        for _, row in cust_df.iterrows():
            conn.execute("""
                INSERT INTO dim_customer (customer_id, customer_name, province, segment)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    customer_name=excluded.customer_name,
                    province=excluded.province,
                    segment=excluded.segment
            """, (str(row['customer_id']).strip(), row.get('customer_name'), row.get('province'), row.get('segment')))

    if 'products' in xls.sheet_names:
        prod_df = pd.read_excel(xls, 'products')
        for _, row in prod_df.iterrows():
            conn.execute("""
                INSERT INTO dim_product (product_id, product_name, category)
                VALUES (?, ?, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    product_name=excluded.product_name,
                    category=excluded.category
            """, (str(row['product_id']).strip(), row.get('product_name'), row.get('category')))

    conn.commit()

def process_batch(sheet_name: str, config: PipelineConfig) -> bool:
    start_time = datetime.now().isoformat()
    logging.info(f"--- Processing Batch: {sheet_name} ---")
    
    conn = sqlite3.connect(config.db_path)
    
    try:
        # Load Dimensions
        if os.path.exists(config.excel_file_path):
            load_dimensions(config.excel_file_path, conn)

        # 1. Extract
        if os.path.exists(config.excel_file_path):
            xls = pd.ExcelFile(config.excel_file_path)
            df = pd.read_excel(xls, sheet_name)
        else:
            # Fallback for CSV files
            csv_file = f"{sheet_name}.csv"
            df = pd.read_csv(csv_file)

        rows_read = len(df)

        # 2. Transform & Data Quality Validation
        quarantine_list = []
        valid_rows = []

        # Get valid dimension keys
        valid_custs = set(pd.read_sql("SELECT customer_id FROM dim_customer", conn)['customer_id'].astype(str))
        valid_prods = set(pd.read_sql("SELECT product_id FROM dim_product", conn)['product_id'].astype(str))

        # Value Mappings
        payment_map = {
            'CC': 'Credit Card', 'credit card': 'Credit Card', 'CREDIT_CARD': 'Credit Card',
            'TRANSFER': 'Transfer', 'transfer': 'Transfer',
            'cash': 'Cash', 'CASH': 'Cash'
        }
        channel_map = {
            'web': 'Online', 'ONLINE': 'Online', 'online': 'Online',
            'store': 'In-Store', 'STORE': 'In-Store', 'in-store': 'In-Store'
        }

        for idx, row in df.iterrows():
            reasons = []

            # Date Parsing
            order_date = pd.to_datetime(row.get('order_date'), errors='coerce')
            if pd.isna(order_date):
                reasons.append("INVALID_DATE")

            # Numeric Coercion & Validation
            qty = pd.to_numeric(row.get('quantity'), errors='coerce')
            price = pd.to_numeric(row.get('unit_price'), errors='coerce')
            disc = pd.to_numeric(row.get('discount_pct'), errors='coerce')

            if pd.isna(qty) or qty <= 0:
                reasons.append("INVALID_QUANTITY")
            if pd.isna(price) or price <= 0:
                reasons.append("INVALID_UNIT_PRICE")
            if pd.isna(disc) or not (0 <= disc <= 100):
                reasons.append("INVALID_DISCOUNT")

            # Referential Integrity Checks
            cust_id = str(row.get('customer_id')).strip() if pd.notna(row.get('customer_id')) else ""
            prod_id = str(row.get('product_id')).strip() if pd.notna(row.get('product_id')) else ""

            if not cust_id or cust_id not in valid_custs:
                reasons.append("CUSTOMER_NOT_FOUND")
            if not prod_id or prod_id not in valid_prods:
                reasons.append("PRODUCT_NOT_FOUND")

            if reasons:
                row_dict = row.to_dict()
                row_dict['reason_code'] = "|".join(reasons)
                row_dict['source_batch'] = sheet_name
                quarantine_list.append(row_dict)
            else:
                gross = qty * price
                net = gross * (1 - (disc / 100.0))
                
                raw_pay = str(row.get('payment_method')).strip() if pd.notna(row.get('payment_method')) else ''
                raw_chan = str(row.get('sales_channel')).strip() if pd.notna(row.get('sales_channel')) else ''
                
                pay_method = payment_map.get(raw_pay, raw_pay)
                channel = channel_map.get(raw_chan, raw_chan)
                
                updated_at = str(row.get('updated_at')) if pd.notna(row.get('updated_at')) else start_time

                valid_rows.append({
                    'order_id': str(row['order_id']).strip(),
                    'order_date': order_date,
                    'customer_id': cust_id,
                    'product_id': prod_id,
                    'quantity': int(qty),
                    'unit_price': float(price),
                    'discount_pct': float(disc),
                    'gross_amount': round(float(gross), 2),
                    'net_amount': round(float(net), 2),
                    'payment_method': pay_method,
                    'sales_channel': channel,
                    'updated_at': updated_at
                })

        # Save Quarantine Records
        if quarantine_list:
            q_df = pd.DataFrame(quarantine_list)
            header = not os.path.exists(config.quarantine_path)
            q_df.to_csv(config.quarantine_path, mode='a', index=False, header=header)

        valid_df = pd.DataFrame(valid_rows)
        rows_valid = len(valid_df)
        rows_quarantine = len(quarantine_list)

        # Deduplicate valid records by order_id, keeping the latest updated_at
        if not valid_df.empty:
            valid_df = valid_df.sort_values('updated_at').groupby('order_id').last().reset_index()

        # 3. Load & Incremental Upsert
        rows_loaded = 0
        if not valid_df.empty:
            cursor = conn.cursor()
            for _, row in valid_df.iterrows():
                dt = row['order_date']
                date_key = int(dt.strftime('%Y%m%d'))
                cursor.execute("""
                    INSERT OR IGNORE INTO dim_date (date_key, full_date, day, month, quarter, year)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date_key, dt.strftime('%Y-%m-%d'), dt.day, dt.month, dt.quarter, dt.year))

                cust_key = cursor.execute("SELECT customer_key FROM dim_customer WHERE customer_id=?", (row['customer_id'],)).fetchone()[0]
                prod_key = cursor.execute("SELECT product_key FROM dim_product WHERE product_id=?", (row['product_id'],)).fetchone()[0]

                # Upsert logic (Idempotent)
                cursor.execute("""
                    INSERT INTO fact_sales (
                        order_id, date_key, customer_key, product_key, quantity, unit_price,
                        discount_pct, gross_amount, net_amount, payment_method, sales_channel, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_id) DO UPDATE SET
                        date_key=excluded.date_key,
                        customer_key=excluded.customer_key,
                        product_key=excluded.product_key,
                        quantity=excluded.quantity,
                        unit_price=excluded.unit_price,
                        discount_pct=excluded.discount_pct,
                        gross_amount=excluded.gross_amount,
                        net_amount=excluded.net_amount,
                        payment_method=excluded.payment_method,
                        sales_channel=excluded.sales_channel,
                        updated_at=excluded.updated_at
                    WHERE excluded.updated_at >= fact_sales.updated_at
                """, (
                    row['order_id'], date_key, cust_key, prod_key, row['quantity'],
                    row['unit_price'], row['discount_pct'], row['gross_amount'],
                    row['net_amount'], row['payment_method'], row['sales_channel'], row['updated_at']
                ))
                if cursor.rowcount > 0:
                    rows_loaded += 1

            conn.commit()

        end_time = datetime.now().isoformat()

        # Write Run Log to DB and CSV
        log_entry = {
            'batch': sheet_name,
            'started_at': start_time,
            'ended_at': end_time,
            'rows_read': rows_read,
            'rows_valid': rows_valid,
            'rows_quarantine': rows_quarantine,
            'rows_loaded': rows_loaded,
            'status': 'SUCCESS'
        }
        
        conn.execute("""
            INSERT INTO pipeline_run_log (batch, started_at, ended_at, rows_read, rows_valid, rows_quarantine, rows_loaded, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sheet_name, start_time, end_time, rows_read, rows_valid, rows_quarantine, rows_loaded, 'SUCCESS'))
        conn.commit()

        log_df = pd.DataFrame([log_entry])
        header = not os.path.exists(config.run_log_path)
        log_df.to_csv(config.run_log_path, mode='a', index=False, header=header)

        logging.info(f"Batch {sheet_name} Completed successfully.")
        return True

    except Exception as e:
        conn.rollback()
        end_time = datetime.now().isoformat()
        logging.error(f"Batch {sheet_name} failed: {str(e)}")
        
        conn.execute("""
            INSERT INTO pipeline_run_log (batch, started_at, ended_at, rows_read, rows_valid, rows_quarantine, rows_loaded, status)
            VALUES (?, ?, ?, 0, 0, 0, 0, ?)
        """, (sheet_name, start_time, end_time, f'FAILED: {str(e)}'))
        conn.commit()
        return False
    finally:
        conn.close()

# ==========================================
# Task 5: Orchestration
# ==========================================
def run_pipeline(config: PipelineConfig):
    init_db(config.db_path)
    
    # Requirement Task 4: Run batch_1, batch_1 (re-run to test idempotency), batch_2, batch_3
    schedule = ["orders_batch_1", "orders_batch_1", "orders_batch_2", "orders_batch_3"]
    
    for batch in schedule:
        process_batch(batch, config)

if __name__ == "__main__":
    cfg = PipelineConfig()
    run_pipeline(cfg)