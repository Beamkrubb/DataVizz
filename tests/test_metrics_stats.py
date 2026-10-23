"""Formula tests: expected values are worked by hand from the spec formulas."""
import math
import unittest

import numpy as np
import pandas as pd

from src import metrics as m
from src import stats as st


class MetricTests(unittest.TestCase):
    def test_yoy(self):
        self.assertAlmostEqual(m.yoy_growth(110, 100), 10.0)
        self.assertAlmostEqual(m.yoy_growth(90, 100), -10.0)
        self.assertIsNone(m.yoy_growth(5, 0))
        self.assertIsNone(m.yoy_growth(5, None))

    def test_yield_and_harvest_ratio(self):
        self.assertAlmostEqual(m.yield_kg_per_rai(450, 1000), 450.0)
        self.assertAlmostEqual(m.harvest_ratio(950, 1000), 95.0)
        self.assertIsNone(m.yield_kg_per_rai(1, 0))

    def test_quadrants(self):
        x = pd.Series([10, 1, 1, 10, np.nan])
        y = pd.Series([10, 10, 1, 1, 5])
        self.assertEqual(list(m.classify_quadrant(x, y, 5, 5)), ["Q1", "Q2", "Q3", "Q4", ""])

    def test_dry_spell_detected(self):
        rows = []
        for yr, (jun, jul) in {2561: (200, 200), 2563: (220, 180), 2562: (100, 120)}.items():
            rows += [{"year": yr, "month": 6, "rain_mm": jun},
                     {"year": yr, "month": 7, "rain_mm": jul}]
        r = m.dry_spell_check(pd.DataFrame(rows), 2562)
        self.assertAlmostEqual(r.baseline_mm, 400.0)
        self.assertAlmostEqual(r.current_mm, 220.0)
        self.assertAlmostEqual(r.deficit_pct, 45.0)
        self.assertTrue(r.risk)

    def test_dry_spell_no_baseline(self):
        df = pd.DataFrame([{"year": 2562, "month": 6, "rain_mm": 1},
                           {"year": 2562, "month": 7, "rain_mm": 1}])
        r = m.dry_spell_check(df, 2562)
        self.assertFalse(r.risk)
        self.assertIsNone(r.baseline_mm)

    def test_dry_spell_incomplete_year_ignored(self):
        df = pd.DataFrame([{"year": 2562, "month": 6, "rain_mm": 1}])
        self.assertIsNone(m.dry_spell_check(df, 2562).current_mm)

    def test_irrigation_and_soil(self):
        self.assertAlmostEqual(m.irrigation_ratio(25, 100), 25.0)
        self.assertTrue(m.soil_mismatch(20, 11))
        self.assertFalse(m.soil_mismatch(20, 10))

    def test_margin(self):
        margin, ratio = m.profit_margin(8.0, 6.0)
        self.assertAlmostEqual(margin, 2.0)
        self.assertAlmostEqual(ratio, 25.0)
        self.assertEqual(m.profit_margin(None, 1), (None, None))

    def test_break_even(self):
        r = m.break_even(area_rai=10, yield_kg_rai=500, price_kg=8,
                         variable_cost_rai=3000, fixed_cost_rai=500)
        self.assertEqual(r.tc_rai, 3500)
        self.assertEqual(r.tc_total, 35000)
        self.assertEqual(r.revenue, 40000)
        self.assertEqual(r.net_profit, 5000)
        self.assertAlmostEqual(r.break_even_yield, 437.5)
        self.assertAlmostEqual(r.break_even_price, 7.0)
        self.assertAlmostEqual(r.margin_pct, 12.5)

    def test_price_summary(self):
        s = m.price_summary(pd.Series([1, 2, 3]))
        self.assertEqual((s["min"], s["max"], s["mean"]), (1, 3, 2))
        self.assertAlmostEqual(s["std"], 1.0)

    def test_match_product(self):
        cands = ["ข้าวเปลือกเจ้านาปี ความชื้น 15%", "มันสำปะหลังสด", "ข้าวโพดเลี้ยงสัตว์ ความชื้น 14.5%"]
        self.assertEqual(m.match_product("มันสำปะหลังโรงงาน", cands), "มันสำปะหลังสด")
        self.assertTrue(m.match_product("ข้าวนาปี", cands).startswith("ข้าวเปลือกเจ้านาปี"))
        self.assertIsNone(m.match_product("ยางพารา", cands))


class StatsTests(unittest.TestCase):
    def test_perfect_linear(self):
        r = st.correlation_report([1, 2, 3, 4, 5], [3, 5, 7, 9, 11])
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.pearson_r, 1.0)
        self.assertAlmostEqual(r.spearman_rho, 1.0)
        self.assertAlmostEqual(r.slope, 2.0)
        self.assertAlmostEqual(r.intercept, 1.0)
        self.assertAlmostEqual(r.r_squared, 1.0)
        self.assertTrue(r.significant)

    def test_pearson_matches_formula(self):
        x = np.array([1200, 1350, 980, 1500, 1100, 1420], float)
        y = np.array([410, 445, 380, 470, 400, 430], float)
        num = ((x - x.mean()) * (y - y.mean())).sum()
        den = math.sqrt(((x - x.mean()) ** 2).sum() * ((y - y.mean()) ** 2).sum())
        r = st.correlation_report(x, y)
        self.assertAlmostEqual(r.pearson_r, num / den)
        self.assertAlmostEqual(r.r_squared, (num / den) ** 2)

    def test_monotonic_nonlinear_spearman(self):
        r = st.correlation_report([1, 2, 3, 4, 5], [1, 4, 9, 16, 100])
        self.assertAlmostEqual(r.spearman_rho, 1.0)
        self.assertLess(r.pearson_r, 1.0)

    def test_insufficient_and_constant(self):
        self.assertFalse(st.correlation_report([1, 2], [1, 2]).ok)
        self.assertFalse(st.correlation_report([1, 1, 1], [1, 2, 3]).ok)
        self.assertEqual(st.correlation_report([1, 2, None, 4], [1, None, 3, 4]).n, 2)


if __name__ == "__main__":
    unittest.main()
