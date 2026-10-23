"""Thai Agriculture & Climate Intelligence Dashboard — Streamlit entry point.

Run:  streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Thai Agri & Climate Intelligence", page_icon="🌾",
                   layout="wide", initial_sidebar_state="collapsed")

from src import config as cfg  # noqa: E402
from src import data_loader as dl  # noqa: E402
from src import filters as flt  # noqa: E402
from src import ui  # noqa: E402
from src.tabs import tab1_overview, tab2_climate, tab3_drivers, tab4_economics  # noqa: E402


@st.cache_data(show_spinner="กำลังโหลดชุดข้อมูล…")
def load_data():
    return dl.load_all()


ALL_REGIONS = "ทุกภาค"


def _apply_pending_province() -> None:
    """A map click in Tab 1 queues a province; apply it before widgets render."""
    prov = st.session_state.pop("pending_province", None)
    if prov and prov in cfg.PROVINCE_TO_REGION:
        st.session_state["f_level"] = flt.LEVEL_PROVINCE
        st.session_state["f_region_p"] = cfg.PROVINCE_TO_REGION[prov]
        st.session_state["f_province"] = prov


def render_controls(prod: pd.DataFrame | None) -> flt.FilterState:
    """Global Controls Bar (spec §2) — shared by every tab."""
    _apply_pending_province()
    crops = flt.available_crops(prod)
    years = flt.available_years(prod)

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2.2, 2.2, 1.2, 2.4])
        sel_crops = c1.multiselect(
            "ชนิดพืช", crops, default=[cfg.DEFAULT_CROP] if cfg.DEFAULT_CROP in crops else crops[:1],
            key="f_crops", help="เลือกได้หลายชนิด — กราฟที่ต้องใช้พืชชนิดเดียวจะใช้ชนิดแรกที่เลือก")
        default_year = cfg.DEFAULT_YEAR if cfg.DEFAULT_YEAR in years else years[-1]
        year = c2.select_slider("ปี พ.ศ.", options=years, value=default_year, key="f_year",
                                help="สถิติการผลิต 2550–2562 · สภาพอากาศและราคา 2561–2562")
        level = c3.selectbox("ระดับพื้นที่", list(flt.LEVEL_LABELS),
                             format_func=flt.LEVEL_LABELS.get, key="f_level")
        region = province = None
        with c4:
            if level == flt.LEVEL_REGION:
                region = st.selectbox("ภาค", list(cfg.REGIONS), key="f_region")
            elif level == flt.LEVEL_PROVINCE:
                r1, r2 = st.columns(2)
                reg = r1.selectbox("ภาค", [ALL_REGIONS] + list(cfg.REGIONS), key="f_region_p")
                plist = cfg.ALL_PROVINCES if reg == ALL_REGIONS else sorted(cfg.REGIONS[reg])
                if st.session_state.get("f_province") not in plist:
                    st.session_state.pop("f_province", None)
                province = r2.selectbox("จังหวัด", plist, key="f_province")
            else:
                st.selectbox("ขอบเขต", [cfg.COUNTRY_LABEL], disabled=True, key="f_country")

    if not sel_crops:
        st.warning("ยังไม่ได้เลือกชนิดพืช — ใช้ค่าเริ่มต้น " + cfg.DEFAULT_CROP)
        sel_crops = [cfg.DEFAULT_CROP]
    return flt.FilterState(crops=sel_crops, year=int(year), level=level,
                           region=region, province=province)


def render_status_sidebar(status: dict[str, dl.DatasetStatus]) -> None:
    with st.sidebar:
        st.subheader("สถานะชุดข้อมูล")
        loaded = sum(s.loaded for s in status.values())
        st.caption(f"พร้อมใช้งาน {loaded} / {len(status)} ชุด · ระบบไม่ใช้ข้อมูลจำลอง")
        for s in status.values():
            icon = "✅" if s.loaded else "⚪"
            extra = f" · {s.rows:,} แถว" if s.loaded else ""
            st.markdown(f"{icon} **{s.label}**{extra}  \n<small>{s.message}</small>",
                        unsafe_allow_html=True)
        st.divider()
        gistda = "ตั้งค่า API Key แล้ว" if cfg.GISTDA_API_KEY else "ยังไม่ได้ตั้งค่า GISTDA_API_KEY (HTTP 403)"
        st.caption(f"GISTDA agriculture-07: {gistda}")
        if st.button("โหลดข้อมูลใหม่", width="stretch" if _btn_stretch() else "content"):
            st.cache_data.clear()
            st.rerun()


def _btn_stretch() -> bool:
    import inspect
    p = inspect.signature(st.button).parameters.get("width")
    return p is not None


def main() -> None:
    data, status = load_data()

    st.markdown("### 🌾 Thai Agriculture & Climate Intelligence Dashboard")
    st.caption("ข้อมูลเปิดภาครัฐ: สศก. · กรมอุตุนิยมวิทยา · สสน. · GISTDA · กรมชลประทาน · "
               "กรมพัฒนาที่ดิน · ปภ.  —  ดูสถานะชุดข้อมูลได้ที่แถบด้านข้าง (›)")

    state = render_controls(data["production"])
    render_status_sidebar(status)

    if not any(s.loaded for s in status.values()):
        st.warning("ยังไม่พบไฟล์ข้อมูลต้นทางเลย — ดาวน์โหลดจากหน่วยงานเจ้าของข้อมูลแล้ววางไว้ในโฟลเดอร์ "
                   "`data/` และ `data/raw/` ตามรายการใน README.md", icon="⚠️")

    t1, t2, t3, t4 = st.tabs(["① ภาพรวมการผลิต", "② สภาพอากาศและฤดูกาล",
                              "③ ปัจจัยการผลิต", "④ ราคา ต้นทุน และความคุ้มค่า"])
    with t1:
        tab1_overview.render(data, status, state)
    with t2:
        tab2_climate.render(data, status, state)
    with t3:
        tab3_drivers.render(data, status, state)
    with t4:
        tab4_economics.render(data, status, state)


main()
