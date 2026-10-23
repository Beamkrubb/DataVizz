# 🌾 Thai Agriculture & Climate Intelligence Dashboard

แดชบอร์ดวิเคราะห์ข้อมูลการเกษตรและสภาพอากาศเชิงพื้นที่ของประเทศไทย ที่เปลี่ยนข้อมูลเปิดภาครัฐ (Open Government Data) จาก สศก. (OAE), กรมอุตุนิยมวิทยา (TMD), สสน. (HII), GISTDA, กรมชลประทาน (RID), กรมพัฒนาที่ดิน (LDD) และ ปภ. (DDPM) ให้เป็นข้อมูลเชิงลึกสำหรับผู้กำหนดนโยบาย นักวิจัย เกษตรกร และสถาบันการเงิน

> **Real Open Data Edition — Zero Mock Data.** ระบบไม่สร้างข้อมูลจำลองใด ๆ หากชุดข้อมูลใดยังไม่พร้อม (ไม่มีไฟล์ / ไม่มี API Key) หน้าจอจะแสดงสถานะนั้นตรง ๆ แทนการแสดงตัวเลขสมมติ

---

## 📚 เอกสารอ้างอิงของโปรเจกต์

| ไฟล์ | เนื้อหา |
|---|---|
| [`dashboard_technical_specification_document_for_antigravity .md`](./dashboard_technical_specification_document_for_antigravity%20.md) | ข้อกำหนดฟังก์ชัน, UI ของแต่ละ Tab, สูตรคำนวณ, Tech Stack (**เอกสารหลัก**) |
| [`data_sources.md`](./data_sources.md) | พจนานุกรมข้อมูล (Schema), แหล่งที่มา, ใบอนุญาต, ข้อจำกัดของแต่ละชุดข้อมูล |
| [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) | ความคืบหน้าการพัฒนาแบบทีละขั้น |

> หมายเหตุ: `data_sources.md` (ข้อ 10) อ้างถึงโครงสร้าง 6 Tab จากเวอร์ชันก่อน ส่วนเอกสาร Spec ใช้ 4 Tab — โปรเจกต์นี้ยึด **4 Tab ตาม Spec** เป็นหลัก

---

## 🎛️ Global Controls Bar

ตัวกรองร่วมที่ทำให้ทุก Tab อัปเดตพร้อมกัน

- **ชนิดพืช** — Single/Multi-select (ค่าเริ่มต้น: ข้าวนาปี) จาก 26 ชนิด
- **ปี พ.ศ.** — 2550–2562 สำหรับสถิติการผลิต / 2561–2562 สำหรับสภาพอากาศและราคา (ค่าเริ่มต้น: 2562)
- **ขอบเขตพื้นที่** — ทั้งประเทศ → ภาค (4 ภาค) → จังหวัด (77 จังหวัด)
- **กฎป้องกันการนับซ้ำ (Double-Counting Prevention):** ระดับประเทศ/ภาค อ่านค่าจากแถว `geo_level = country / region` โดยตรง ห้ามรวมค่าจากระดับจังหวัดซ้ำ

## 📊 โครงสร้าง Dashboard (4 Tabs)

| Tab | ชื่อ | องค์ประกอบหลัก |
|---|---|---|
| 1 | ภาพรวมการผลิต (Overview & Spatial) | KPI Cards (YoY, Harvest Ratio, Yield) · Choropleth Map · Scale vs Efficiency Quadrant |
| 2 | สภาพอากาศและฤดูกาล (Climate & Seasonality) | Rain/Temp Dual-axis Chart · Dry Spell Alert · Scatter + OLS, Pearson r, Spearman ρ, p-value, R² · Academic Guardrail |
| 3 | ปัจจัยการผลิต (Drivers & Infrastructure) | Irrigation Ratio vs Yield · Soil Suitability S1/S2/S3/N (เตือนเมื่อ S3+N > 30%) · Cost Donut + Mechanization |
| 4 | เศรษฐศาสตร์ฟาร์ม (Farm Economics) | Farmgate Price Tracker · Margin Analysis · Break-even Calculator |

## 🧮 สูตรคำนวณหลัก

