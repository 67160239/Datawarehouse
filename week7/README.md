# Python Data Pipeline Engineering Lab

## 1. วิธีติดตั้งและการเตรียมสภาพแวดล้อม (Installation & Setup)
```bash
# ติดตั้งไลบรารีที่จำเป็น
pip install pandas numpy openpyxl
```

## 2. วิธีการรัน Data Pipeline (Execution)
```bash
python pipeline.py
```

## 3. โครงสร้าง Star Schema Data Warehouse
* **Fact Table:**
  * `fact_sales`: เก็บข้อมูลรายการขาย (Grain: 1 รายการสินค้าต่อ order_id ที่ผ่านการตรวจคุณภาพ)
* **Dimension Tables:**
  * `dim_customer`: ข้อมูลลูกค้า (`customer_key`, `customer_id`, `customer_name`, `province`, `segment`)
  * `dim_product`: ข้อมูลสินค้า (`product_key`, `product_id`, `product_name`, `category`)
  * `dim_date`: มิติด้านเวลา (`date_key`, `full_date`, `day`, `month`, `quarter`, `year`)

## 4. Reflection: เหตุใด Availability จึงมักสำคัญกว่า Strictness ใน Production Pipeline
ในระบบ Production Data Pipeline การรักษาความพร้อมใช้งานของข้อมูล (**Availability**) มีความสำคัญอย่างยิ่งในการขับเคลื่อนธุรกิจแบบ Real-time หรือ Near Real-time หากเลือกใช้แนวคิดแบบ **Strictness** (Fail-fast) เมื่อพบข้อมูลที่มีข้อผิดพลาด เช่น รูปแบบวันที่ผิด หรือรหัสสินค้าไม่ตรง ระบบจะทำการสั่งยกเลิก (Abort) การทำงานของ Batch ทั้งหมดทันที ซึ่งส่งผลให้ข้อมูลที่ถูกต้องจำนวนมากใน Batch นั้นไม่สามารถเข้าสู่ Data Warehouse ได้ เกิดปัญหาข้อมูลขาดหายใน Dashboard และรายงานการตัดสินใจของผู้บริหาร

ในทางกลับกัน การออกแบบ Pipeline ให้เน้น **Availability** ร่วมกับกลไก **Fault Tolerance & Quarantine Isolation** จะทำการกรองเฉพาะแถวที่มีปัญหาแยกออกไปเก็บไว้ใน `quarantine.csv` พร้อมระบุ `reason_code` อย่างชัดเจน ในขณะที่ข้อมูลที่สมบูรณ์จะถูกประมวลผลและโหลดเข้าสู่ Data Warehouse ตามปกติ ทำให้ระบบงานปลายทาง (Downstream Applications) และทีม Business Intelligence สามารถใช้ประโยชน์จากข้อมูลได้อย่างต่อเนื่อง ส่วนทีม Data Quality สามารถเข้ามาตรวจสอบ แก้ไข และประมวลผลข้อมูลใน Quarantine ย้อนหลังได้อย่างเป็นระบบโดยไม่กระทบต่อภาพรวมของธุรกิจ
