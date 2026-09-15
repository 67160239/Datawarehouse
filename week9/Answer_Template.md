# รายงานแลป OLTP OLAP และ Pivot

**ชื่อ:** นาย ศุภกริชณ์ เจริญวุฒิวนพันธ์  
**รหัส:** 67160239  
**กลุ่ม:** 2  

---

## 1. OLTP

### 1.1 การทำงานของ OLTP

OLTP (Online Transaction Processing) เป็นระบบสำหรับจัดการข้อมูลธุรกรรมแบบทันที เช่น การเพิ่ม แก้ไข และเปลี่ยนสถานะข้อมูล โดยต้องรักษาความถูกต้องของข้อมูล

ในการทดลองใช้ฐานข้อมูล `oltp.db` โดย Order `O1004` เริ่มต้นมีสถานะ `PENDING`

### 1.2 ผลการรันรอบที่ 1

```text
Before: [('O1004', 'PENDING')]
Rows updated: 1
After: [('O1004', 'PAID')]
```

รอบแรกสามารถเปลี่ยนสถานะจาก `PENDING` เป็น `PAID` ได้สำเร็จ 1 รายการ

### 1.3 ผลการรันรอบที่ 2

```text
Before: [('O1004', 'PAID')]
Rows updated: 0
After: [('O1004', 'PAID')]
```

รอบที่สองไม่สามารถเปลี่ยนข้อมูลซ้ำได้ เพราะเงื่อนไขกำหนดว่าสถานะเดิมต้องเป็น `PENDING`

### 1.4 ETL

- **Extract:** ดึงข้อมูลจากระบบ OLTP
- **Transform:** ตรวจสอบและจัดรูปแบบข้อมูล
- **Load:** นำข้อมูลเข้าสู่ Data Warehouse

กระบวนการคือ

**OLTP → Extract → Transform → Load → Data Warehouse**

---

## 2. Grain และ Star Schema

### 2.1 Grain

Grain ของ `fact_sales` คือ

**1 แถว = 1 รายการสินค้า (Product Line) ภายใน 1 Order**

ดังนั้น หาก 1 Order มีหลายสินค้า จะมีหลายแถวใน Fact Table

### 2.2 Star Schema

Fact Table คือ `fact_sales`

Dimension ที่เกี่ยวข้อง ได้แก่

- `dim_date`
- `dim_product`
- `dim_store`
- `dim_customer`

โครงสร้างโดยรวม:

```text
              dim_date
                  |
dim_product — fact_sales — dim_store
                  |
            dim_customer
```

### 2.3 PK / FK

Dimension แต่ละตารางมี Primary Key ของตัวเอง ส่วน `fact_sales` ใช้ Foreign Key สำหรับเชื่อมไปยัง Dimension ต่าง ๆ

### 2.4 Dimensions

- **Date:** Year, Month, Day
- **Product:** Product, Category
- **Store:** Store/Branch, Province
- **Customer:** ข้อมูลลูกค้า

### 2.5 Measures

- `quantity` = จำนวนสินค้าที่ขาย
- `unit_price` = ราคาต่อหน่วย
- `amount` = ยอดขายต่อรายการ

`quantity` และ `amount` สามารถใช้ `SUM()` ได้

### 2.6 Hierarchy

**Time:** Year → Month → Day

**Location:** Province → Store / Branch

### 2.7 ผล q01

| line_count | order_count | units | revenue |
|     8      |      6      |   23  |   1390  |

มีรายการขาย 8 รายการ จาก 6 Orders จำนวนสินค้า 23 หน่วย และยอดขายรวม **1,390 บาท**

---

## 3. OLAP

### 3.1 q02 — Roll-up

| Month | Revenue |
| 2026-08 | 490 |
| 2026-09 | 900 |

**Operation: Roll-up**

รวมข้อมูลจากระดับรายการขึ้นมาเป็นระดับเดือน เพื่อดูยอดขายรวมของแต่ละเดือน

### 3.2 q03 — Month × Province