| ตัวชี้วัด | สูตร |
|---|---|
| YoY Growth (%) | (Vₜ − Vₜ₋₁) / Vₜ₋₁ × 100 |
| Harvest Ratio (%) | Harvest Area / Plant Area × 100 |
| Yield (กก./ไร่) | Production (ตัน) × 1000 / Harvest Area (ไร่) |
| Irrigation Ratio (%) | Irrigation Area / Agricultural Area × 100 |
| Profit Margin (บาท/กก.) | Farmgate Price − Production Cost |
| Margin Ratio (%) | Profit Margin / Farmgate Price × 100 |
| Dry Spell Risk | ฝนสะสม มิ.ย.–ก.ค. ต่ำกว่าค่าเฉลี่ยย้อนหลัง > 30% |
| Break-even | TC_rai = VC + FC · TR = P × Y × A · Y_BE = TC_rai / P · P_BE = TC_rai / Y |

---

## 💾 ชุดข้อมูลที่ระบบต้องการ

ไฟล์ข้อมูลดิบ **ไม่ได้รวมอยู่ใน Repository** ต้องดาวน์โหลดจากแหล่งต้นทางแล้ววางตามตำแหน่งด้านล่าง (รายละเอียด Schema ดูที่ `data_sources.md`)

| ไฟล์ | หน่วยงาน | ใช้ใน |
|---|---|---|
| `data/สถิติการผลิตสินค้าเกษตรรายปี 2550-2562.xlsx` | สศก. | Global, Tab 1–3 |
| `data/thai_provinces.geojson` | OpenGISData-Thailand | Tab 1 (Join: `properties.pro_th`) |
| `data/raw/spatial_rain_hii.csv` | สสน. | Tab 2 |
| `data/raw/national_rain_1970_current.csv` | สสน. | Tab 2 |
| `data/raw/provincial_temp_2018_2019.csv` | สสน. | Tab 2 |
| `data/raw/tmd_agromet_sample.json` | TMD (API fallback cache) | Tab 2 |
| `data/raw/provincial_irrigation_rid_oae.csv` | กรมชลประทาน / สศก. | Tab 3 |
| `data/raw/ldd_soil_suitability.csv` | กรมพัฒนาที่ดิน | Tab 3 |
| `data/raw/oae_production_cost_structure.csv` | สศก. | Tab 3, 4 |
| `data/raw/disaster_affected_agricultural_area.csv` | DOAE / ปภ. | Tab 3 |
| `data/raw/oae_farmgate_prices_2561_2562.csv` | สศก. (Catalog ID 35) | Tab 4 |

บริการ API ภายนอก: TMD `WeatherTodayByAgro/v1` และ GISTDA `agriculture-07` (ต้องใช้ API Key — ตั้งค่าผ่าน environment variable `GISTDA_API_KEY`)

---

## 🛠️ Tech Stack

- **App:** Python 3.10+ · [Streamlit](https://streamlit.io)
- **Visualization:** Plotly (Scatter/OLS, Dual-axis, Stacked Bar, Donut, Waterfall, Choropleth)
- **Data & Statistics:** pandas · NumPy · SciPy (`pearsonr`, `spearmanr`, `linregress`)
- **Testing:** pytest

## 📁 โครงสร้างโปรเจกต์ (เป้าหมาย)

```
DataVizz/
├── app.py                  # Streamlit entry point + Global Controls Bar
├── src/
│   ├── config.py           # paths, crop list, regions, constants
│   ├── data_loader.py      # อ่าน/ตรวจสอบไฟล์ข้อมูล + รายงานสถานะ
│   ├── filters.py          # Global filter state + double-counting rule
│   ├── metrics.py          # YoY, yield, ratios, margin, break-even
│   ├── stats.py            # Pearson, Spearman, OLS, R²
│   └── tabs/               # tab1_overview.py … tab4_economics.py
├── data/
│   └── raw/                # ไฟล์ CSV/JSON จากแหล่งต้นทาง (ไม่ commit)
├── tests/                  # unit tests ของสูตรคำนวณ
├── requirements.txt
├── README.md
└── PROJECT_STATUS.md
```

## ▶️ การติดตั้งและใช้งาน

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
pytest                           # รันชุดทดสอบสูตรคำนวณ
```

## ⚖️ ใบอนุญาตข้อมูล

ข้อมูลทั้งหมดเป็นสิทธิ์ของหน่วยงานเจ้าของข้อมูล ภายใต้ Open Government Data License / TMD Open Data License ตามที่ระบุใน `data_sources.md` ผลการวิเคราะห์เชิงสถิติแสดงความสัมพันธ์เท่านั้น — *Correlation is NOT Causation*
