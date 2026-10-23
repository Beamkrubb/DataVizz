# 📈 Project Status — Thai Agriculture & Climate Intelligence Dashboard

_Last updated: 2026-10-23_

## Summary

| # | Phase | Status | Commit |
|---|---|---|---|
| 0 | Project README (from spec + data dictionary) | ✅ Done | `docs: add project README` |
| 1 | Scaffold: requirements, `.gitignore`, `src/config.py`, status file | ✅ Done | `chore: scaffold project` |
| 2 | Data loader + dataset status registry | ✅ Done | `feat: data loader` |
| 3 | Metrics & statistics engine + unit tests | ✅ Done | `feat: metrics and statistics engine` |
| 4 | App shell + Global Controls Bar (double-counting rule) | ✅ Done | `feat: app shell and global controls` |
| 5 | Tab 1 — Overview & Spatial | ✅ Done | `feat: tab 1 overview` |
| 6 | Tab 2 — Climate & Seasonality | ✅ Done | `feat: tab 2 climate` |
| 7 | Tab 3 — Production Drivers | ⏳ Pending | |
| 8 | Tab 4 — Farm Economics & Calculator | ⏳ Pending | |
| 9 | Verification (tests + smoke run of every tab) | ⏳ Pending | |
| 10 | Load real source data & visual QA | 🚧 Blocked — data files not in repo | |

Legend: ✅ Done · 🔄 In progress · ⏳ Pending · 🚧 Blocked

## ⚠️ Open issues / blockers

1. **Source data is not in the folder.** Only the two spec documents exist. All files listed in the README
   (`data/raw/*.csv`, the OAE `.xlsx`, `data/thai_provinces.geojson`) must be downloaded from the owning
   agencies. Per the "Zero Mock Data" rule the app shows a clear "dataset not loaded" state instead of
   inventing numbers.
2. **Spec vs data-dictionary tab mismatch.** `data_sources.md` §10 describes 6 tabs; the spec defines 4.
   Implementation follows the **4-tab spec**; disaster data (§15) is shown inside Tab 3.
3. **Schemas for some files are not fully specified** (national rain, provincial temperature, irrigation,
   soil, cost, disaster). The loader accepts several common column names per field; if the real files
   use different headers, add them to the alias lists in `src/data_loader.py`.
4. **UI not run in the build environment.** The build machine had no internet access to install
   Streamlit/Plotly; core logic is unit-tested and the UI is smoke-tested with stubs. First real run
   should happen locally after `pip install -r requirements.txt`.

## 📝 Change log

### Step 5 — Tab 1: Overview & Spatial Analysis (2026-10-23)
- **KPI cards** (one row per selected crop): planted area, harvested area + harvest ratio, total
  production, and yield, each with YoY vs. the previous year. Values come from the scope's own
  `geo_level` row.
- **Choropleth map**: switch between production (ตัน) and yield (กก./ไร่) on a sequential blue
  scale, joined on `properties.pro_th`. Hover shows province, production, area and yield.
  **Clicking a province filters the whole dashboard.** Province view shows its region with the
  selected province outlined. Provinces missing from the GeoJSON are listed. Without the GeoJSON,
  the map falls back to a top-15 ranking bar.
- **Scale vs. Efficiency quadrant**: X = planted or harvested area (log toggle), Y = yield, with
  national-mean reference lines. Q1–Q4 are coded by both colour and marker shape; Q4 target
  provinces are listed, with a table view of all points.
- **13-year trend** for the scope (production / area / yield) with the selected year marked.
- Smoke run with synthetic scratch fixtures (not shipped): 3 charts render in all 5 filter
  scenarios, including a province with missing years.

### Step 4 — App shell & Global Controls Bar (2026-10-23)
- `src/filters.py`: `FilterState` (crops, year, level, region, province). `scope_rows()` enforces the
  **Double-Counting Prevention Rule**: country and region views read their own `geo_level` rows and
  never sum provinces. Also adds province-level selectors, national reference means for the quadrant,
  and an unweighted spatial mean for province-only climate data.
- `app.py`: top-of-page Global Controls Bar (crop multiselect, year slider, cascading
  country → region → province), cached `load_all()`, 4 tabs, and a sidebar dataset-status panel with
  row counts, GISTDA API-key status and a reload button. Map clicks can queue a province
  (`pending_province`) that the controls apply on rerun.
- `src/ui.py`: validated colour palette (fixed categorical order, sequential blue, status colours,
  ordered S1→N soil ramp), number formatting, Plotly styling, an honest "data not loaded" notice and a
  table-view expander for accessibility.
- `.streamlit/config.toml`: theme pinned to light so chart ink and palette stay validated.
- `tests/test_filters.py`: 6 tests (country/region rows are **not** province sums) → 31/31 pass.
- Smoke run with stubbed Streamlit/Plotly and no data: all 5 filter scenarios render without error.
- **Design decision:** Tab 2's "dual-axis rain + temperature" chart will be built as two stacked panels
  sharing the month axis. Two y-scales on one plot is a well-known misreading risk, and stacked panels
  show the same information.

### Step 3 — Metrics & statistics engine (2026-10-23)
- `src/metrics.py`: YoY growth, yield, harvest ratio, 2×2 quadrant classifier (national-mean
  reference lines), dry-spell check (Jun–Jul total vs. mean of all *other* complete years, flag at
  > 30 % deficit), irrigation ratio, soil mismatch (S3 + N > 30 %), price summary (max/min/mean,
  ±1σ volatility band, CV), profit margin, break-even calculator (TC_rai, TC_total, TR, net profit,
  Y_BE, P_BE), and `match_product` to link crop names across OAE sources.
- `src/stats.py`: Pearson r + p, Spearman ρ + p, OLS (β0, β1, R², SE) via SciPy, with guards for
  n < 3 and constant variables; plain-language strength labels.
- `tests/test_metrics_stats.py`: 15 tests, worked by hand from the spec formulas → **25/25 tests pass**.

### Step 2 — Data loader (2026-10-23)
- `src/data_loader.py`: one loader per dataset (11 total) that normalises headers through alias
  tables (English + Thai), coerces numbers (handles `1,000`, `-`), converts CE → BE years, and
  canonicalises province names.
- Production: honours source `geo_level` or classifies rows as country / region / province, and
  recomputes `yield_per_rai`, `harvest_ratio` and `damaged_area` with the data-dictionary formulas
  (zero harvest area → NaN, no division error).
- Farmgate: derives `price_baht_per_kg` and an approximate weekly date; soil shares are normalised
  to % per row; irrigation ratio and total cost are computed when not supplied; TMD JSON accepts
  the raw API envelope or a flat list.
- `load_all()` returns `(data, status)`. A missing or malformed file yields `None` plus a readable
  status message — never placeholder values.
- `tests/test_data_loader.py`: 10 tests, all passing.

### Step 1 — Scaffold (2026-10-23)
- Added `requirements.txt` (Streamlit, Plotly, pandas, NumPy, SciPy, openpyxl, pytest).
- Added `.gitignore` (raw data, venv, caches are not versioned).
- Added `src/config.py`: data paths (overridable with `DATAVIZZ_DATA_DIR`), the 4 OAE regions →
  77 provinces mapping (17/20/26/14), province spelling aliases, crop list, default filters,
  thresholds (dry spell 30 %, soil mismatch 30 %, rainfed < 20 %), cost categories.

### Step 0 — README (2026-10-23)
- Created `README.md` summarising purpose, global controls, 4 tabs, formulas, required datasets,
  tech stack, structure and setup.
