# 🚀 Dashboard Specification Document for Antigravity
## Project: Thai Agriculture & Climate Intelligence Dashboard

---

## 📌 1. ภาพรวมระบบ (System Overview & Architecture)

เอกสารนี้ระบุข้อกำหนดด้านฟังก์ชันการทำงาน (Functional Specifications) การประมวลผลข้อมูล (Data Engine) สูตรคำนวณทางสถิติและเศรษฐศาสตร์ และสถาปัตยกรรม UI/UX สำหรับทีมพัฒนา **Antigravity** เพื่อสร้างแดชบอร์ดการบริหารจัดการและวิเคราะห์ข้อมูลการเกษตรและสภาพอากาศเชิงพื้นที่ของประเทศไทย (Thai Agriculture & Climate Intelligence Dashboard)

### 🎯 เป้าหมายหลัก (Core Purpose)
เปลี่ยนข้อมูลเปิดภาครัฐ (Open Government Data) จากหน่วยงาน สศก., กรมอุตุนิยมวิทยา (TMD), สสน. (HII), GISTDA, กรมชลประทาน (RID), กรมพัฒนาที่ดิน (LDD), และ ปภ. (DDPM) ให้เป็นข้อมูลเชิงลึกที่ตอบโจทย์ตั้งแต่ระดับผู้กำหนดนโยบาย (Policy Makers) นักวิจัย จนถึงเกษตรกรและสถาบันการเงิน

---

## 🎛️ 2. แถบควบคุมกลาง (Global Controls Bar)

แถบควบคุมกลางวางอยู่ตำแหน่ง **Top Navigation Bar** ทำหน้าที่เป็นตัวกรองร่วม (Global Filter Engine) เพื่อให้ข้อมูลในทุก Tab (Tab 1–4) ปรับเปลี่ยนสอดคล้องกันอย่างสมบูรณ์แบบ (Data Synchronization)

### 2.1 ตัวกรองหลัก (Filter Controls)
1. **ชนิดพืช (Crop Selector):**
   * *Type:* Single / Multi-select Dropdown (Default: ข้าวนาปี)
   * *Options:* ข้าวนาปี, ข้าวนาปรัง, ข้าวโพดเลี้ยงสัตว์, มันสำปะหลังโรงงาน, อ้อยโรงงาน (และพืชเศรษฐกิจอื่นรวม 26 ชนิด)
2. **ปี พ.ศ. (Crop / Calendar Year Selector):**
   * *Type:* Slider / Single Dropdown (Default: พ.ศ. 2562)
   * *Range:* พ.ศ. 2550 – 2562 (สถิติการผลิต 13 ปี) / พ.ศ. 2561 – 2562 (สำหรับข้อมูลสภาพอากาศและราคา)
3. **ขอบเขตพื้นที่ (Spatial Boundary Selector):**
   * *Type:* Cascading Dropdown (ระดับประเทศ $\rightarrow$ ภาค $\rightarrow$ จังหวัด)
   * *Options:* 
     * ทั้งประเทศ (Country)
     * ภาคเหนือ, ภาคตะวันออกเฉียงเหนือ, ภาคกลาง, ภาคใต้ (4 ภูมิภาค)
     * รายจังหวัด 77 จังหวัด (Provinces)

### 2.2 พฤติกรรมข้อมูล (Filter State Management)
* **Double-Counting Prevention Rule:** การเลือกระดับ "ทั้งประเทศ" หรือ "ภาค" ต้องดึงข้อมูลตรงจากแถบ `geo_level` (`country` หรือ `region`) ไม่นำค่าระดับจังหวัดมารวมกันซ้ำอีก
* เมื่อมีการเปลี่ยน Filter ให้ทำ Re-render กราฟและ KPI ทั้งหมดใน Tab ที่ใช้งานอยู่แบบ Reactive Transition

---

## 📊 3. รายละเอียดการพัฒนาแต่ละ Tab

---

### TAB 1: ภาพรวมการผลิตสินค้าเกษตร (Overview & Spatial Analysis)

🎯 **วัตถุประสงค์:** ฉายภาพรวมการผลิตสินค้าเกษตร ประเมินการเติบโตย้อนหลัง และชี้เป้าความได้เปรียบเชิงพื้นที่

#### 1. Quick Executive Summary (KPI Cards)
แสดงการเปรียบเทียบเทียบปีต่อปี (Year-over-Year: YoY) ด้วยสูตร:
$$\text{YoY Growth (\%)} = \left( \frac{\text{Value}_t - \text{Value}_{t-1}}{\text{Value}_{t-1}} \right) \times 100$$

