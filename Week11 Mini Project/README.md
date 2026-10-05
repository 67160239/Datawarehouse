# GLASSCORE AI Dashboard

## 1. Project Overview

**GLASSCORE AI** คือแนวคิดระบบ AI สำหรับช่วยตรวจสอบคุณภาพในอุตสาหกรรมกระจกและกระจกเงา โดยนำข้อมูลจากกระบวนการผลิตและการตรวจสอบคุณภาพมาวิเคราะห์ผ่าน Dashboard เพื่อช่วยให้ผู้ใช้งานสามารถติดตามประสิทธิภาพการผลิต วิเคราะห์ปัญหา Defect และมองเห็นข้อมูลที่เกี่ยวข้องกับการใช้ AI ในกระบวนการตรวจสอบได้ง่ายขึ้น

Dashboard นี้จัดทำขึ้นสำหรับรายวิชา **Business Idea Creation** โดยเน้นการนำ Data Analytics และ AI มาใช้สนับสนุนการตัดสินใจในกระบวนการผลิต

---

## 2. Objectives

- ติดตามปริมาณการผลิตและผลการตรวจสอบคุณภาพ
- วิเคราะห์จำนวนและประเภทของ Defect ที่เกิดขึ้น
- วิเคราะห์ Defect ตามสายการผลิต
- วิเคราะห์ลำดับความสำคัญของปัญหาด้วย Pareto Analysis
- เปรียบเทียบการตรวจสอบแบบ AI และ Manual
- แสดงข้อมูลเพื่อสนับสนุนการตัดสินใจด้าน Quality Control
- นำเสนอแนวทางการทำงานของ AI Inspection ในรูปแบบที่เข้าใจง่าย

---

## 3. Dataset

ไฟล์ข้อมูลหลัก:

`data/glass_production_data.xlsx`

ข้อมูลประกอบด้วย **2,000 รายการ** และมีข้อมูลสำคัญ เช่น

- Production ID
- Date
- Product Type
- Production Line
- Shift
- Quantity
- Passed
- Defective
- Defect Type
- Defect Severity
- Inspection Method
- AI Detected
- Inspection Time
- Machine ID
- Temperature
- Humidity
- Production Cost
- Waste Cost

ข้อมูลครอบคลุมการผลิตกระจกหลายประเภท เช่น Tempered Glass, Laminated Glass, Mirror, Clear Glass และ Low-E Glass

---

## 4. Dashboard Structure

### Page 1: Production & Defect Trend

**คำถามหลัก: เราผลิตได้ดีแค่ไหน?**

ประกอบด้วย:

- Total Production
- Total Passed
- Total Defective
- Defect Rate
- Total Waste Cost
- Production & Defect Trend
- Defect by Product Type

หน้านี้ใช้สำหรับติดตามภาพรวมของการผลิตและคุณภาพสินค้า

---

### Page 2: Defect Analysis

**คำถามหลัก: ปัญหาเกิดจากอะไร?**

ประกอบด้วย:

- Defect Type Analysis
- Heatmap: Defect Type × Production Line
- Pareto Analysis

หน้านี้ช่วยให้สามารถระบุประเภท Defect ที่เกิดขึ้นบ่อย และมองเห็นว่าสายการผลิตใดมีปัญหามากที่สุด

---

### Page 3: AI Quality Insight

**คำถามหลัก: AI ช่วยแก้ปัญหาอย่างไร?**

ประกอบด้วย:

- AI Detected
- Manual Inspection
- AI Detection Rate
- AI vs Manual Inspection
- AI Inspection Flow

หน้านี้นำเสนอข้อมูลเกี่ยวกับการตรวจสอบด้วย AI และ Manual รวมถึงแสดง Flow การทำงานของ AI Inspection ตั้งแต่ Camera → AI Detection → Defect Detection → Alert → QA Review

---

## 5. Key Insights

จาก Dashboard สามารถสรุป Insight สำคัญได้ดังนี้:

