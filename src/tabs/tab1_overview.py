"""TAB 1 — ภาพรวมการผลิตสินค้าเกษตร (Overview & Spatial Analysis)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .. import config as cfg
from .. import filters as flt
from .. import metrics as m
from .. import ui

METRICS = {
    "production_ton": ("ผลผลิตรวม", "ตัน"),
    "yield_per_rai": ("ผลผลิตต่อไร่", "กก./ไร่"),
}
QUAD_COLORS = {"Q1": ui.SERIES[0], "Q2": ui.SERIES[2], "Q3": ui.MUTED, "Q4": ui.SERIES[1]}
QUAD_SYMBOLS = {"Q1": "circle", "Q2": "diamond", "Q3": "square", "Q4": "triangle-up"}


def render(data, status, state: flt.FilterState) -> None:
    st.markdown(f"#### ภาพรวมการผลิต · {state.scope_name} · พ.ศ. {state.year}")
    if not ui.require(status, ["production"], "ภาพรวมการผลิต"):
        return
    prod: pd.DataFrame = data["production"]

    _kpi_section(prod, state)
    st.divider()

    crop = state.primary_crop
    if len(state.crops) > 1:
        crop = st.selectbox("พืชสำหรับแผนที่และ Quadrant", state.crops, key="t1_crop")

    left, right = st.columns([1.05, 1])
    with left:
        _map_section(data, status, prod, state, crop)
    with right:
        _quadrant_section(prod, state, crop)
    st.divider()
    _trend_section(prod, state)
    ui.source_caption(status["production"].label)


# --------------------------------------------------------------------------- KPIs
def _kpi_section(prod: pd.DataFrame, state: flt.FilterState) -> None:
    rows = flt.scope_rows(prod, state, years=[state.year, state.year - 1])
    if rows.empty:
        ui.empty_notice(f"ไม่มีแถวข้อมูลระดับ “{flt.LEVEL_LABELS[state.level]}” สำหรับ "
                        f"{state.scope_name} ในปี {state.year} (ระบบไม่รวมยอดจากจังหวัดเพื่อป้องกันการนับซ้ำ)")
        return
    for crop in state.crops:
        cur = rows[(rows["product"] == crop) & (rows["year"] == state.year)]
        prev = rows[(rows["product"] == crop) & (rows["year"] == state.year - 1)]
        if cur.empty:
            ui.empty_notice(f"{crop}: ไม่มีข้อมูลปี {state.year} สำหรับ {state.scope_name}")
            continue
        c, p = cur.iloc[0], (prev.iloc[0] if not prev.empty else None)

        def yoy(col):
            v = m.yoy_growth(c[col], p[col]) if p is not None else None
            return None if v is None else f"{v:+.1f}% YoY"

        if len(state.crops) > 1:
            st.markdown(f"**{crop}**")
        k1, k2, k3, k4 = st.columns(4)
        ui.kpi(k1, "เนื้อที่เพาะปลูก", ui.fmt_num(c["area_plant_rai"], 0, "ไร่"), yoy("area_plant_rai"))
        ui.kpi(k2, "เนื้อที่เก็บเกี่ยว", ui.fmt_num(c["area_harvest_rai"], 0, "ไร่"),
               f"อัตราเก็บเกี่ยว {ui.fmt_pct(c['harvest_ratio'])}", delta_color="off",
               help="Harvest Ratio = เนื้อที่เก็บเกี่ยว ÷ เนื้อที่เพาะปลูก × 100")
        ui.kpi(k3, "ผลผลิตรวม", ui.fmt_num(c["production_ton"], 0, "ตัน"), yoy("production_ton"))
        ui.kpi(k4, "ผลผลิตต่อไร่", ui.fmt_num(c["yield_per_rai"], 0, "กก./ไร่"), yoy("yield_per_rai"),
               help="Yield = ผลผลิต (ตัน) × 1000 ÷ เนื้อที่เก็บเกี่ยว (ไร่)")


# --------------------------------------------------------------------------- Map
def _map_rows(prod, state, crop):
    if state.level == flt.LEVEL_PROVINCE and state.province:
        # Show the province within its region for context.
        ctx = flt.FilterState(crops=[crop], year=state.year, level=flt.LEVEL_REGION,
                              region=cfg.PROVINCE_TO_REGION.get(state.province))
        return flt.province_rows(prod, ctx, crop)
    return flt.province_rows(prod, state, crop)


def _map_section(data, status, prod, state, crop) -> None:
    metric = st.radio("ตัวชี้วัดบนแผนที่", list(METRICS), format_func=lambda k: METRICS[k][0],
                      horizontal=True, key="t1_map_metric")
    label, unit = METRICS[metric]
    df = _map_rows(prod, state, crop).dropna(subset=[metric])
    if df.empty:
        ui.empty_notice(f"ไม่มีข้อมูลรายจังหวัดของ {crop} ปี {state.year}")
        return

    if not status["geojson"].loaded:
        ui.require(status, ["geojson"], "แผนที่ Choropleth")
        st.caption(f"แสดงอันดับ {label} รายจังหวัดแทนแผนที่")
        top = df.nlargest(15, metric).sort_values(metric)
        fig = go.Figure(go.Bar(x=top[metric], y=top["province"], orientation="h",
                               marker=dict(color=ui.SERIES[0], cornerradius=4),
                               hovertemplate="%{y}: %{x:,.0f} " + unit + "<extra></extra>"))
        ui.plot(ui.style(fig, height=460, legend=False), key="t1_rank")
        return

    gj = data["geojson"]
    hover = df.assign(
        area_txt=df["area_plant_rai"].map(lambda v: ui.fmt_num(v, 0)),
        prod_txt=df["production_ton"].map(lambda v: ui.fmt_num(v, 0)),
        yield_txt=df["yield_per_rai"].map(lambda v: ui.fmt_num(v, 0)),
    )
    fig = go.Figure(go.Choropleth(
        geojson=gj, featureidkey="id", locations=hover["province"], z=hover[metric],
        colorscale=[[i / (len(ui.SEQUENTIAL_BLUE) - 1), c] for i, c in enumerate(ui.SEQUENTIAL_BLUE)],
        marker=dict(line=dict(color="white", width=0.6)),
        colorbar=dict(title=dict(text=unit), thickness=10, len=0.6),
        customdata=hover[["prod_txt", "area_txt", "yield_txt"]].values,
        hovertemplate=("<b>%{location}</b><br>ผลผลิตรวม %{customdata[0]} ตัน"
                       "<br>พื้นที่ปลูก %{customdata[1]} ไร่<br>ผลผลิตต่อไร่ %{customdata[2]} กก./ไร่"
                       "<extra></extra>"),
    ))
    if state.level == flt.LEVEL_PROVINCE and state.province in set(hover["province"]):
        fig.add_trace(go.Choropleth(
            geojson=gj, featureidkey="id", locations=[state.province], z=[1],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
            marker=dict(line=dict(color=ui.INK, width=2.2)), hoverinfo="skip"))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    ui.style(fig, height=560, legend=False)
    fig.update_layout(margin=dict(l=0, r=0, t=8, b=0), plot_bgcolor="rgba(0,0,0,0)")
    event = ui.plot(fig, key="t1_map", selectable=True)

    missing = sorted(set(df["province"]) - {f["id"] for f in gj["features"]})
    if missing:
        st.caption(f"⚠️ ไม่พบขอบเขตใน GeoJSON: {', '.join(missing)}")
    st.caption("คลิกจังหวัดบนแผนที่เพื่อกรองทั้งแดชบอร์ดไปยังจังหวัดนั้น")
    for pt in ui.selected_points(event):
        prov = pt.get("location") if isinstance(pt, dict) else None
        if prov and prov != state.province and prov in cfg.PROVINCE_TO_REGION:
            st.session_state["pending_province"] = prov
            st.rerun()


# --------------------------------------------------------------------------- Quadrant
def _quadrant_section(prod, state, crop) -> None:
    st.markdown("**Scale vs. Efficiency Matrix**")
    c1, c2 = st.columns([1.4, 1])
    x_col = c1.radio("แกน X (Scale)", ["area_plant_rai", "area_harvest_rai"],
                     format_func={"area_plant_rai": "เนื้อที่เพาะปลูก",
                                  "area_harvest_rai": "เนื้อที่เก็บเกี่ยว"}.get,
                     horizontal=True, key="t1_quad_x")
    log_x = c2.toggle("แกน X แบบ log", value=True, key="t1_quad_log")

    allp = flt.province_rows(prod, state, crop, restrict_to_scope=False)
    allp = allp.dropna(subset=[x_col, "yield_per_rai"])
    allp = allp[allp[x_col] > 0]
    if len(allp) < 2:
        ui.empty_notice("ข้อมูลรายจังหวัดไม่พอสำหรับ Quadrant")
        return
    # Reference lines = national averages across provinces (spec: X̄, Ȳ).
    x_ref, y_ref = float(allp[x_col].mean()), float(allp["yield_per_rai"].mean())
    allp = allp.assign(quadrant=m.classify_quadrant(allp[x_col], allp["yield_per_rai"], x_ref, y_ref))
    df = allp[allp["province"].isin(state.provinces_in_scope())] \
        if state.level == flt.LEVEL_REGION else allp

    fig = go.Figure()
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        d = df[df["quadrant"] == q]
        if d.empty:
            continue
        sel = (d["province"] == state.province).to_numpy()
        fig.add_trace(go.Scatter(
            x=d[x_col], y=d["yield_per_rai"], mode="markers", name=m.QUADRANT_LABELS[q],
            marker=dict(size=np.where(sel, 16, 10), color=QUAD_COLORS[q], symbol=QUAD_SYMBOLS[q],
                        line=dict(color=np.where(sel, ui.INK, ui.SURFACE).tolist(),
                                  width=np.where(sel, 2, 1.5))),
            customdata=np.stack([d["province"], d["production_ton"]], axis=-1),
            hovertemplate=("<b>%{customdata[0]}</b><br>พื้นที่ %{x:,.0f} ไร่<br>"
                           "ผลผลิตต่อไร่ %{y:,.0f} กก./ไร่<br>ผลผลิตรวม %{customdata[1]:,.0f} ตัน"
                           "<extra>" + q + "</extra>"),
        ))
    fig.add_vline(x=x_ref, line=dict(color=ui.AXIS, dash="dash", width=1.5))
    fig.add_hline(y=y_ref, line=dict(color=ui.AXIS, dash="dash", width=1.5))
    for q, (ax, ay, xa, ya) in {"Q1": (1, 1, "right", "top"), "Q2": (0, 1, "left", "top"),
                                "Q3": (0, 0, "left", "bottom"), "Q4": (1, 0, "right", "bottom")}.items():
        fig.add_annotation(xref="paper", yref="paper", x=ax, y=ay, text=q, showarrow=False,
                           xanchor=xa, yanchor=ya, font=dict(color=ui.MUTED, size=13))
    fig.update_xaxes(title="ไร่ (Scale)", type="log" if log_x else "linear")
    fig.update_yaxes(title="กก./ไร่ (Efficiency)")
    ui.style(fig, height=470)
    fig.update_layout(legend=dict(orientation="h", y=-0.22, yanchor="top"))
    ui.plot(fig, key="t1_quad")
    st.caption(f"เส้นอ้างอิง = ค่าเฉลี่ยรายจังหวัดทั้งประเทศ: X̄ = {ui.fmt_num(x_ref)} ไร่ · "
               f"Ȳ = {ui.fmt_num(y_ref)} กก./ไร่")

    counts = df["quadrant"].value_counts().reindex(["Q1", "Q2", "Q3", "Q4"]).fillna(0).astype(int)
    q4 = df[df["quadrant"] == "Q4"].sort_values(x_col, ascending=False)["province"].tolist()
    if q4:
        st.markdown(f"🎯 **Q4 (พื้นที่ปลูกมาก ผลผลิตต่ำ — เป้าหมายปรับปรุง):** {', '.join(q4[:10])}"
                    + (f" และอีก {len(q4) - 10} จังหวัด" if len(q4) > 10 else ""))
    ui.table_view(
        df[["province", "region", x_col, "yield_per_rai", "production_ton", "quadrant"]]
        .sort_values(["quadrant", x_col], ascending=[True, False])
        .rename(columns={"province": "จังหวัด", "region": "ภาค", x_col: "พื้นที่ (ไร่)",
                         "yield_per_rai": "กก./ไร่", "production_ton": "ตัน", "quadrant": "Quadrant"}),
        f"ดูตาราง Quadrant (Q1 {counts['Q1']} · Q2 {counts['Q2']} · Q3 {counts['Q3']} · Q4 {counts['Q4']})")


# --------------------------------------------------------------------------- Trend
TREND_METRICS = {
    "production_ton": ("ผลผลิตรวม", "ตัน"),
    "area_plant_rai": ("เนื้อที่เพาะปลูก", "ไร่"),
    "yield_per_rai": ("ผลผลิตต่อไร่", "กก./ไร่"),
}


def _trend_section(prod, state) -> None:
    st.markdown(f"**แนวโน้มย้อนหลัง 13 ปี · {state.scope_name}**")
    metric = st.radio("ตัวชี้วัด", list(TREND_METRICS), format_func=lambda k: TREND_METRICS[k][0],
                      horizontal=True, key="t1_trend_metric")
    label, unit = TREND_METRICS[metric]
    rows = flt.scope_rows(prod, state).sort_values("year")
    if rows.empty:
        ui.empty_notice("ไม่มีข้อมูลแนวโน้มสำหรับขอบเขตที่เลือก")
        return
    fig = go.Figure()
    for i, crop in enumerate(state.crops[:8]):
        d = rows[rows["product"] == crop]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["year"], y=d[metric], name=crop, mode="lines+markers",
            line=dict(color=ui.SERIES[i], width=2),
            marker=dict(size=8, line=dict(color=ui.SURFACE, width=1.5)),
            hovertemplate=crop + " · พ.ศ. %{x}: %{y:,.0f} " + unit + "<extra></extra>"))
    fig.add_vline(x=state.year, line=dict(color=ui.AXIS, width=1, dash="dot"))
    fig.update_xaxes(title="ปี พ.ศ.", dtick=1)
    fig.update_yaxes(title=unit, rangemode="tozero")
    ui.plot(ui.style(fig, height=340, legend=len(state.crops) > 1), key="t1_trend")