* **Card 1: เนื้อที่เพาะปลูก (Planting Area):** แสดงหน่วย "ไร่" และ $\Delta\%$ YoY
* **Card 2: เนื้อที่เก็บเกี่ยว (Harvested Area):** แสดงหน่วย "ไร่" และ อัตราการเก็บเกี่ยว ($\text{Harvest Ratio \%} = \frac{\text{Harvest Area}}{\text{Plant Area}} \times 100$)
* **Card 3: ผลผลิตรวม (Total Production):** แสดงหน่วย "ตัน" และ $\Delta\%$ YoY
* **Card 4: ผลผลิตต่อไร่ (Yield per Rai):** แสดงหน่วย "กก./ไร่" คำนวณจาก:
$$\text{Yield} = \frac{\text{Production (ton)} \times 1000}{\text{Harvested Area (rai)}}$$

#### 2. Spatial Pattern Recognition (Choropleth Map)
* **Visual Component:** แผนที่ประเทศไทยแยกตามสีความเข้มข้นของผลผลิต (Choropleth Map)
* **Data Key:** `data/thai_provinces.geojson` จับคู่กับ `province` ในสถิติ สศก.
* **Metric Switcher:** สลับแสดงระหว่าง **ผลผลิตรวม (ตัน)** หรือ **ผลผลิตต่อไร่ (กก./ไร่)**
* **Interaction:** Hover แสดง Tooltip (ชื่อจังหวัด, ผลผลิตรวม, พื้นที่ปลูก, Yield) และ Click เพื่อ Filter เข้าสู่จังหวัดนั้นๆ

#### 3. Scale vs. Efficiency Matrix (Quadrant Analysis)
* **Chart Type:** 2x2 Quadrant Scatter Plot
* **X-Axis:** เนื้อที่เพาะปลูก/เก็บเกี่ยว (Scale) — หน่วย: ไร่
* **Y-Axis:** ผลผลิตต่อไร่ (Efficiency/Yield) — หน่วย: กก./ไร่
* **Reference Lines:** เส้นแบ่งแกน X และ Y ใช้ค่าเฉลี่ยระดับประเทศ ($\bar{X}, \bar{Y}$)
* **Quadrant Definitions:**
  * **Q1 (Top-Right):** High Scale, High Efficiency (จังหวัดผู้นำการผลิตป้อนตลาด)
  * **Q2 (Top-Left):** Low Scale, High Efficiency (พื้นที่ศักยภาพสูง ผลิตภาพดีแต่พื้นที่จำกัด)
  * **Q3 (Bottom-Left):** Low Scale, Low Efficiency (พื้นที่ผลิตขนาดเล็ก/ไม่เหมาะสม)
  * **Q4 (Bottom-Right):** High Scale, Low Efficiency (พื้นที่ปลูกมาก แต่ผลผลิตต่ำ — *เป้าหมายปรับปรุงเทคโนโลยี/ย้ายพืช*)

---

### TAB 2: สภาพอากาศและสถานการณ์เพาะปลูก (Climate & Seasonality)

🎯 **วัตถุประสงค์:** วิเคราะห์อิทธิพลของฝน อุณหภูมิ การทิ้งช่วง ต่อผลผลิตการเกษตร ทั้งมิติเชิงพื้นที่และฤดูกาล

#### 1. Seasonality Breakdown & Dry Spell Analysis
* **Chart Type:** Dual-axis Combo Line + Bar Chart
* **X-Axis:** เดือน (ม.ค. – ธ.ค.)
* **Primary Y-Axis (Bar):** ปริมาณฝนเฉลี่ยรายเดือน (มม.) จาก HII IDW Spatial Rain
* **Highlight Zone:** แรงเงาเน้นช่วงฤดูฝนหลัก **พ.ค. – ต.ค.** เพื่อประเมินความสมบูรณ์ของน้ำ
* **Secondary Y-Axis (Line):** อุณหภูมิสูงสุด-ต่ำสุดเฉลี่ย ($T_{\max}, T_{\min}$)
* **Dry Spell Indicator Banner:** คำนวณฝนทิ้งช่วง หากปริมาณฝนสะสมในเดือน มิ.ย. – ก.ค. ต่ำกว่าค่าเฉลี่ยย้อนหลัง $> 30\%$ ให้แสดงการเตือน **"สภาวะเสี่ยงฝนทิ้งช่วง (Dry Spell Risk Detected)"**

#### 2. Statistical Rigor (Bivariate Scatter Plot & Regression)
* **Chart Type:** Scatter Plot พร้อม Line of Best Fit (OLS Regression Engine)
* **Variables:** 
  * X = ปริมาณฝนสะสมเชิงพื้นที่ (มม.) / อุณหภูมิ
  * Y = ผลผลิตต่อไร่ (กก./ไร่)