| Month | Province | Revenue |
| 2026-08 | Bangkok | 310 |
| 2026-08 | Chonburi | 180 |
| 2026-09 | Bangkok | 540 |
| 2026-09 | Chonburi | 360 |

ใช้เปรียบเทียบยอดขายตามเดือนและจังหวัด

### 3.3 q04 — Drill-down

| Full Date | Revenue |
| 2026-09-09 | 360 |
| 2026-09-10 | 300 |
| 2026-09-11 | 240 |

**Operation: Drill-down**

```sql
WHERE year = 2026
  AND month = '2026-09'
```

เจาะจากระดับเดือนลงมาเป็นระดับวัน โดยเลือกเฉพาะเดือนกันยายน 2026

### 3.4 q05 — Slice

| Province | Revenue |
| Bangkok | 540 |
| Chonburi | 360 |

**Operation: Slice**

```sql
WHERE year = 2026
  AND month = '2026-09'
```

เลือกเฉพาะข้อมูลเดือนกันยายน แล้วดูยอดขายแยกตามจังหวัด

### 3.5 q06 — Dice

| Category | Province | Revenue |
|   Drink  | Bangkok  |   300   |
|   Drink  | Chonburi |   200   |

**Operation: Dice**

```sql
WHERE year = 2026
  AND month = '2026-09'
  AND category = 'Drink'
  AND province IN ('Bangkok', 'Chonburi')
```

เลือกข้อมูลหลายเงื่อนไขพร้อมกัน ได้แก่ เดือน Category และจังหวัด

### 3.6 q07 — HAVING

| Province | Revenue |
| Bangkok | 540 |

```sql
WHERE year = 2026
  AND month = '2026-09'
HAVING SUM(amount) > 400
```

`WHERE` ใช้กรองข้อมูลก่อน `GROUP BY` ส่วน `HAVING` ใช้กรองผลหลังการรวมข้อมูล จึงเหลือ Bangkok ที่มียอดขาย 540 บาท

### 3.7 q12 — Drill-through

| Order ID | Line No | Product | Quantity | Amount |
|   O1005  |    1    |   Tea    |   6   |   300   |
|   O1006  |    1    |   Cookie  |   3   |   240   |

**ยอดรวม = 540 บาท**

เป็นการเจาะดูรายละเอียดจากระดับจังหวัดลงไปถึง Order และ Product Line

---

## 4. Pivot

### 4.1 q08 — Province × Month

| Province | 2026-08 | 2026-09 | Total |
| Bangkok |     310 |   540  |      850 |
| Chonburi |    180 |   360  |     540 |
| Total |       490 |   900  |    1390 |

ใช้ `SUM(CASE WHEN...)` เพื่อแยกยอดขายตามเดือน

### 4.2 P1 — Province × Month

กำหนด

- Rows = `province`
- Columns = `month`
- Values = `amount`
- Aggregation = `sum`

| Province | 2026-08 | 2026-09 | Total |
| Bangkok    | 310 |     540 |    850 |
| Chonburi   | 180 |     360 |    540 |
| Total      | 490 |     900 |   1390 |

### 4.3 P2 — September Category × Province

กรองเฉพาะเดือน `2026-09`

- Rows = `category`
- Columns = `province`
- Values = `amount`
- Aggregation = `sum`

| Category | Bangkok | Chonburi | Total |
| Drink |      300 |     200 |    500 |
| Snack |      240 |     160 |    400 |
| Total |      540 |     360 |    900 |

ยอดขายเดือนกันยายนรวม **900 บาท**

### 4.4 P3 — Assert Grand Total

```python
assert p1.loc['Total', 'Total'] == df['amount'].sum()
```

ผลการตรวจสอบ:

```text
P3: PASS - P1 grand total is correct
```

Grand Total ของ P1 = **1,390 บาท**  
`df['amount'].sum()` = **1,390 บาท**

ดังนั้นยอดรวมของ Pivot ถูกต้อง

### 4.5 P4 — Export CSV

Export สำเร็จ:

