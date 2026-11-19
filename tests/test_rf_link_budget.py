import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import rf_link_budget as rf  # noqa: E402


class TestRfLinkBudget(unittest.TestCase):
    def test_fspl_433mhz_at_1km(self):
        # 20*log10(1) + 20*log10(433) + 32.44 ≈ 85.17 dB
        fspl = rf.compute_fspl_db(1.0, 433.0)
        self.assertAlmostEqual(fspl, 85.17, places=1)

    def test_lora_sf12_css_metrics(self):
        proc_gain = rf.compute_processing_gain_db(12)
        self.assertAlmostEqual(proc_gain, 36.12, places=2)

        sens = rf.compute_rx_sensitivity_dbm(125_000.0, 12, noise_figure_db=6.0)
        self.assertAlmostEqual(sens, -137.03, places=1)

    def test_end_to_end_link_budget_and_fresnel(self):
        res_1km = rf.analyze_lora_link(distance_km=1.0)
        res_10km = rf.analyze_lora_link(distance_km=10.0)

        self.assertGreater(res_1km.link_margin_db, res_10km.link_margin_db)
        self.assertAlmostEqual(res_1km.symbol_duration_ms, 32.77, places=2)
        self.assertAlmostEqual(res_1km.symbol_rate_sps, 30.52, places=2)
        self.assertAlmostEqual(res_1km.bit_rate_bps, 183.11, places=1)
        self.assertGreater(res_1km.link_margin_db, 50.0)
        self.assertGreater(res_10km.fresnel_60pct_clearance_m, res_1km.fresnel_60pct_clearance_m)


if __name__ == "__main__":
    unittest.main()