* **Statistical Metrics Engine:** คำนวณค่าและแสดงใน Panel ข้างกราฟ:
  1. **Pearson Correlation Coefficient ($r$):**
     $$r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$$
  2. **Spearman Rank Correlation ($\rho$):** สำหรับประเมินความสัมพันธ์แบบ Non-linear
  3. **p-value:** ทดสอบนัยสำคัญทางสถิติ ($p < 0.05$)
  4. **OLS Linear Model:** $Y = \beta_0 + \beta_1 X$ พร้อมค่า $R^2$

#### 3. Academic Guardrail Panel
* **UI Banner:** กล่องข้อความแจ้งเตือนมาตรฐานวิชาการ (Academic Alert Callout):
  > ⚠️ **Academic Guardrail:** *"Correlation is NOT Causation"* — ค่าสหสัมพันธ์ทางสถิติแสดงเพียงความสัมพันธ์เชิงตัวเลขระหว่างสภาพอากาศและผลผลิต ไม่ได้หมายความว่าปริมาณฝนเป็นปัจจัยเดียวที่กำหนดผลผลิต โปรดพิจารณาปัจจัยเชิงโครงสร้างอื่นๆ ใน Tab 3 ร่วมด้วย

---

### TAB 3: ปัจจัยที่เกี่ยวข้องกับผลผลิต (Production Drivers & Infrastructure)

🎯 **วัตถุประสงค์:** เจาะลึกโครงสร้างพื้นฐาน ปัจจัยกายภาพ ดิน และภัยธรรมชาติ นอกเหนือจากสภาพอากาศ

#### 1. Infrastructure Gap Analysis (Irrigation vs Yield)
* **Chart Type:** Scatter Plot / Grouped Bar
* **Metric:** สัดส่วนพื้นที่ชลประทานเทียบกับพื้นที่เกษตรกรรม (\%) ($X$) ปะทะ ผลผลิตต่อไร่ ($Y$)
$$\text{Irrigation Ratio (\%)} = \left( \frac{\text{Irrigation Area (rai)}}{\text{Total Agricultural Area (rai)}} \right) \times 100$$
* **Insight Key:** เปรียบเทียบผลผลิตระหว่างพื้นที่พึ่งพาน้ำฝน (Rainfed Area, Irrigation < 20%) กับพื้นที่ชลประทาน (Irrigated Area)

#### 2. Soil Suitability Alignment (Agri-Map Integration)
* **Chart Type:** 100% Stacked Bar Chart
* **X-Axis:** จังหวัด หรือ พืชที่เลือก
* **Y-Axis:** สัดส่วนการปลูกพืชบนชั้นความเหมาะสมของดิน (%)
* **Categories:** 
  * $S1$: เหมาะสมสูง (Highly Suitable)
  * $S2$: เหมาะสมปานกลาง (Moderately Suitable)
  * $S3$: เหมาะสมน้อย (Marginally Suitable)
  * $N$: ไม่เหมาะสม (Not Suitable)
* **Actionable Insight:** หากพบสัดส่วนชั้น $S3$ และ $N$ รวมกัน $>30\%$ ระบบจะแจ้งเตือนการปลูกพืชไม่ตรงตามศักยภาพดิน (Mismatched Soil-Crop Allocation)

#### 3. Cost Structure & Mechanization Breakdown
* **Chart Type:** Donut Chart + Horizontal Bar Chart
* **Donut Chart:** โครงสร้างต้นทุนการผลิต (บาท/ไร่) จำแนกตาม:
  * ค่าพันธุ์ | ค่าปุ๋ยเคมี | ค่าสารเคมีกำจัดศัตรูพืช | ค่าน้ำมัน/สูบน้ำ | ค่าเครื่องจักร | ค่าแรงงานคน | ค่าเช่าที่ดิน
* **Bar Chart:** ระดับการใช้เครื่องจักรกลเกษตร (Mechanization Index \%) เทียบกับต้นทุนค่าแรงงานคน

---

### TAB 4: ราคา ต้นทุน และความคุ้มค่า (Farm Economics & Profitability)

🎯 **วัตถุประสงค์:** เชื่อมโยงมิติการผลิตเข้าสู่เศรษฐศาสตร์ ติดตามราคาหน้าฟาร์ม และคำนวณจุดคุ้มทุน

#### 1. Market Intelligence (Farmgate Prices Tracker)
* **Data Source:** สถิติราคาที่เกษตรกรขายได้ ณ ไร่นา รายสัปดาห์ (1,979 รายการ)
* **Chart Type:** Time-series Line Chart แสดงความผันผวนของราคาขายจริง (บาท/กิโลกรัม)
* **KPI Metrics:** 
  * ราคาสูงสุด ($\max$), ราคาต่ำสุด ($\min$), ราคาเฉลี่ย ($\bar{P}$)
  * สภาพคล่องกรอบราคา (Price Volatility Band)

