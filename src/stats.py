"""Statistical engine for Tab 2/3: Pearson r, Spearman ρ, p-values, OLS + R²."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats as sps

MIN_POINTS = 3
ALPHA = 0.05


@dataclass
class CorrelationReport:
    n: int
    ok: bool
    note: str = ""
    pearson_r: Optional[float] = None
    pearson_p: Optional[float] = None
    spearman_rho: Optional[float] = None
    spearman_p: Optional[float] = None
    slope: Optional[float] = None          # β1
    intercept: Optional[float] = None      # β0
    r_squared: Optional[float] = None
    slope_stderr: Optional[float] = None

    @property
    def significant(self) -> bool:
        return self.ok and self.pearson_p is not None and self.pearson_p < ALPHA

    def as_dict(self) -> dict:
        return asdict(self)

    def predict(self, x) -> np.ndarray:
        return self.intercept + self.slope * np.asarray(x, dtype=float)


def correlation_report(x, y) -> CorrelationReport:
    """Pairwise-complete correlation + simple OLS (Y = β0 + β1·X)."""
    df = pd.DataFrame({"x": pd.to_numeric(pd.Series(x), errors="coerce").values,
                       "y": pd.to_numeric(pd.Series(y), errors="coerce").values}).dropna()
    n = len(df)
    if n < MIN_POINTS:
        return CorrelationReport(n, False, f"ต้องมีข้อมูลอย่างน้อย {MIN_POINTS} จุด (มี {n})")
    if df["x"].nunique() < 2 or df["y"].nunique() < 2:
        return CorrelationReport(n, False, "ค่าตัวแปรคงที่ — คำนวณสหสัมพันธ์ไม่ได้")
    pr = sps.pearsonr(df["x"], df["y"])
    sr = sps.spearmanr(df["x"], df["y"])
    lr = sps.linregress(df["x"], df["y"])
    return CorrelationReport(
        n=n, ok=True,
        pearson_r=float(pr[0]), pearson_p=float(pr[1]),
        spearman_rho=float(sr[0]), spearman_p=float(sr[1]),
        slope=float(lr.slope), intercept=float(lr.intercept),
        r_squared=float(lr.rvalue ** 2), slope_stderr=float(lr.stderr),
    )


def describe_strength(r: Optional[float]) -> str:
    """Plain-language label for |r| (Cohen-style thresholds)."""
    if r is None:
        return "—"
    a = abs(r)
    level = ("แทบไม่มีความสัมพันธ์" if a < 0.1 else "อ่อน" if a < 0.3 else
             "ปานกลาง" if a < 0.5 else "ค่อนข้างสูง" if a < 0.7 else "สูง")
    direction = "เชิงบวก" if r > 0 else "เชิงลบ" if r < 0 else ""
    return f"{level} {direction}".strip()
