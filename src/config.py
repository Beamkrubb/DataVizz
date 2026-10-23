"""Project-wide constants: paths, geography, crops, and display labels.

Every value here comes from the project spec / data dictionary. Nothing in this
module is data about production, weather or prices — those are only ever read
from the source files listed in ``DATASET_FILES``.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Allow the data folder to be relocated (e.g. a shared drive) without code edits.
DATA_DIR = Path(os.environ.get("DATAVIZZ_DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"

# key -> candidate locations (first existing wins). Names follow data_sources.md.
DATASET_FILES: dict[str, list[Path]] = {
    "production": [
        DATA_DIR / "สถิติการผลิตสินค้าเกษตรรายปี 2550-2562.xlsx",
        PROJECT_ROOT / "สถิติการผลิตสินค้าเกษตรรายปี 2550-2562.xlsx",
        RAW_DIR / "oae_production_2550_2562.csv",
    ],
    "geojson": [DATA_DIR / "thai_provinces.geojson"],
    "spatial_rain": [RAW_DIR / "spatial_rain_hii.csv"],
    "national_rain": [RAW_DIR / "national_rain_1970_current.csv"],
    "provincial_temp": [RAW_DIR / "provincial_temp_2018_2019.csv"],
    "tmd_agromet": [RAW_DIR / "tmd_agromet_sample.json"],
    "irrigation": [RAW_DIR / "provincial_irrigation_rid_oae.csv"],
    "soil": [RAW_DIR / "ldd_soil_suitability.csv"],
    "cost": [RAW_DIR / "oae_production_cost_structure.csv"],
    "disaster": [RAW_DIR / "disaster_affected_agricultural_area.csv"],
    "farmgate": [RAW_DIR / "oae_farmgate_prices_2561_2562.csv"],
}

DATASET_LABELS: dict[str, str] = {
    "production": "สถิติการผลิตสินค้าเกษตรรายปี 2550–2562 (สศก.)",
    "geojson": "ขอบเขตจังหวัด GeoJSON (OpenGISData-Thailand)",
    "spatial_rain": "ฝนเชิงพื้นที่รายเดือน รายจังหวัด (สสน.)",
    "national_rain": "ฝนเชิงพื้นที่ทั้งประเทศ 1970–ปัจจุบัน (สสน.)",
    "provincial_temp": "อุณหภูมิสูงสุด-ต่ำสุด รายจังหวัด (สสน.)",
    "tmd_agromet": "ตรวจวัดอากาศเพื่อการเกษตรรายวัน (กรมอุตุฯ)",
    "irrigation": "พื้นที่ชลประทานและพื้นที่เกษตร (กรมชลประทาน/สศก.)",
    "soil": "ความเหมาะสมของดิน Agri-Map (กรมพัฒนาที่ดิน)",
    "cost": "ต้นทุนการผลิตและการใช้เครื่องจักร (สศก.)",
    "disaster": "พื้นที่การเกษตรประสบภัย (กสก./ปภ.)",
    "farmgate": "ราคาที่เกษตรกรขายได้ ณ ไร่นา รายสัปดาห์ (สศก.)",
}

# External services (keys are optional; the UI reports their absence honestly)
GISTDA_API_KEY = os.environ.get("GISTDA_API_KEY", "")

# ---------------------------------------------------------------------------
# Geography (OAE 4-region classification, 77 provinces)
# ---------------------------------------------------------------------------
COUNTRY_LABEL = "ทั้งประเทศ"
REGIONS: dict[str, list[str]] = {
    "ภาคเหนือ": [
        "เชียงราย", "เชียงใหม่", "น่าน", "พะเยา", "แพร่", "แม่ฮ่องสอน", "ลำปาง",
        "ลำพูน", "อุตรดิตถ์", "ตาก", "สุโขทัย", "พิษณุโลก", "พิจิตร", "กำแพงเพชร",
        "เพชรบูรณ์", "นครสวรรค์", "อุทัยธานี",
    ],
    "ภาคตะวันออกเฉียงเหนือ": [
        "กาฬสินธุ์", "ขอนแก่น", "ชัยภูมิ", "นครพนม", "นครราชสีมา", "บึงกาฬ",
        "บุรีรัมย์", "มหาสารคาม", "มุกดาหาร", "ยโสธร", "ร้อยเอ็ด", "เลย", "ศรีสะเกษ",
        "สกลนคร", "สุรินทร์", "หนองคาย", "หนองบัวลำภู", "อำนาจเจริญ", "อุดรธานี",
        "อุบลราชธานี",
    ],
    "ภาคกลาง": [
        "กรุงเทพมหานคร", "กาญจนบุรี", "จันทบุรี", "ฉะเชิงเทรา", "ชลบุรี", "ชัยนาท",
        "ตราด", "นครนายก", "นครปฐม", "นนทบุรี", "ปทุมธานี", "ประจวบคีรีขันธ์",
        "ปราจีนบุรี", "พระนครศรีอยุธยา", "เพชรบุรี", "ราชบุรี", "ระยอง", "ลพบุรี",
        "สมุทรปราการ", "สมุทรสงคราม", "สมุทรสาคร", "สระแก้ว", "สระบุรี", "สิงห์บุรี",
        "สุพรรณบุรี", "อ่างทอง",
    ],
    "ภาคใต้": [
        "กระบี่", "ชุมพร", "ตรัง", "นครศรีธรรมราช", "นราธิวาส", "ปัตตานี", "พังงา",
        "พัทลุง", "ภูเก็ต", "ยะลา", "ระนอง", "สงขลา", "สตูล", "สุราษฎร์ธานี",
    ],
}
PROVINCE_TO_REGION: dict[str, str] = {
    p: r for r, provinces in REGIONS.items() for p in provinces
}
ALL_PROVINCES: list[str] = sorted(PROVINCE_TO_REGION)

# Spelling variants seen across OAE / HII / GeoJSON sources -> canonical name
PROVINCE_ALIASES: dict[str, str] = {
    "กรุงเทพฯ": "กรุงเทพมหานคร",
    "กรุงเทพ": "กรุงเทพมหานคร",
    "กทม.": "กรุงเทพมหานคร",
    "อยุธยา": "พระนครศรีอยุธยา",
    "พระนครศรีอยุธยา ": "พระนครศรีอยุธยา",
    "ประจวบฯ": "ประจวบคีรีขันธ์",
    "นครศรีฯ": "นครศรีธรรมราช",
    "หนองบัวลำภู ": "หนองบัวลำภู",
}
REGION_ALIASES: dict[str, str] = {
    "เหนือ": "ภาคเหนือ",
    "ตะวันออกเฉียงเหนือ": "ภาคตะวันออกเฉียงเหนือ",
    "ภาคอีสาน": "ภาคตะวันออกเฉียงเหนือ",
    "กลาง": "ภาคกลาง",
    "ใต้": "ภาคใต้",
}
COUNTRY_ALIASES = {"ทั้งประเทศ", "รวมทั้งประเทศ", "ประเทศไทย", "รวม"}

# ---------------------------------------------------------------------------
# Crops and calendar
# ---------------------------------------------------------------------------
MAIN_CROPS = [
    "ข้าวนาปี",
    "ข้าวนาปรัง",
    "ข้าวโพดเลี้ยงสัตว์",
    "มันสำปะหลังโรงงาน",
    "อ้อยโรงงาน",
]
DEFAULT_CROP = "ข้าวนาปี"
PRODUCTION_YEARS = list(range(2550, 2563))   # พ.ศ. 2550–2562
CLIMATE_PRICE_YEARS = [2561, 2562]
DEFAULT_YEAR = 2562

# Keywords used to match a production crop to the closest farmgate-price,
# soil and cost product names (sources name products differently).
CROP_KEYWORDS: dict[str, list[str]] = {
    "ข้าวนาปี": ["ข้าวเปลือกเจ้านาปี", "นาปี", "ข้าวเปลือกเจ้า", "ข้าว"],
    "ข้าวนาปรัง": ["ข้าวเปลือกเจ้านาปรัง", "นาปรัง", "ข้าวเปลือกเจ้า", "ข้าว"],
    "ข้าวโพดเลี้ยงสัตว์": ["ข้าวโพดเลี้ยงสัตว์", "ข้าวโพด"],
    "มันสำปะหลังโรงงาน": ["มันสำปะหลังสด", "มันสำปะหลัง"],
    "อ้อยโรงงาน": ["อ้อยโรงงาน", "อ้อย"],
}

THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
               "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
RAINY_SEASON_MONTHS = range(5, 11)          # พ.ค.–ต.ค.
DRY_SPELL_MONTHS = (6, 7)                   # มิ.ย.–ก.ค.
DRY_SPELL_THRESHOLD_PCT = 30.0              # deficit vs. historical mean
SOIL_MISMATCH_THRESHOLD_PCT = 30.0          # S3 + N
RAINFED_IRRIGATION_THRESHOLD_PCT = 20.0     # irrigation ratio < 20% = rainfed

COST_CATEGORIES: dict[str, str] = {
    "seed_cost": "ค่าพันธุ์",
    "fertilizer_cost": "ค่าปุ๋ยเคมี",
    "pesticide_cost": "ค่าสารเคมีกำจัดศัตรูพืช",
    "fuel_cost": "ค่าน้ำมัน/สูบน้ำ",
    "machinery_cost": "ค่าเครื่องจักร",
    "labor_cost": "ค่าแรงงานคน",
    "land_rent_cost": "ค่าเช่าที่ดิน",
}
# Fixed vs variable split used to pre-fill the break-even calculator
FIXED_COST_KEYS = ["land_rent_cost"]


def canonical_province(name: object) -> str:
    """Return the canonical Thai province name (or the trimmed input)."""
    if name is None:
        return ""
    s = str(name).strip()
    if s.startswith("จังหวัด"):
        s = s[len("จังหวัด"):].strip()
    return PROVINCE_ALIASES.get(s, s)


def classify_geo_level(name: str) -> str:
    """Classify an area label as country / region / province / unknown."""
    s = str(name).strip()
    if s in COUNTRY_ALIASES:
        return "country"
    if s in REGIONS or s in REGION_ALIASES:
        return "region"
    if canonical_province(s) in PROVINCE_TO_REGION:
        return "province"
    return "unknown"
