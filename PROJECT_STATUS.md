# 📈 Project Status — Thai Agriculture & Climate Intelligence Dashboard

_Last updated: 2026-10-23_

## Summary

| # | Phase | Status | Commit |
|---|---|---|---|
| 0 | Project README (from spec + data dictionary) | ✅ Done | `docs: add project README` |
| 1 | Scaffold: requirements, `.gitignore`, `src/config.py`, status file | ✅ Done | `chore: scaffold project` |
| 2 | Data loader + dataset status registry | ⏳ Pending | |
| 3 | Metrics & statistics engine + unit tests | ⏳ Pending | |
| 4 | App shell + Global Controls Bar (double-counting rule) | ⏳ Pending | |
| 5 | Tab 1 — Overview & Spatial | ⏳ Pending | |
| 6 | Tab 2 — Climate & Seasonality | ⏳ Pending | |
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

### Step 1 — Scaffold (2026-10-23)
- Added `requirements.txt` (Streamlit, Plotly, pandas, NumPy, SciPy, openpyxl, pytest).
- Added `.gitignore` (raw data, venv, caches are not versioned).
- Added `src/config.py`: data paths (overridable with `DATAVIZZ_DATA_DIR`), the 4 OAE regions →
  77 provinces mapping (17/20/26/14), province spelling aliases, crop list, default filters,
  thresholds (dry spell 30 %, soil mismatch 30 %, rainfed < 20 %), cost categories.

### Step 0 — README (2026-10-23)
- Created `README.md` summarising purpose, global controls, 4 tabs, formulas, required datasets,
  tech stack, structure and setup.
