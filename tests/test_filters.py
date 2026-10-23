import unittest

import pandas as pd

from src import filters as f


def _prod():
    rows = []
    for prov, lvl, area in [("ทั้งประเทศ", "country", 1000), ("ภาคเหนือ", "region", 400),
                            ("เชียงใหม่", "province", 150), ("น่าน", "province", 100),
                            ("ขอนแก่น", "province", 300)]:
        rows.append({"year": 2562, "product": "ข้าวนาปี", "province": prov, "geo_level": lvl,
                     "area_plant_rai": area, "yield_per_rai": area / 2})
    return pd.DataFrame(rows)


class FilterTests(unittest.TestCase):
    def test_country_uses_country_row_not_sum(self):
        rows = f.scope_rows(_prod(), f.FilterState())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows["area_plant_rai"].iloc[0], 1000)   # not 550 (sum of provinces)

    def test_region_uses_region_row(self):
        s = f.FilterState(level=f.LEVEL_REGION, region="ภาคเหนือ")
        rows = f.scope_rows(_prod(), s)
        self.assertEqual(rows["area_plant_rai"].tolist(), [400])

    def test_province_scope(self):
        s = f.FilterState(level=f.LEVEL_PROVINCE, province="น่าน")
        self.assertEqual(f.scope_rows(_prod(), s)["area_plant_rai"].tolist(), [100])
        self.assertEqual(s.scope_region, "ภาคเหนือ")

    def test_province_rows_restricted_to_region(self):
        s = f.FilterState(level=f.LEVEL_REGION, region="ภาคเหนือ")
        self.assertEqual(sorted(f.province_rows(_prod(), s)["province"]), ["น่าน", "เชียงใหม่"])

    def test_national_reference(self):
        ref = f.national_reference(_prod(), "ข้าวนาปี", 2562)
        self.assertAlmostEqual(ref["x_mean"], (150 + 100 + 300) / 3)
        self.assertAlmostEqual(ref["country_yield"], 500)

    def test_available_crops_main_first(self):
        df = pd.DataFrame({"product": ["ยางพารา", "อ้อยโรงงาน", "ข้าวนาปี"], "year": [1, 1, 1]})
        self.assertEqual(f.available_crops(df), ["ข้าวนาปี", "อ้อยโรงงาน", "ยางพารา"])


if __name__ == "__main__":
    unittest.main()
