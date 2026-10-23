"""TAB 2 — สภาพอากาศและสถานการณ์เพาะปลูก (Climate & Seasonality)."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from .. import config as cfg
from .. import filters as flt
from .. import metrics as m
from .. import stats as sx
from .. import ui

GUARDRAIL = ("⚠️ **Academic Guardrail:** *“Correlation is NOT Causation”* — ค่าสหสัมพันธ์ทางสถิติแสดงเพียง"
             "ความสัมพันธ์เชิงตัวเลขระหว่างสภาพอากาศและผลผลิต ไม่ได้หมายความว่าปริมาณฝนเป็นปัจจัยเดียวที่"
             "กำหนดผลผลิต โปรดพิจารณาปัจจัยเชิงโครงสร้างอื่นๆ ใน Tab 3 ร่วมด้วย")


def render(data, status, state: flt.FilterState) -> None:
    st.markdown(f"#### สภาพอากาศและฤดูกาล · {state.scope_name}")
    _seasonality_section(data, status, state)
    st.divider()
    _correlation_section(data, status, state)
    st.warning(GUARDRAIL)
    st.divider()
    _tmd_section(data, status, state)


# --------------------------------------------------------------------------- helpers
def _scope_monthly_rain(data, status, state) -> tuple[Optional[pd.DataFrame], str]:
    """Monthly rain series (year, month, rain_mm) for the selected scope.

    Country scope prefers the official HII national series (long history);
    regions/provinces use the unweighted mean of province IDW rainfall.
    """
    if state.level == flt.LEVEL_COUNTRY and status["national_rain"].loaded:
        return data["national_rain"][["year", "month", "rain_mm"]], status["national_rain"].label
    if status["spatial_rain"].loaded:
        df = flt.scope_province_mean(data["spatial_rain"], state, ["avg_rain_mm"], ["year", "month"])
        if df.empty:
            return None, ""
        return df.rename(columns={"avg_rain_mm": "rain_mm"}), status["spatial_rain"].label
    return None, ""


def _pick_year(available: list[int], wanted: int, key: str, label: str) -> Optional[int]:
    if not available:
        return None
    if wanted in available:
        return wanted
    default = max([y for y in available if y <= wanted] or [min(available)])
    st.caption(f"ℹ️ ข้อมูล{label}ไม่มีปี {wanted} — เลือกปีที่มีข้อมูลด้านล่าง")
    return st.selectbox(f"ปีข้อมูล{label}", available, index=available.index(default), key=key)


# --------------------------------------------------------------------------- Seasonality
def _seasonality_section(data, status, state) -> None:
    st.markdown("**Seasonality Breakdown & Dry Spell Analysis**")
    if not status["spatial_rain"].loaded and not status["national_rain"].loaded:
        ui.require(status, ["spatial_rain", "national_rain"], "กราฟฤดูกาลฝน")
        return
    rain, rain_src = _scope_monthly_rain(data, status, state)
    if rain is None or rain.empty:
        ui.empty_notice("ไม่มีข้อมูลฝนสำหรับขอบเขตที่เลือก")
        return
    years = sorted(int(y) for y in rain["year"].dropna().unique())
    year = _pick_year(years, state.year, "t2_rain_year", "ฝน")
    cur = rain[rain["year"] == year].set_index("month")["rain_mm"].reindex(range(1, 13))
    base = rain[rain["year"] != year].groupby("month")["rain_mm"].mean().reindex(range(1, 13))

    temp = None
    if status["provincial_temp"].loaded:
        t = flt.scope_province_mean(data["provincial_temp"], state, ["tmax_c", "tmin_c"],
                                    ["year", "month"])
        if not t.empty and year in set(t["year"]):
            temp = t[t["year"] == year].set_index("month").reindex(range(1, 13))

    # Dry-spell banner
    ds = m.dry_spell_check(rain, year)
    if ds.risk:
        st.error(f"🚨 **สภาวะเสี่ยงฝนทิ้งช่วง (Dry Spell Risk Detected)** — ฝนสะสม มิ.ย.–ก.ค. {year} = "
                 f"{ui.fmt_num(ds.current_mm, 0, 'มม.')} ต่ำกว่าค่าเฉลี่ยย้อนหลัง "
                 f"({ui.fmt_num(ds.baseline_mm, 0, 'มม.')}) {ui.fmt_pct(ds.deficit_pct)}")
    elif ds.deficit_pct is not None:
        st.success(f"✅ ไม่พบสภาวะฝนทิ้งช่วง — ฝนสะสม มิ.ย.–ก.ค. {year} = {ui.fmt_num(ds.current_mm, 0, 'มม.')} "
                   f"เทียบค่าเฉลี่ย {ui.fmt_num(ds.baseline_mm, 0, 'มม.')} "
                   f"({'ต่ำกว่า' if ds.deficit_pct > 0 else 'สูงกว่า'} {ui.fmt_pct(abs(ds.deficit_pct))}; "
                   f"เกณฑ์เตือน > {cfg.DRY_SPELL_THRESHOLD_PCT:.0f}%)")
    else:
        ui.empty_notice(f"ประเมินฝนทิ้งช่วงไม่ได้: {ds.note}")

    rows = 2 if temp is not None else 1
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.62, 0.38] if rows == 2 else [1.0],
                        subplot_titles=("ปริมาณฝนรายเดือน (มม.)",) +
                                       (("อุณหภูมิเฉลี่ย (°C)",) if rows == 2 else ()))
    x = cfg.THAI_MONTHS
    fig.add_vrect(x0=x[4], x1=x[9], fillcolor=ui.HIGHLIGHT_WASH, line_width=0, row=1, col=1,
                  annotation_text="ฤดูฝนหลัก พ.ค.–ต.ค.", annotation_position="top left",
                  annotation_font=dict(color=ui.MUTED, size=11))
    fig.add_trace(go.Bar(x=x, y=cur.values, name=f"ฝน พ.ศ. {year}",
                         marker=dict(color=ui.SERIES[0], cornerradius=4),
                         hovertemplate="%{x}: %{y:,.1f} มม.<extra>" + str(year) + "</extra>"), row=1, col=1)
    if base.notna().any():
        fig.add_trace(go.Scatter(x=x, y=base.values, name="ค่าเฉลี่ยปีอื่น", mode="lines+markers",
                                 line=dict(color=ui.INK_2, width=2, dash="dash"), marker=dict(size=8),
                                 hovertemplate="%{x}: เฉลี่ย %{y:,.1f} มม.<extra></extra>"), row=1, col=1)
    if temp is not None:
        for col, name, color in [("tmax_c", "Tmax", ui.SERIES[1]), ("tmin_c", "Tmin", ui.SERIES[2])]:
            fig.add_trace(go.Scatter(x=x, y=temp[col].values, name=name, mode="lines+markers",
                                     line=dict(color=color, width=2),
                                     marker=dict(size=8, line=dict(color=ui.SURFACE, width=1.5)),
                                     hovertemplate="%{x}: %{y:.1f} °C<extra>" + name + "</extra>"),
                          row=2, col=1)
    fig.update_yaxes(title_text="มม.", row=1, col=1, rangemode="tozero")
    if temp is not None:
        fig.update_yaxes(title_text="°C", row=2, col=1)
    ui.style(fig, height=560 if rows == 2 else 380)
    fig.update_annotations(font=dict(color=ui.INK_2, size=13))
    ui.plot(fig, key="t2_season")
    if temp is None:
        ui.empty_notice("ไม่มีข้อมูลอุณหภูมิของปี/ขอบเขตนี้" if status["provincial_temp"].loaded
                        else f"ไม่มีข้อมูลอุณหภูมิ — {status['provincial_temp'].message}")
    baseline_txt = (f"{min(ds.baseline_years)}–{max(ds.baseline_years)}" if ds.baseline_years else "—")
    ui.source_caption(rain_src, status["provincial_temp"].label if temp is not None else "")
    st.caption(f"ค่าเฉลี่ยย้อนหลังคำนวณจากปี {baseline_txt} (ไม่รวมปีที่เลือก)"
               + ("" if state.level == flt.LEVEL_COUNTRY else
                  " · ค่าระดับภาค/จังหวัด = ค่าเฉลี่ยเชิงพื้นที่ของจังหวัดในขอบเขต"))


# --------------------------------------------------------------------------- Correlation
X_OPTIONS = {
    "rain_annual": ("ฝนสะสมทั้งปี", "มม."),
    "rain_season": ("ฝนสะสมฤดูฝน พ.ค.–ต.ค.", "มม."),
    "rain_junjul": ("ฝนสะสม มิ.ย.–ก.ค.", "มม."),
    "tmax_mean": ("อุณหภูมิสูงสุดเฉลี่ย", "°C"),
    "tmin_mean": ("อุณหภูมิต่ำสุดเฉลี่ย", "°C"),
}


def _province_climate(data, status) -> Optional[pd.DataFrame]:
    """Province × year climate features."""
    parts = []
    if status["spatial_rain"].loaded:
        r = data["spatial_rain"]
        full = r.groupby(["province", "year"])["month"].nunique().rename("n_months")
        agg = pd.concat([
            r.groupby(["province", "year"])["avg_rain_mm"].sum().rename("rain_annual"),
            r[r["month"].isin(cfg.RAINY_SEASON_MONTHS)].groupby(["province", "year"])["avg_rain_mm"]
             .sum().rename("rain_season"),
            r[r["month"].isin(cfg.DRY_SPELL_MONTHS)].groupby(["province", "year"])["avg_rain_mm"]
             .sum().rename("rain_junjul"),
            full], axis=1)
        agg.loc[agg["n_months"] < 12, "rain_annual"] = np.nan   # incomplete year
        parts.append(agg.drop(columns="n_months"))
    if status["provincial_temp"].loaded:
        t = data["provincial_temp"]
        parts.append(t.groupby(["province", "year"])[["tmax_c", "tmin_c"]].mean()
                     .rename(columns={"tmax_c": "tmax_mean", "tmin_c": "tmin_mean"}))
    if not parts:
        return None
    return pd.concat(parts, axis=1).reset_index()


def _correlation_section(data, status, state) -> None:
    st.markdown("**Statistical Rigor — ความสัมพันธ์สภาพอากาศกับผลผลิตต่อไร่**")
    if not ui.require(status, ["production"], "การวิเคราะห์สหสัมพันธ์"):
        return
    prod = data["production"]
    crop = state.primary_crop
    if len(state.crops) > 1:
        crop = st.selectbox("พืชสำหรับการวิเคราะห์", state.crops, key="t2_crop")

    modes = {"province": "รายจังหวัด (Province × Year)", "national": "ระดับประเทศรายปี 2550–2562"}
    mode = st.radio("หน่วยการวิเคราะห์", list(modes), format_func=modes.get, horizontal=True,
                    key="t2_mode")
    if mode == "national":
        _national_regression(data, status, prod, crop)
        return

    clim = _province_climate(data, status)
    if clim is None:
        ui.require(status, ["spatial_rain", "provincial_temp"], "การวิเคราะห์รายจังหวัด")
        return
    xs = [k for k in X_OPTIONS if k in clim.columns]
    c1, c2 = st.columns([1.3, 1])
    x_key = c1.selectbox("ตัวแปร X", xs, format_func=lambda k: X_OPTIONS[k][0], key="t2_x")
    clim_years = sorted(int(y) for y in clim["year"].dropna().unique())
    overlap = [y for y in clim_years if y in set(prod["year"].dropna().astype(int))]
    if not overlap:
        ui.empty_notice("ปีของข้อมูลสภาพอากาศและสถิติการผลิตไม่ทับซ้อนกัน")
        return
    pool_opts = ["selected", "pooled"]
    pool = c2.radio("ช่วงปี", pool_opts, horizontal=True, key="t2_pool",
                    index=1 if state.level == flt.LEVEL_PROVINCE else 0,
                    format_func={"selected": "เฉพาะปีที่เลือก",
                                 "pooled": f"รวมทุกปีที่มีข้อมูล ({overlap[0]}–{overlap[-1]})"}.get)
    years = overlap if pool == "pooled" else [_pick_year(overlap, state.year, "t2_corr_year", "สภาพอากาศ")]

    y_df = prod[(prod["geo_level"] == flt.LEVEL_PROVINCE) & (prod["product"] == crop)
                & (prod["year"].isin(years))][["province", "region", "year", "yield_per_rai"]]
    if state.level != flt.LEVEL_COUNTRY:
        y_df = y_df[y_df["province"].isin(state.provinces_in_scope())]
    df = y_df.merge(clim, on=["province", "year"], how="inner").dropna(subset=[x_key, "yield_per_rai"])
    x_label, x_unit = X_OPTIONS[x_key]
    _scatter_with_stats(df, x_key, x_label, x_unit, crop, hover_col="province",
                        key="t2_scatter", color_by_year=len(years) > 1)
    st.caption("หมายเหตุ: `year` ของสถิติการผลิตคือปีที่รายงานผลผลิต ซึ่งอาจไม่ตรงกับฤดูฝนของปีปฏิทินเดียวกันทุกพืช")


def _national_regression(data, status, prod, crop) -> None:
    if not ui.require(status, ["national_rain"], "การวิเคราะห์ระดับประเทศ"):
        return
    r = data["national_rain"]
    n_months = r.groupby("year")["month"].nunique()
    full_years = n_months[n_months == 12].index
    opts = {"rain_annual": ("ฝนสะสมทั้งปี (ประเทศ)", "มม."),
            "rain_season": ("ฝนสะสม พ.ค.–ต.ค. (ประเทศ)", "มม."),
            "rain_junjul": ("ฝนสะสม มิ.ย.–ก.ค. (ประเทศ)", "มม.")}
    x_key = st.selectbox("ตัวแปร X", list(opts), format_func=lambda k: opts[k][0], key="t2_nat_x")
    months = {"rain_annual": range(1, 13), "rain_season": cfg.RAINY_SEASON_MONTHS,
              "rain_junjul": cfg.DRY_SPELL_MONTHS}[x_key]
    x = (r[r["year"].isin(full_years) & r["month"].isin(months)].groupby("year")["rain_mm"].sum()
         .rename(x_key).reset_index())
    y = prod[(prod["geo_level"] == flt.LEVEL_COUNTRY) & (prod["product"] == crop)][["year", "yield_per_rai"]]
    df = y.merge(x, on="year").dropna()
    df["label"] = df["year"].astype(str)
    _scatter_with_stats(df, x_key, *opts[x_key], crop, hover_col="label", key="t2_nat_scatter")


def _scatter_with_stats(df, x_key, x_label, x_unit, crop, hover_col, key, color_by_year=False) -> None:
    rep = sx.correlation_report(df[x_key], df["yield_per_rai"]) if not df.empty \
        else sx.CorrelationReport(0, False, "ไม่มีข้อมูลที่จับคู่ได้")
    left, right = st.columns([2.2, 1])
    with left:
        fig = go.Figure()
        groups = [(str(y), g) for y, g in df.groupby("year")] if color_by_year else [("", df)]
        for i, (name, g) in enumerate(groups[:3]):
            fig.add_trace(go.Scatter(
                x=g[x_key], y=g["yield_per_rai"], mode="markers", name=f"พ.ศ. {name}" if name else crop,
                marker=dict(size=10, color=ui.SERIES[i], line=dict(color=ui.SURFACE, width=1.5)),
                text=g[hover_col],
                hovertemplate="<b>%{text}</b><br>" + x_label + " %{x:,.1f} " + x_unit +
                              "<br>ผลผลิตต่อไร่ %{y:,.0f} กก./ไร่<extra></extra>"))
        if rep.ok:
            xx = np.linspace(df[x_key].min(), df[x_key].max(), 50)
            fig.add_trace(go.Scatter(x=xx, y=rep.predict(xx), mode="lines", name="OLS fit",
                                     line=dict(color=ui.INK, width=2), hoverinfo="skip"))
        fig.update_xaxes(title=f"{x_label} ({x_unit})")
        fig.update_yaxes(title="ผลผลิตต่อไร่ (กก./ไร่)")
        ui.plot(ui.style(fig, height=430, legend=len(groups) > 1 or rep.ok), key=key)
    with right:
        st.markdown("**Statistical Metrics**")
        if not rep.ok:
            st.info(rep.note)
            return
        st.metric("Pearson r", f"{rep.pearson_r:.3f}", help="ความสัมพันธ์เชิงเส้น")
        st.caption(f"p = {rep.pearson_p:.4f} · {sx.describe_strength(rep.pearson_r)}")
        st.metric("Spearman ρ", f"{rep.spearman_rho:.3f}", help="ความสัมพันธ์เชิงอันดับ (non-linear, monotonic)")
        st.caption(f"p = {rep.spearman_p:.4f}")
        st.metric("R² (OLS)", f"{rep.r_squared:.3f}")
        st.latex(rf"\hat{{Y}} = {rep.intercept:,.1f} {'+' if rep.slope >= 0 else '-'} {abs(rep.slope):.4f}X")
        if rep.significant:
            st.success(f"มีนัยสำคัญทางสถิติ (p < {sx.ALPHA}) · n = {rep.n}")
        else:
            st.warning(f"ไม่มีนัยสำคัญทางสถิติ (p ≥ {sx.ALPHA}) · n = {rep.n}")
    ui.table_view(df.drop(columns=[c for c in ("label",) if c in df.columns]))


# --------------------------------------------------------------------------- TMD
def _tmd_section(data, status, state) -> None:
    with st.expander("🌡️ สถานีตรวจวัดอากาศเพื่อการเกษตร (กรมอุตุนิยมวิทยา) — ข้อมูลล่าสุดใน cache"):
        if not ui.require(status, ["tmd_agromet"], "ข้อมูลสถานี TMD"):
            return
        df = data["tmd_agromet"]
        if state.level != flt.LEVEL_COUNTRY:
            df = df[df["province"].isin(state.provinces_in_scope())]
        if df.empty:
            ui.empty_notice("ไม่มีสถานีในขอบเขตที่เลือก")
            return
        cols = [c for c in ["station_name", "province", "datetime", "temp_c", "max_temp_c",
                            "min_temp_c", "relative_humidity_pct", "rainfall_mm"] if c in df.columns]
        st.dataframe(df[cols].rename(columns={
            "station_name": "สถานี", "province": "จังหวัด", "datetime": "เวลาตรวจวัด",
            "temp_c": "อุณหภูมิ °C", "max_temp_c": "สูงสุด °C", "min_temp_c": "ต่ำสุด °C",
            "relative_humidity_pct": "ความชื้น %", "rainfall_mm": "ฝน 24 ชม. (มม.)"}), hide_index=True)
        ui.source_caption(status["tmd_agromet"].label + " (fallback cache)")