```text
pivot_province_month.csv
pivot_september.csv
```

ผลการรัน:

```text
P4: Exported CSV files successfully
```

### 4.6 ก่อนแก้ — Mean

เมื่อลบ `aggfunc='sum'` ออก Pivot จะใช้ `mean` เป็นค่าเริ่มต้น

Bangkok เดือนกันยายนมีข้อมูล 300 และ 240 บาท

**(300 + 240) / 2 = 270**

ดังนั้นก่อนแก้ Bangkok เดือนกันยายน = **270 บาท**

ค่า 270 เป็นค่าเฉลี่ยของรายการขาย ไม่ใช่ยอดขายรวม

### 4.7 หลังแก้ — Sum

กำหนด

```python
aggfunc='sum'
```

จะได้

**300 + 240 = 540 บาท**

ดังนั้นหากต้องการยอดขายรวม ต้องใช้ `sum`

### 4.8 Excel PivotTable — Drink

กำหนด

- Rows = `province`
- Columns = `month`
- Values = `amount`
- Filter = `category`
- Category = `Drink`
- Values = `Sum`

ผลเดือนกันยายน:

| Province | Revenue |
| Bangkok | 300 |
| Chonburi | 200 |
| Total | 500 |

ยอดขาย Drink เดือนกันยายนรวม **500 บาท**

---

## 5. ตรวจความถูกต้อง

### 5.1 q09 — Revenue รายเดือนและ ALL

| Month | Revenue |
| 2026-08 | 490 |
| 2026-09 | 900 |
| ALL | 1390 |

ตรวจสอบได้ว่า

**490 + 900 = 1,390 บาท**

ดังนั้นยอดรวมทั้งหมดถูกต้อง

### 5.2 q10 — AOV

| Month | Revenue | Orders | AOV | Avg Line |
| 2026-08 | 490 |    3 |   163.33 | 122.50 |
| 2026-09 | 900 |    3 |   300.00 | 225.00 |

สูตร:

**AOV = Revenue ÷ จำนวน Order**

เดือนกันยายน:

**900 ÷ 3 = 300 บาท/Order**

AOV ใช้จำนวน Order ที่ไม่ซ้ำกัน ส่วน Avg Line คือค่าเฉลี่ยของ `amount` ต่อรายการขาย

### 5.3 q11 — ตรวจสอบ JOIN

| Stage | Row Count | Revenue |
| BEFORE_JOIN | 8 | 1390 |
| AFTER_JOIN | 8 | 1390 |

จำนวนแถวและยอดขายเท่ากัน แสดงว่า JOIN ไม่ได้ทำให้เกิดการคูณแถวหรือทำให้ยอดขายเพิ่มขึ้น

### 5.4 ชนิดของ Measure

| Measure | ประเภท |
| quantity | Additive |
| amount | Additive |
| unit_price | ไม่ควร SUM โดยตรง |
| AOV | Calculated Measure |
| Avg Line | Calculated Measure |

`quantity` และ `amount` สามารถนำมารวมด้วย `SUM()` ได้ ส่วน AOV และ Avg Line เป็นค่าที่คำนวณขึ้นมา

---

## 6. สรุป

### 6.1 ข้อค้นพบที่ 1

เดือนกันยายนมียอดขายสูงกว่าเดือนสิงหาคม

- August = 490 บาท
- September = 900 บาท

เพิ่มขึ้น **410 บาท**

### 6.2 ข้อค้นพบที่ 2

เมื่อรวมยอดขายทั้งสองเดือน Bangkok มียอดขายสูงกว่า Chonburi

- Bangkok = 850 บาท
- Chonburi = 540 บาท

ต่างกัน **310 บาท**

### 6.3 ข้อจำกัด

ข้อมูลในการทดลองเป็นข้อมูลจำลองและมีจำนวนรายการไม่มาก จึงเหมาะสำหรับการทดลอง OLTP, OLAP และ Pivot มากกว่าการนำไปวิเคราะห์ธุรกิจจริง