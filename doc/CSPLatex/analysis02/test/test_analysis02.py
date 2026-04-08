from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "script"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_analysis02 as a2


class TestAnalysis02(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = Path(__file__).resolve().parents[1]
        self.top30_csv = self.base_dir.parent / "analysis01" / "output" / "analysis-5_top30.csv"

    def test_load_top30_trials_count_and_family_size(self) -> None:
        trials = a2.load_top30_trials(self.top30_csv)
        self.assertEqual(len(trials), 30)
        for trial in trials:
            self.assertEqual(set(trial.posteriors.keys()), set(a2.FAMILY_ORDER))

    def test_confusion_row_sum_close_to_one(self) -> None:
        trials = a2.load_top30_trials(self.top30_csv)
        result = a2.run_categorical_confusion(trials, repeats_per_family=20, seed=42)
        for row in result["confusion_matrix"]:
            self.assertTrue(math.isclose(sum(row), 1.0, rel_tol=0.0, abs_tol=1e-9))

    def test_full_run_outputs_files(self) -> None:
        result = a2.run(self.base_dir)
        self.assertEqual(result["n_trials"], 30)
        self.assertTrue(0.0 <= result["diagonal_mean"] <= 1.0)
        output_dir = self.base_dir / "output"
        self.assertTrue((output_dir / "analysis02_categorical_confusion.json").exists())
        self.assertTrue((output_dir / "analysis02_categorical_confusion_matrix.csv").exists())
        self.assertTrue((output_dir / "figures" / "fig_analysis02_confusion_heatmap.png").exists())
        self.assertTrue((output_dir / "figures" / "fig_analysis02_diagonal_bars.png").exists())


if __name__ == "__main__":
    unittest.main()