#### 2. Margin Analysis (Profit/Loss Spectrum)
* **Chart Type:** Waterfall Chart หรือ Target Comparison Bar
* **Formula:**
$$\text{Profit Margin (THB/kg)} = \text{Farmgate Price (THB/kg)} - \text{Production Cost (THB/kg)}$$
$$\text{Profit Margin Ratio (\%)} = \left( \frac{\text{Profit Margin}}{\text{Farmgate Price}} \right) \times 100$$
* **Visual Color Code:** เขียว = กำไรสุทธิ (Net Margin > 0) | แดง = ขาดทุน (Net Margin < 0)

#### 3. Interactive Farm Profit & Break-even Calculator
เครื่องมือการคำนวณจุดคุ้มทุนแบบโต้ตอบ (What-If Scenarios Engine) สำหรับเกษตรกรและนักวิเคราะห์:

##### Input Parameters (ผู้ใช้ปรับค่าได้):
1. พื้นที่ปลูก (ไร่) — $[Area]$
2. ผลผลิตคาดการณ์ (กก./ไร่) — $[Yield]$
3. ราคาขายคาดการณ์ (บาท/กก.) — $[Price]$
4. ต้นทุนผันแปร เช่น ปุ๋ย, เมล็ดพันธุ์, แรงงาน (บาท/ไร่) — $[Variable\_Cost]$
5. ต้นทุนคงที่ เช่น ค่าเช่าดิน, ค่าเสื่อมเครื่องจักร (บาท/ไร่) — $[Fixed\_Cost]$

##### Calculation Formulas (มาตรฐาน สศก.):
1. **ต้นทุนรวมต่อไร่ (Total Cost per Rai):**
$$TC_{rai} = Variable\_Cost + Fixed\_Cost$$
2. **ต้นทุนรวมทั้งหมด (Total Cost):**
$$TC_{total} = TC_{rai} \times Area$$
3. **รายได้รวมคาดการณ์ (Total Revenue):**
$$TR = Price \times Yield \times Area$$
4. **กำไรสุทธิคาดการณ์ (Net Profit):**
$$\text{Net Profit} = TR - TC_{total}$$
5. **ผลผลิต ณ จุดคุ้มทุน (Break-even Yield - กก./ไร่):**
$$Y_{BE} = \frac{TC_{rai}}{Price}$$
6. **ราคา ณ จุดคุ้มทุน (Break-even Price - บาท/กก.):**
$$P_{BE} = \frac{TC_{rai}}{Yield}$$

---

## 💾 4. สรุปชุดข้อมูลและการเชื่อมโยง (Data Source Mapping)

| Tab ID | Component UI | Primary File / API Source | Join / Foreign Keys |
|---|---|---|---|
| **Global** | Crop, Year, Area Filters | `สถิติการผลิตสินค้าเกษตรรายปี 2550-2562.xlsx` | `product`, `year`, `province` |
| **Tab 1** | Executive Summary, Map, Matrix | สถิติ สศก. + `data/thai_provinces.geojson` | `province` $\leftrightarrow$ `properties.pro_th` |
| **Tab 2** | Weather Breakdown & Scatter Plot | `data/raw/spatial_rain_hii.csv`, TMD API | `PROV_T`, `YEAR`, `MONTH` |
| **Tab 3** | Infrastructure, Soil, Cost | `provincial_irrigation_rid_oae.csv`, `ldd_soil_suitability.csv` | `province`, `product` |
| **Tab 4** | Farmgate Price & Calculator | `data/raw/oae_farmgate_prices_2561_2562.csv`, `oae_production_cost_structure.csv` | `product`, `year`, `month` |

---

## 🛠️ 5. ข้อแนะนำด้านเทคโนโลยีและการพัฒนา (Tech Stack Recommendations)

1. **Frontend / Application Framework:**
   * React (Next.js / Vite) หรือ Streamlit / Dash (กรณีเน้น Python Data Science Stack)
   * Tailwind CSS สำหรับ UI/Styling และ Responsive Layout
2. **Data Visualization Libraries:**
   * **Plotly.js / ECharts:** สำหรับ Scatter Plots, OLS Trendlines, Dual-axis Charts, และ Stacked Bars
   * **Leaflet / Mapbox / Deck.gl:** สำหรับการเรนเดอร์ Choropleth Map (.GeoJSON)
3. **Data Engine / Statistical Analytics:**
   * Python (Pandas, NumPy, SciPy.stats, Statsmodels) หรือ JavaScript Simple-Statistics library
   * คำนวณ Pearson $r$, Spearman $\rho$, และ OLS Regression บน Server-side หรือ Client-side (in-memory)

---
*เอกสารฉบับนี้พร้อมนำไปใช้งานสำหรับทีม Antigravity ในการพัฒนา Dashboard ต่อไป*