1. ระบบสามารถติดตามปริมาณการผลิตและจำนวนสินค้าที่ผ่าน/ไม่ผ่านการตรวจสอบได้จาก KPI
2. Defect Rate ช่วยให้เห็นภาพรวมของปัญหาคุณภาพในการผลิต
3. สามารถเปรียบเทียบจำนวน Defect ระหว่าง Product Type และ Production Line ได้
4. Heatmap ช่วยระบุจุดที่มี Defect สูง เพื่อใช้เป็นข้อมูลในการหาสาเหตุ
5. Pareto Analysis ช่วยจัดลำดับ Defect ที่ควรให้ความสำคัญก่อน
6. ข้อมูล Inspection Method สามารถใช้เปรียบเทียบการตรวจสอบแบบ AI และ Manual
7. AI Inspection สามารถนำเสนอเป็นกระบวนการตั้งแต่การรับภาพจาก Camera ไปจนถึงการแจ้งเตือนและตรวจสอบโดย QA

---

## 6. Tools & Technologies

- **Microsoft Power BI** — สำหรับสร้าง Interactive Dashboard
- **Microsoft Excel** — สำหรับจัดเก็บและเตรียม Dataset
- **DAX** — สำหรับสร้าง Measures และคำนวณ KPI
- **Data Visualization** — สำหรับนำเสนอข้อมูลในรูปแบบ Chart, Matrix และ Pareto Analysis
- **AI Concept** — สำหรับแนวคิดการตรวจสอบ Defect จากภาพ

---

## 7. Dashboard Design

แนวทางการออกแบบใช้โทนสีที่สื่อถึงเทคโนโลยีและอุตสาหกรรมกระจก ได้แก่

- Deep Navy: `#0B1F3A`
- Glass Blue: `#1677D2`
- Cyan: `#20C4D9`
- White: `#FFFFFF`

โดยเน้นการออกแบบให้ข้อมูลสำคัญสามารถมองเห็นได้อย่างรวดเร็ว และแบ่ง Dashboard ตามคำถามทางธุรกิจ

---

## 8. Project Structure

```text
GLASSCORE-AI-Dashboard/
│
├── README.md
│
├── data/
│   └── glass_production_data.xlsx
│
├── dashboard/
│   └── GLASSCORE_AI_Dashboard.pbix
│
├── screenshots/
│   ├── overview.png
│   ├── defect_analysis.png
│   └── ai_insight.png
│
├── documentation/
│   └── dashboard_description.pdf
│
└── members/
    └── group_members.txt
```

---

## 9. Project Members

| No. | Name | Role |
|---|---|---|
| 1 | [ชื่อสมาชิก] | Project Leader |
| 2 | [ชื่อสมาชิก] | Data / Dashboard |
| 3 | [ชื่อสมาชิก] | AI / Technology |
| 4 | [ชื่อสมาชิก] | Business / Presentation |
| 5 | [ชื่อสมาชิก] | QA / Documentation |

> สามารถแก้ไขรายชื่อและบทบาทให้ตรงกับสมาชิกจริงของกลุ่มก่อนส่ง Repository

---

## 10. Conclusion

GLASSCORE AI Dashboard ถูกออกแบบมาเพื่อเปลี่ยนข้อมูลการผลิตและการตรวจสอบคุณภาพให้กลายเป็นข้อมูลเชิงวิเคราะห์ที่สามารถนำไปใช้ประกอบการตัดสินใจได้

Dashboard แบ่งการวิเคราะห์ออกเป็น 3 ส่วน ได้แก่ **Production Overview, Defect Analysis และ AI Quality Insight** ทำให้ผู้ใช้งานสามารถมองเห็นตั้งแต่ภาพรวมของการผลิต ไปจนถึงสาเหตุของปัญหา และบทบาทของ AI ในกระบวนการตรวจสอบคุณภาพ

แนวคิดของ GLASSCORE AI จึงมุ่งเน้นการนำ **Data + AI + Visualization** มาประยุกต์ใช้เพื่อสนับสนุนการควบคุมคุณภาพในอุตสาหกรรมกระจก
