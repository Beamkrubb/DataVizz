"""Load, validate and normalise every source dataset.

Design rules (from data_sources.md):
* Zero mock data — a missing / malformed file yields ``None`` plus a status
  message; nothing is ever synthesised.
* Every frame is normalised to the canonical column names documented in the
  data dictionary, so the rest of the app never deals with header variants.
* Years are always Buddhist Era (พ.ศ.); CE inputs (e.g. HII ``YEAR``) get +543.

This module has no Streamlit dependency so it can be unit-tested directly;
``app.py`` wraps :func:`load_all` in ``st.cache_data``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from . import config as cfg


# ---------------------------------------------------------------------------
# Status registry
# ---------------------------------------------------------------------------
@dataclass
class DatasetStatus:
    key: str
    label: str
    path: str | None
    loaded: bool
    rows: int = 0
    message: str = ""


class DataValidationError(ValueError):
    """Raised when a file exists but does not match the expected schema."""


# ---------------------------------------------------------------------------
# Column aliases: canonical name -> accepted headers (case/space-insensitive)
# Extend these lists if a real source file uses a different header.
# ---------------------------------------------------------------------------
PRODUCTION_ALIASES = {
    "crop_year": ["crop_year", "ปีเพาะปลูก"],
    "year": ["year", "ปี", "ปี พ.ศ.", "ปีพ.ศ.", "ปีเก็บเกี่ยว"],
    "product": ["product", "สินค้า", "ชนิดสินค้า", "พืช", "crop"],
    "province": ["province", "จังหวัด", "พื้นที่", "area", "ระดับพื้นที่"],
    "geo_level": ["geo_level", "level", "ระดับ"],
    "area_plant_rai": ["area_plant_rai", "เนื้อที่เพาะปลูก", "เนื้อที่เพาะปลูก (ไร่)",
                       "เนื้อที่ปลูก (ไร่)", "plant_area"],
    "area_harvest_rai": ["area_harvest_rai", "เนื้อที่เก็บเกี่ยว", "เนื้อที่เก็บเกี่ยว (ไร่)",
                         "harvest_area"],
    "production_ton": ["production_ton", "ผลผลิต", "ผลผลิต (ตัน)", "production"],
    "yield_per_rai": ["yield_per_rai", "ผลผลิตต่อไร่", "ผลผลิตต่อไร่ (กก.)",
                      "ผลผลิตต่อไร่ (กก./ไร่)", "yield"],
}
FARMGATE_ALIASES = {
    "product": ["product", "สินค้า", "ชนิดสินค้า"],
    "year": ["year", "ปี"],
    "month": ["month", "เดือน"],
    "week": ["week", "สัปดาห์"],
    "price_baht_per_ton": ["price_baht_per_ton", "ราคา (บาท/ตัน)", "price_ton"],
    "price_baht_per_kg": ["price_baht_per_kg", "ราคา (บาท/กก.)", "price_kg", "price"],
}
SPATIAL_RAIN_ALIASES = {
    "year": ["YEAR", "year"],
    "month": ["MONTH", "month"],
    "prov_id": ["PROV_ID", "prov_id"],
    "province": ["PROV_T", "province", "จังหวัด"],
    "min_rain_mm": ["MinRain", "min_rain"],
    "max_rain_mm": ["MaxRain", "max_rain"],
    "avg_rain_mm": ["AvgRain", "avg_rain", "rain_mm"],
}
NATIONAL_RAIN_ALIASES = {
    "year": ["YEAR", "year", "ปี"],
    "month": ["MONTH", "month", "เดือน"],
    "rain_mm": ["AvgRain", "avg_rain", "rain_mm", "rainfall_mm", "rain", "RAIN"],
}
TEMP_ALIASES = {
    "date": ["date", "DATE", "datetime", "วันที่"],
    "year": ["YEAR", "year"],
    "month": ["MONTH", "month"],
    "province": ["PROV_T", "province", "จังหวัด"],
    "tmax_c": ["Tmax", "TMAX", "tmax", "max_temp", "max_temp_c", "MaxTemp"],
    "tmin_c": ["Tmin", "TMIN", "tmin", "min_temp", "min_temp_c", "MinTemp"],
}
TMD_ALIASES = {
    "station_number": ["station_number", "WmoStationNumber", "StationNumber"],
    "station_name": ["station_name", "StationNameThai", "StationNameTh"],
    "province": ["province", "Province"],
    "latitude": ["latitude", "Latitude", "Latitude.Value"],
    "longitude": ["longitude", "Longitude", "Longitude.Value"],
    "datetime": ["datetime", "Observation.DateTime", "DateTime"],
    "temp_c": ["temp_c", "Observation.Temperature", "Observation.Temperature.Value"],
    "max_temp_c": ["max_temp_c", "Observation.MaxTemperature",
                   "Observation.MaxTemperature.Value"],
    "min_temp_c": ["min_temp_c", "Observation.MinTemperature",
                   "Observation.MinTemperature.Value"],
    "relative_humidity_pct": ["relative_humidity_pct", "Observation.RelativeHumidity",
                              "Observation.RelativeHumidity.Value"],
    "rainfall_mm": ["rainfall_mm", "Observation.Rainfall", "Observation.Rainfall.Value",
                    "Observation.Rainfall24Hr"],
}
IRRIGATION_ALIASES = {
    "province": ["province", "จังหวัด", "PROV_T"],
    "year": ["year", "ปี"],
    "irrigation_area_rai": ["irrigation_area_rai", "พื้นที่ชลประทาน", "irrigated_area_rai"],
    "agri_area_rai": ["agri_area_rai", "agricultural_area_rai", "total_agricultural_area_rai",
                      "พื้นที่เกษตรกรรม", "พื้นที่ถือครองทางการเกษตร"],
    "irrigation_ratio_pct": ["irrigation_ratio_pct", "irrigation_ratio", "สัดส่วนชลประทาน"],
}
SOIL_ALIASES = {
    "province": ["province", "จังหวัด", "PROV_T"],
    "product": ["product", "crop", "พืช"],
    "s1": ["s1", "s1_pct", "S1", "S1 %", "s1_rai"],
    "s2": ["s2", "s2_pct", "S2", "S2 %", "s2_rai"],
    "s3": ["s3", "s3_pct", "S3", "S3 %", "s3_rai"],
    "n": ["n", "n_pct", "N", "N %", "n_rai"],
}
COST_ALIASES = {
    "product": ["product", "crop", "สินค้า", "พืช"],
    "year": ["year", "ปี"],
    "province": ["province", "จังหวัด"],
    "seed_cost": ["seed_cost", "seed", "ค่าพันธุ์"],
    "fertilizer_cost": ["fertilizer_cost", "fertilizer", "ค่าปุ๋ยเคมี", "ค่าปุ๋ย"],
    "pesticide_cost": ["pesticide_cost", "pesticide", "ค่าสารเคมีกำจัดศัตรูพืช", "ค่าสารเคมี"],
    "fuel_cost": ["fuel_cost", "fuel", "ค่าน้ำมัน/สูบน้ำ", "ค่าน้ำมัน"],
    "machinery_cost": ["machinery_cost", "machinery", "ค่าเครื่องจักร"],
    "labor_cost": ["labor_cost", "labour_cost", "labor", "ค่าแรงงานคน", "ค่าแรงงาน"],
    "land_rent_cost": ["land_rent_cost", "land_rent", "ค่าเช่าที่ดิน"],
    "total_cost_baht_per_rai": ["total_cost_baht_per_rai", "total_cost", "ต้นทุนรวมต่อไร่"],
    "cost_baht_per_kg": ["cost_baht_per_kg", "cost_per_kg", "ต้นทุนต่อกิโลกรัม"],
    "mechanization_pct": ["mechanization_pct", "mechanization_index", "mechanization",
                          "สัดส่วนการใช้เครื่องจักร"],
}
DISASTER_ALIASES = {
    "province": ["province", "จังหวัด"],
    "year": ["year", "ปี"],
    "flood_area_rai": ["flood_area_rai", "flood_rai", "พื้นที่ประสบอุทกภัย"],
    "drought_area_rai": ["drought_area_rai", "drought_rai", "พื้นที่ประสบภัยแล้ง"],
    "total_affected_rai": ["total_affected_rai", "total_rai", "พื้นที่ประสบภัยรวม"],
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def _norm_header(h: object) -> str:
    return " ".join(str(h).replace("\n", " ").split()).lower()


def apply_aliases(df: pd.DataFrame, aliases: dict[str, list[str]]) -> pd.DataFrame:
    """Rename columns to canonical names; unknown columns are kept untouched."""
    lookup = {_norm_header(a): canon for canon, alist in aliases.items() for a in alist}
    rename: dict[str, str] = {}
    taken: set[str] = set()
    for col in df.columns:
        canon = lookup.get(_norm_header(col))
        if canon and canon not in taken:
            rename[col] = canon
            taken.add(canon)
    return df.rename(columns=rename)


def require_columns(df: pd.DataFrame, cols: list[str], key: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"{key}: ไม่พบคอลัมน์ที่จำเป็น {missing} (พบ: {list(df.columns)[:15]})"
        )


def to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", "", regex=False).str.strip()
                .replace({"": np.nan, "-": np.nan, "nan": np.nan, "None": np.nan}),
                errors="coerce",
            )
    return df


def to_buddhist_year(series: pd.Series) -> pd.Series:
    """Convert CE years (< 2400) to BE; BE values are left unchanged."""
    s = pd.to_numeric(series, errors="coerce")
    return s.where(s >= 2400, s + 543).astype("Int64")


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None)
        frames = [df for df in sheets.values() if not df.empty]
        if not frames:
            raise DataValidationError(f"{path.name}: ไฟล์ว่าง")
        # Keep sheets that share the first sheet's header set (multi-sheet exports).
        first = set(map(_norm_header, frames[0].columns))
        same = [f for f in frames if set(map(_norm_header, f.columns)) == first]
        return pd.concat(same, ignore_index=True)
    for enc in ("utf-8-sig", "cp874", "tis-620"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise DataValidationError(f"{path.name}: อ่าน encoding ไม่ได้ (utf-8 / cp874)")


def find_file(key: str) -> Path | None:
    for p in cfg.DATASET_FILES.get(key, []):
        if p.exists():
            return p
    return None


def _add_province_cols(df: pd.DataFrame, col: str = "province") -> pd.DataFrame:
    df[col] = df[col].map(cfg.canonical_province)
    df["region"] = df[col].map(cfg.PROVINCE_TO_REGION)
    return df


# ---------------------------------------------------------------------------
# Per-dataset loaders (each takes a path, returns a normalised DataFrame)
# ---------------------------------------------------------------------------
def load_production(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), PRODUCTION_ALIASES)
    require_columns(df, ["year", "product", "province", "area_plant_rai",
                         "area_harvest_rai", "production_ton"], "production")
    df = to_numeric(df, ["area_plant_rai", "area_harvest_rai", "production_ton",
                         "yield_per_rai"])
    df["year"] = to_buddhist_year(df["year"])
    df["product"] = df["product"].astype(str).str.strip()
    df["province"] = df["province"].astype(str).str.strip()

    # geo_level: trust the source column when present, otherwise classify.
    if "geo_level" in df.columns:
        df["geo_level"] = df["geo_level"].astype(str).str.strip().str.lower()
        bad = ~df["geo_level"].isin(["country", "region", "province"])
        df.loc[bad, "geo_level"] = df.loc[bad, "province"].map(cfg.classify_geo_level)
    else:
        df["geo_level"] = df["province"].map(cfg.classify_geo_level)

    is_prov = df["geo_level"] == "province"
    is_reg = df["geo_level"] == "region"
    df.loc[is_prov, "province"] = df.loc[is_prov, "province"].map(cfg.canonical_province)
    df.loc[is_reg, "province"] = df.loc[is_reg, "province"].map(
        lambda s: cfg.REGION_ALIASES.get(s, s))
    df.loc[df["geo_level"] == "country", "province"] = cfg.COUNTRY_LABEL
    df["region"] = np.where(is_prov, df["province"].map(cfg.PROVINCE_TO_REGION),
                            np.where(is_reg, df["province"], None))

    # Derived metrics (data dictionary formulas); recompute yield where missing.
    harvest = df["area_harvest_rai"].replace(0, np.nan)
    plant = df["area_plant_rai"].replace(0, np.nan)
    computed_yield = df["production_ton"] * 1000 / harvest
    if "yield_per_rai" not in df.columns:
        df["yield_per_rai"] = computed_yield
    else:
        df["yield_per_rai"] = df["yield_per_rai"].fillna(computed_yield)
    df["harvest_ratio"] = df["area_harvest_rai"] / plant * 100
    df["damaged_area"] = df["area_plant_rai"] - df["area_harvest_rai"]
    return df.dropna(subset=["year"]).reset_index(drop=True)


def load_farmgate(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), FARMGATE_ALIASES)
    require_columns(df, ["product", "year", "month"], "farmgate")
    if "price_baht_per_ton" not in df.columns and "price_baht_per_kg" not in df.columns:
        raise DataValidationError("farmgate: ต้องมี price_baht_per_ton หรือ price_baht_per_kg")
    df = to_numeric(df, ["month", "week", "price_baht_per_ton", "price_baht_per_kg"])
    df["year"] = to_buddhist_year(df["year"])
    df["product"] = df["product"].astype(str).str.strip()
    if "price_baht_per_kg" not in df.columns:
        df["price_baht_per_kg"] = df["price_baht_per_ton"] / 1000
    elif "price_baht_per_ton" in df.columns:
        df["price_baht_per_kg"] = df["price_baht_per_kg"].fillna(df["price_baht_per_ton"] / 1000)
    if "week" not in df.columns:
        df["week"] = 1
    df["week"] = df["week"].fillna(1)
    # Approximate observation date (week-of-month -> day 1, 8, 15, 22, 28) in CE.
    day = ((df["week"].clip(1, 5) - 1) * 7 + 1).clip(upper=28).astype(int)
    df["date"] = pd.to_datetime(
        dict(year=df["year"].astype(int) - 543, month=df["month"].astype(int), day=day),
        errors="coerce",
    )
    return df.dropna(subset=["price_baht_per_kg", "date"]).sort_values("date").reset_index(drop=True)


def load_spatial_rain(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), SPATIAL_RAIN_ALIASES)
    require_columns(df, ["year", "month", "province", "avg_rain_mm"], "spatial_rain")
    df = to_numeric(df, ["month", "prov_id", "min_rain_mm", "max_rain_mm", "avg_rain_mm"])
    df["year"] = to_buddhist_year(df["year"])
    df = _add_province_cols(df)
    return df.dropna(subset=["year", "month", "avg_rain_mm"]).reset_index(drop=True)


def load_national_rain(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), NATIONAL_RAIN_ALIASES)
    require_columns(df, ["year", "month", "rain_mm"], "national_rain")
    df = to_numeric(df, ["month", "rain_mm"])
    df["year"] = to_buddhist_year(df["year"])
    return df.dropna(subset=["year", "month", "rain_mm"]).reset_index(drop=True)


def load_provincial_temp(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), TEMP_ALIASES)
    if "date" in df.columns and ("year" not in df.columns or "month" not in df.columns):
        d = pd.to_datetime(df["date"], errors="coerce")
        df["year"], df["month"] = d.dt.year, d.dt.month
    require_columns(df, ["year", "month", "province", "tmax_c", "tmin_c"], "provincial_temp")
    df = to_numeric(df, ["month", "tmax_c", "tmin_c"])
    df["year"] = to_buddhist_year(df["year"])
    df = _add_province_cols(df)
    # Aggregate daily records (if any) to monthly means per province.
    out = (df.groupby(["year", "month", "province", "region"], dropna=False)[["tmax_c", "tmin_c"]]
             .mean().reset_index())
    return out.dropna(subset=["year", "month"])


def load_tmd_agromet(path: Path) -> pd.DataFrame:
    raw: Any = json.loads(path.read_text(encoding="utf-8-sig"))
    # Accept the raw TMD envelope ({"Stations": {"Station": [...]}}) or a plain list.
    if isinstance(raw, dict):
        for k in ("Stations", "stations", "data", "Station"):
            if k in raw:
                raw = raw[k]
                break
        if isinstance(raw, dict):
            raw = raw.get("Station", raw.get("station", [raw]))
    if not isinstance(raw, list) or not raw:
        raise DataValidationError("tmd_agromet: ไม่พบรายการสถานีในไฟล์ JSON")
    df = apply_aliases(pd.json_normalize(raw), TMD_ALIASES)
    require_columns(df, ["station_name", "province"], "tmd_agromet")
    df = to_numeric(df, ["latitude", "longitude", "temp_c", "max_temp_c", "min_temp_c",
                         "relative_humidity_pct", "rainfall_mm"])
    df["province"] = df["province"].map(cfg.canonical_province)
    return df


def load_irrigation(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), IRRIGATION_ALIASES)
    require_columns(df, ["province"], "irrigation")
    df = to_numeric(df, ["irrigation_area_rai", "agri_area_rai", "irrigation_ratio_pct"])
    if "year" in df.columns:
        df["year"] = to_buddhist_year(df["year"])
    if {"irrigation_area_rai", "agri_area_rai"} <= set(df.columns):
        computed = df["irrigation_area_rai"] / df["agri_area_rai"].replace(0, np.nan) * 100
        df["irrigation_ratio_pct"] = (df["irrigation_ratio_pct"].fillna(computed)
                                      if "irrigation_ratio_pct" in df.columns else computed)
    require_columns(df, ["irrigation_ratio_pct"], "irrigation")
    return _add_province_cols(df).reset_index(drop=True)


def load_soil(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), SOIL_ALIASES)
    require_columns(df, ["province", "product", "s1", "s2", "s3", "n"], "soil")
    df = to_numeric(df, ["s1", "s2", "s3", "n"])
    # Normalise each row to percentages (works whether the source holds % or rai).
    total = df[["s1", "s2", "s3", "n"]].sum(axis=1).replace(0, np.nan)
    for c in ["s1", "s2", "s3", "n"]:
        df[f"{c}_pct"] = df[c] / total * 100
    df["product"] = df["product"].astype(str).str.strip()
    return _add_province_cols(df).reset_index(drop=True)


def load_cost(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), COST_ALIASES)
    require_columns(df, ["product"], "cost")
    cats = [c for c in cfg.COST_CATEGORIES if c in df.columns]
    df = to_numeric(df, cats + ["total_cost_baht_per_rai", "cost_baht_per_kg",
                                "mechanization_pct"])
    if "total_cost_baht_per_rai" not in df.columns:
        if not cats:
            raise DataValidationError("cost: ต้องมี total_cost_baht_per_rai หรือคอลัมน์ต้นทุนรายหมวด")
        df["total_cost_baht_per_rai"] = df[cats].sum(axis=1, min_count=1)
    if "year" in df.columns:
        df["year"] = to_buddhist_year(df["year"])
    df["product"] = df["product"].astype(str).str.strip()
    if "province" in df.columns:
        df["province"] = df["province"].map(cfg.canonical_province)
    return df.reset_index(drop=True)


def load_disaster(path: Path) -> pd.DataFrame:
    df = apply_aliases(read_table(path), DISASTER_ALIASES)
    require_columns(df, ["province"], "disaster")
    df = to_numeric(df, ["flood_area_rai", "drought_area_rai", "total_affected_rai"])
    if "year" in df.columns:
        df["year"] = to_buddhist_year(df["year"])
    if "total_affected_rai" not in df.columns:
        parts = [c for c in ("flood_area_rai", "drought_area_rai") if c in df.columns]
        if not parts:
            raise DataValidationError("disaster: ไม่พบคอลัมน์พื้นที่ประสบภัย")
        df["total_affected_rai"] = df[parts].sum(axis=1, min_count=1)
    return _add_province_cols(df).reset_index(drop=True)


def load_geojson(path: Path) -> dict:
    gj = json.loads(path.read_text(encoding="utf-8-sig"))
    feats = gj.get("features") if isinstance(gj, dict) else None
    if not feats:
        raise DataValidationError("geojson: ไม่พบ features")
    for f in feats:
        props = f.setdefault("properties", {})
        name = props.get("pro_th") or props.get("PROV_T") or props.get("name_th")
        if not name:
            raise DataValidationError("geojson: feature ไม่มี properties.pro_th")
        props["pro_th"] = cfg.canonical_province(name)
        f["id"] = props["pro_th"]
    return gj


LOADERS: dict[str, Callable[[Path], Any]] = {
    "production": load_production,
    "geojson": load_geojson,
    "spatial_rain": load_spatial_rain,
    "national_rain": load_national_rain,
    "provincial_temp": load_provincial_temp,
    "tmd_agromet": load_tmd_agromet,
    "irrigation": load_irrigation,
    "soil": load_soil,
    "cost": load_cost,
    "disaster": load_disaster,
    "farmgate": load_farmgate,
}


def load_dataset(key: str) -> tuple[Any, DatasetStatus]:
    label = cfg.DATASET_LABELS.get(key, key)
    path = find_file(key)
    if path is None:
        expected = cfg.DATASET_FILES[key][0]
        try:
            shown = expected.relative_to(cfg.PROJECT_ROOT)
        except ValueError:
            shown = expected
        return None, DatasetStatus(key, label, None, False, 0,
                                   f"ไม่พบไฟล์ — วางไฟล์ที่ `{shown}`")
    try:
        data = LOADERS[key](path)
    except Exception as exc:  # report every failure; never fall back to fake data
        return None, DatasetStatus(key, label, str(path), False, 0, f"โหลดไม่สำเร็จ: {exc}")
    rows = len(data.get("features", [])) if isinstance(data, dict) else len(data)
    return data, DatasetStatus(key, label, str(path), True, rows, "พร้อมใช้งาน")


def load_all() -> tuple[dict[str, Any], dict[str, DatasetStatus]]:
    data: dict[str, Any] = {}
    status: dict[str, DatasetStatus] = {}
    for key in LOADERS:
        data[key], status[key] = load_dataset(key)
    return data, status
