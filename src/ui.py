"""Shared UI helpers: palette, number formatting, Plotly styling, notices."""
from __future__ import annotations

from typing import Any, Iterable, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .data_loader import DatasetStatus

# ---------------------------------------------------------------------------
# Palette (validated reference palette, light mode — app theme is pinned light
# in .streamlit/config.toml). Categorical slots are used in fixed order.
# ---------------------------------------------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
GOOD, WARNING, SERIOUS, CRITICAL = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
HIGHLIGHT_WASH = "rgba(42,120,214,0.08)"
# Ordered suitability: blue arm = suitable (S1 dark, S2 light), red arm = unsuitable
SOIL_COLORS = {"S1": "#184f95", "S2": "#86b6ef", "S3": "#f0a3a2", "N": "#b8302f"}
FONT = 'system-ui, -apple-system, "Segoe UI", "Noto Sans Thai", Tahoma, sans-serif'


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def _ok(v: Any) -> bool:
    return v is not None and not (isinstance(v, float) and pd.isna(v))


def fmt_num(v: Any, digits: int = 0, unit: str = "") -> str:
    if not _ok(v):
        return "—"
    s = f"{float(v):,.{digits}f}"
    return f"{s} {unit}".strip()


def fmt_pct(v: Any, digits: int = 1, signed: bool = False) -> str:
    if not _ok(v):
        return "—"
    return f"{float(v):{'+' if signed else ''},.{digits}f}%"


# ---------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------
def style(fig: go.Figure, height: int = 420, legend: bool = True,
          title: Optional[str] = None) -> go.Figure:
    fig.update_layout(
        height=height, title=dict(text=title, font=dict(size=15, color=INK)) if title else None,
        font=dict(family=FONT, size=13, color=INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=SURFACE,
        margin=dict(l=8, r=8, t=48 if title else 16, b=8),
        hoverlabel=dict(bgcolor="white", bordercolor=AXIS, font=dict(family=FONT, color=INK)),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(color=INK_2)),
        colorway=SERIES,
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=MUTED),
                     title_font=dict(color=INK_2))
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=MUTED),
                     title_font=dict(color=INK_2))
    return fig


def plot(fig: go.Figure, key: Optional[str] = None, selectable: bool = False):
    """Render a figure full-width; returns the selection event when selectable."""
    kwargs: dict[str, Any] = dict(theme=None, key=key,
                                  config={"displaylogo": False, "locale": "th"})
    if selectable:
        kwargs.update(on_select="rerun", selection_mode=("points",))
    try:
        return st.plotly_chart(fig, width="stretch", **kwargs)
    except Exception:  # older Streamlit without width="stretch"
        return st.plotly_chart(fig, use_container_width=True, **kwargs)


def selected_points(event) -> list[dict]:
    try:
        return list(event["selection"]["points"])
    except Exception:
        try:
            return list(event.selection.points)
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Notices & blocks
# ---------------------------------------------------------------------------
def require(status: dict[str, DatasetStatus], keys: Iterable[str], what: str = "") -> bool:
    """Show an honest 'data not loaded' notice; return True only if all loaded."""
    missing = [status[k] for k in keys if not status[k].loaded]
    if not missing:
        return True
    lines = "\n".join(f"- **{s.label}** — {s.message}" for s in missing)
    st.info(f"ไม่สามารถแสดง{what or 'ส่วนนี้'}ได้ เนื่องจากยังไม่มีชุดข้อมูลต้นทาง "
            f"(ระบบไม่ใช้ข้อมูลจำลอง):\n{lines}", icon="🗂️")
    return False


def empty_notice(msg: str) -> None:
    st.caption(f"— {msg}")


def table_view(df: pd.DataFrame, label: str = "ดูข้อมูลเป็นตาราง") -> None:
    with st.expander(label):
        st.dataframe(df, hide_index=True)


def source_caption(*labels: str) -> None:
    st.caption("แหล่งข้อมูล: " + " · ".join(labels))


def kpi(col, label: str, value: str, delta: Optional[str] = None, help: Optional[str] = None,
        delta_color: str = "normal") -> None:
    col.metric(label, value, delta=delta, help=help, delta_color=delta_color, border=True) \
        if _metric_supports_border() else col.metric(label, value, delta=delta, help=help,
                                                     delta_color=delta_color)


_BORDER: Optional[bool] = None


def _metric_supports_border() -> bool:
    global _BORDER
    if _BORDER is None:
        import inspect
        _BORDER = "border" in inspect.signature(st.metric).parameters
    return _BORDER
