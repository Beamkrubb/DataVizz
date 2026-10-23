"""Domain formulas from the dashboard spec (Tabs 1–4).

All functions are pure and return ``None`` (or NaN) instead of raising when an
input makes the metric undefined (e.g. division by zero, missing baseline).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from . import config as cfg


def _valid(x) -> bool:
    return x is not None and not (isinstance(x, float) and np.isnan(x))


def safe_div(a, b) -> Optional[float]:
    if not _valid(a) or not _valid(b) or b == 0:
        return None
    return float(a) / float(b)


# --------------------------------------------------------------------------- Tab 1
def yoy_growth(current, previous) -> Optional[float]:
    """YoY Growth (%) = (V_t − V_{t−1}) / V_{t−1} × 100."""
    r = safe_div(None if not _valid(current) or not _valid(previous) else current - previous,
                 previous)
    return None if r is None else r * 100


def yield_kg_per_rai(production_ton, harvest_area_rai) -> Optional[float]:
    """Yield = Production (ton) × 1000 / Harvested Area (rai)."""
    r = safe_div(production_ton, harvest_area_rai)
    return None if r is None else r * 1000


def harvest_ratio(harvest_area_rai, plant_area_rai) -> Optional[float]:
    """Harvest Ratio (%) = Harvest Area / Plant Area × 100."""
    r = safe_div(harvest_area_rai, plant_area_rai)
    return None if r is None else r * 100


QUADRANT_LABELS = {
    "Q1": "Q1 · High Scale / High Efficiency — ผู้นำการผลิต",
    "Q2": "Q2 · Low Scale / High Efficiency — ศักยภาพสูง พื้นที่จำกัด",
    "Q3": "Q3 · Low Scale / Low Efficiency — พื้นที่เล็ก/ไม่เหมาะสม",
    "Q4": "Q4 · High Scale / Low Efficiency — เป้าหมายปรับปรุงเทคโนโลยี/ย้ายพืช",
}


def classify_quadrant(x: pd.Series, y: pd.Series, x_ref: float, y_ref: float) -> pd.Series:
    """2×2 Scale-vs-Efficiency quadrant using national reference lines."""
    hi_x, hi_y = x >= x_ref, y >= y_ref
    q = np.select([hi_x & hi_y, ~hi_x & hi_y, ~hi_x & ~hi_y, hi_x & ~hi_y],
                  ["Q1", "Q2", "Q3", "Q4"], default="")
    return pd.Series(q, index=x.index).where(x.notna() & y.notna(), "")


# --------------------------------------------------------------------------- Tab 2
@dataclass
class DrySpellResult:
    year: int
    current_mm: Optional[float]
    baseline_mm: Optional[float]
    baseline_years: list[int]
    deficit_pct: Optional[float]
    risk: bool
    note: str = ""


def dry_spell_check(monthly: pd.DataFrame, year: int, rain_col: str = "rain_mm",
                    months: tuple[int, ...] = cfg.DRY_SPELL_MONTHS,
                    threshold_pct: float = cfg.DRY_SPELL_THRESHOLD_PCT) -> DrySpellResult:
    """Flag dry-spell risk when Jun–Jul rain is > threshold % below the
    historical mean of all *other* years with complete Jun–Jul records.

    ``monthly`` must have columns ``year``, ``month`` and ``rain_col`` for one
    spatial scope (already averaged across provinces if needed).
    """
    sub = monthly[monthly["month"].isin(months)]
    per_year = sub.groupby("year").agg(total=(rain_col, "sum"), n=("month", "nunique"))
    per_year = per_year[per_year["n"] == len(months)]["total"]
    if year not in per_year.index:
        return DrySpellResult(year, None, None, [], None, False,
                              "ไม่มีข้อมูลฝน มิ.ย.–ก.ค. ครบถ้วนของปีที่เลือก")
    base = per_year.drop(index=year)
    if base.empty:
        return DrySpellResult(year, float(per_year[year]), None, [], None, False,
                              "ไม่มีปีอื่นสำหรับคำนวณค่าเฉลี่ยย้อนหลัง")
    current, baseline = float(per_year[year]), float(base.mean())
    deficit = None if baseline == 0 else (baseline - current) / baseline * 100
    return DrySpellResult(year, current, baseline, [int(y) for y in base.index], deficit,
                          bool(deficit is not None and deficit > threshold_pct))


# --------------------------------------------------------------------------- Tab 3
def irrigation_ratio(irrigation_area_rai, agricultural_area_rai) -> Optional[float]:
    """Irrigation Ratio (%) = Irrigation Area / Total Agricultural Area × 100."""
    r = safe_div(irrigation_area_rai, agricultural_area_rai)
    return None if r is None else r * 100


def soil_mismatch(s3_pct, n_pct, threshold: float = cfg.SOIL_MISMATCH_THRESHOLD_PCT) -> bool:
    """True when S3 + N share exceeds the threshold (mismatched soil-crop allocation)."""
    total = (s3_pct or 0) + (n_pct or 0)
    return total > threshold


# --------------------------------------------------------------------------- Tab 4
def price_summary(prices: pd.Series) -> dict:
    p = pd.to_numeric(prices, errors="coerce").dropna()
    if p.empty:
        return {}
    mean, std = float(p.mean()), float(p.std(ddof=1)) if len(p) > 1 else 0.0
    return {
        "max": float(p.max()), "min": float(p.min()), "mean": mean, "std": std,
        "band_low": mean - std, "band_high": mean + std,
        "cv_pct": (std / mean * 100) if mean else None, "n": int(len(p)),
    }


def profit_margin(farmgate_price_kg, production_cost_kg) -> tuple[Optional[float], Optional[float]]:
    """Profit Margin (THB/kg) = Price − Cost; Margin Ratio (%) = Margin / Price × 100."""
    if not _valid(farmgate_price_kg) or not _valid(production_cost_kg):
        return None, None
    margin = float(farmgate_price_kg) - float(production_cost_kg)
    ratio = safe_div(margin, farmgate_price_kg)
    return margin, (None if ratio is None else ratio * 100)


@dataclass
class BreakEvenResult:
    tc_rai: float
    tc_total: float
    revenue: float
    net_profit: float
    profit_per_rai: Optional[float]
    break_even_yield: Optional[float]   # kg/rai
    break_even_price: Optional[float]   # THB/kg
    margin_pct: Optional[float]


def break_even(area_rai: float, yield_kg_rai: float, price_kg: float,
               variable_cost_rai: float, fixed_cost_rai: float) -> BreakEvenResult:
    """OAE-standard farm budget formulas (spec Tab 4 §3)."""
    tc_rai = variable_cost_rai + fixed_cost_rai
    tc_total = tc_rai * area_rai
    revenue = price_kg * yield_kg_rai * area_rai
    net = revenue - tc_total
    margin = safe_div(net, revenue)
    return BreakEvenResult(
        tc_rai=tc_rai, tc_total=tc_total, revenue=revenue, net_profit=net,
        profit_per_rai=safe_div(net, area_rai),
        break_even_yield=safe_div(tc_rai, price_kg),
        break_even_price=safe_div(tc_rai, yield_kg_rai),
        margin_pct=None if margin is None else margin * 100,
    )


def match_product(crop: str, candidates) -> Optional[str]:
    """Find the product name in another source that best matches a production crop."""
    cands = [str(c) for c in candidates if pd.notna(c)]
    if crop in cands:
        return crop
    for kw in cfg.CROP_KEYWORDS.get(crop, [crop]):
        hits = [c for c in cands if kw in c]
        if hits:
            return sorted(hits, key=len)[0]
    return None
