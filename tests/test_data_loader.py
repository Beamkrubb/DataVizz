"""Loader tests. Fixtures are tiny hand-written tables created in a temp dir
purely to exercise parsing logic — they are never read by the app."""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src import config as cfg
from src import data_loader as dl


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _csv(self, name, rows):
        p = self.tmp / name
        pd.DataFrame(rows).to_csv(p, index=False, encoding="utf-8-sig")
        return p

    def test_production_geo_levels_and_derived_metrics(self):
        p = self._csv("prod.csv", [
            {"ปี": 2562, "สินค้า": "ข้าวนาปี", "จังหวัด": "ทั้งประเทศ",
             "area_plant_rai": "1,000", "area_harvest_rai": 800, "production_ton": 400},
            {"ปี": 2562, "สินค้า": "ข้าวนาปี", "จังหวัด": "ภาคเหนือ",
             "area_plant_rai": 500, "area_harvest_rai": 500, "production_ton": 250},
            {"ปี": 2562, "สินค้า": "ข้าวนาปี", "จังหวัด": "จังหวัดกรุงเทพฯ",
             "area_plant_rai": 10, "area_harvest_rai": 0, "production_ton": 0},
        ])
        df = dl.load_production(p)
        self.assertEqual(list(df["geo_level"]), ["country", "region", "province"])
        self.assertEqual(df.loc[2, "province"], "กรุงเทพมหานคร")
        self.assertEqual(df.loc[2, "region"], "ภาคกลาง")
        self.assertAlmostEqual(df.loc[0, "yield_per_rai"], 500.0)   # 400*1000/800
        self.assertAlmostEqual(df.loc[0, "harvest_ratio"], 80.0)
        self.assertAlmostEqual(df.loc[0, "damaged_area"], 200.0)
        self.assertTrue(pd.isna(df.loc[2, "yield_per_rai"]))       # no div-by-zero

    def test_production_missing_column_raises(self):
        p = self._csv("bad.csv", [{"year": 2562, "product": "x"}])
        with self.assertRaises(dl.DataValidationError):
            dl.load_production(p)

    def test_spatial_rain_converts_ce_to_be(self):
        p = self._csv("rain.csv", [
            {"YEAR": 2019, "MONTH": 6, "PROV_ID": 10, "PROV_T": "อยุธยา",
             "MinRain": 1, "MaxRain": 9, "AvgRain": 5}])
        df = dl.load_spatial_rain(p)
        self.assertEqual(int(df.loc[0, "year"]), 2562)
        self.assertEqual(df.loc[0, "province"], "พระนครศรีอยุธยา")

    def test_farmgate_price_per_kg_and_date(self):
        p = self._csv("fg.csv", [
            {"product": "ข้าวโพดเลี้ยงสัตว์", "year": 2562, "month": 3, "week": 2,
             "price_baht_per_ton": 8000}])
        df = dl.load_farmgate(p)
        self.assertAlmostEqual(df.loc[0, "price_baht_per_kg"], 8.0)
        self.assertEqual(df.loc[0, "date"], pd.Timestamp("2019-03-08"))

    def test_soil_rows_normalised_to_percent(self):
        p = self._csv("soil.csv", [
            {"province": "ขอนแก่น", "product": "อ้อยโรงงาน",
             "s1_rai": 50, "s2_rai": 30, "s3_rai": 15, "n_rai": 5}])
        df = dl.load_soil(p)
        self.assertAlmostEqual(df.loc[0, "s1_pct"], 50.0)
        self.assertAlmostEqual(df[["s1_pct", "s2_pct", "s3_pct", "n_pct"]].sum(axis=1)[0], 100.0)

    def test_irrigation_ratio_computed(self):
        p = self._csv("irr.csv", [{"province": "ชัยนาท", "irrigation_area_rai": 30,
                                   "agri_area_rai": 120}])
        self.assertAlmostEqual(dl.load_irrigation(p).loc[0, "irrigation_ratio_pct"], 25.0)

    def test_cost_total_summed_from_categories(self):
        p = self._csv("cost.csv", [{"product": "ข้าวนาปี", "ค่าพันธุ์": 100,
                                    "ค่าปุ๋ยเคมี": 200, "ค่าเช่าที่ดิน": 300}])
        self.assertAlmostEqual(dl.load_cost(p).loc[0, "total_cost_baht_per_rai"], 600.0)

    def test_tmd_envelope(self):
        p = self.tmp / "tmd.json"
        p.write_text(json.dumps({"Stations": {"Station": [
            {"StationNameThai": "สถานี ก", "Province": "เชียงใหม่",
             "Observation": {"MaxTemperature": 33.1, "Rainfall": 2.0}}]}}), encoding="utf-8")
        df = dl.load_tmd_agromet(p)
        self.assertEqual(df.loc[0, "station_name"], "สถานี ก")
        self.assertAlmostEqual(df.loc[0, "max_temp_c"], 33.1)

    def test_geojson_ids(self):
        p = self.tmp / "g.geojson"
        p.write_text(json.dumps({"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"pro_th": "กรุงเทพฯ"}, "geometry": None}]}),
            encoding="utf-8")
        gj = dl.load_geojson(p)
        self.assertEqual(gj["features"][0]["id"], "กรุงเทพมหานคร")

    def test_missing_file_reports_status_not_fake_data(self):
        orig = cfg.DATASET_FILES["soil"]
        cfg.DATASET_FILES["soil"] = [self.tmp / "nope.csv"]
        try:
            data, status = dl.load_dataset("soil")
        finally:
            cfg.DATASET_FILES["soil"] = orig
        self.assertIsNone(data)
        self.assertFalse(status.loaded)
        self.assertIn("ไม่พบไฟล์", status.message)


if __name__ == "__main__":
    unittest.main()
