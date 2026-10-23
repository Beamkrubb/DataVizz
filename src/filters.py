"""Global filter state and the Double-Counting Prevention Rule.

The rule (spec §2.2): country / region views read the source rows whose
``geo_level`` is ``country`` / ``region`` directly. Province rows are never
summed up to rebuild a higher level.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from . import config as cfg

LEVEL_COUNTRY, LEVEL_REGION, LEVEL_PROVINCE = "country", "region", "province"
LEVEL_LABELS = {LEVEL_COUNTRY: "ทั้งประเทศ", LEVEL_REGION: "ภาค", LEVEL_PROVINCE: "จังหวัด"}


@dataclass
class FilterState:
    crops: list[str] = field(default_factory=lambda: [cfg.DEFAULT_CROP])
    year: int = cfg.DEFAULT_YEAR
    level: str = LEVEL_COUNTRY
    region: Optional[str] = None
    province: Optional[str] = None

    @property
    def primary_crop(self) -> str:
        return self.crops[0] if self.crops else cfg.DEFAULT_CROP

    @property
    def scope_name(self) -> str:
        if self.level == LEVEL_PROVINCE and self.province:
            return self.province
        if self.level == LEVEL_REGION and self.region:
            return self.region
        return cfg.COUNTRY_LABEL

    @property
    def scope_region(self) -> Optional[str]:
        if self.level == LEVEL_PROVINCE and self.province:
            return cfg.PROVINCE_TO_REGION.get(self.province)
        if self.level == LEVEL_REGION:
            return self.region
        return None

    def provinces_in_scope(self) -> list[str]:
        if self.level == LEVEL_PROVINCE and self.province:
            return [self.province]
        if self.level == LEVEL_REGION and self.region:
            return list(cfg.REGIONS.get(self.region, []))
        return list(cfg.ALL_PROVINCES)


def available_crops(prod: Optional[pd.DataFrame]) -> list[str]:
    """Main crops first (spec order), then any other products in the data."""
    if prod is None or prod.empty:
        return list(cfg.MAIN_CROPS)
    found = set(prod["product"].dropna().unique())
    main = [c for c in cfg.MAIN_CROPS if c in found]
    return main + sorted(found - set(main))


def available_years(prod: Optional[pd.DataFrame]) -> list[int]:
    if prod is None or prod.empty:
        return list(cfg.PRODUCTION_YEARS)
    return sorted(int(y) for y in prod["year"].dropna().unique())


def scope_rows(prod: pd.DataFrame, state: FilterState, crops: Optional[list[str]] = None,
               years: Optional[list[int]] = None) -> pd.DataFrame:
    """Rows for the selected spatial scope at its *own* geo_level (no re-summing)."""
    crops = crops if crops is not None else state.crops
    df = prod[prod["product"].isin(crops)]
    if years is not None:
        df = df[df["year"].isin(years)]
    if state.level == LEVEL_PROVINCE and state.province:
        return df[(df["geo_level"] == LEVEL_PROVINCE) & (df["province"] == state.province)]
    if state.level == LEVEL_REGION and state.region:
        return df[(df["geo_level"] == LEVEL_REGION) & (df["province"] == state.region)]
    return df[df["geo_level"] == LEVEL_COUNTRY]


def province_rows(prod: pd.DataFrame, state: FilterState, crop: Optional[str] = None,
                  year: Optional[int] = None, restrict_to_scope: bool = True) -> pd.DataFrame:
    """Province-level rows (for maps / scatter plots) of one crop and year."""
    crop = crop or state.primary_crop
    year = year if year is not None else state.year
    df = prod[(prod["geo_level"] == LEVEL_PROVINCE) & (prod["product"] == crop)
              & (prod["year"] == year)]
    if restrict_to_scope:
        df = df[df["province"].isin(state.provinces_in_scope())]
    return df


def national_reference(prod: pd.DataFrame, crop: str, year: int) -> dict:
    """National averages for the quadrant reference lines.

    X̄ / Ȳ are the mean planted area and mean yield across provinces (the
    spec's "national average"); the official country-level yield is returned
    too for display.
    """
    prov = prod[(prod["geo_level"] == LEVEL_PROVINCE) & (prod["product"] == crop)
                & (prod["year"] == year)]
    country = prod[(prod["geo_level"] == LEVEL_COUNTRY) & (prod["product"] == crop)
                   & (prod["year"] == year)]
    return {
        "x_mean": float(prov["area_plant_rai"].mean()) if not prov.empty else None,
        "y_mean": float(prov["yield_per_rai"].mean()) if not prov.empty else None,
        "country_yield": (float(country["yield_per_rai"].iloc[0])
                          if not country.empty and pd.notna(country["yield_per_rai"].iloc[0])
                          else None),
    }


def scope_province_mean(df: pd.DataFrame, state: FilterState, value_cols: list[str],
                        by: list[str]) -> pd.DataFrame:
    """Average a province-level table (rain, temperature …) over the provinces
    in scope. Used for climate data, which exists only at province level; this
    is an unweighted spatial mean, not a re-sum of production totals."""
    sub = df[df["province"].isin(state.provinces_in_scope())]
    if sub.empty:
        return sub
    return sub.groupby(by, as_index=False)[value_cols].mean()
