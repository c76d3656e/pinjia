#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.abspath("src"))

from src.controllers.evaluation_controller import EvaluationController
from models.evaluation import EvaluationResult


class TestEvaluationController(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        self.temp_file_path = self.temp_file.name
        data = {
            "categories": [
                {
                    "id": "technical",
                    "name": "技术指标",
                    "indicators": [
                        {
                            "id": "tech_1",
                            "name": "大块率",
                            "unit": "%",
                            "is_positive": False,
                            "min_value": 0,
                            "max_value": 30,
                        },
                        {
                            "id": "tech_2",
                            "name": "抛掷率",
                            "unit": "%",
                            "is_positive": True,
                            "min_value": 60,
                            "max_value": 95,
                        },
                    ],
                },
                {
                    "id": "safety",
                    "name": "安全指标",
                    "indicators": [
                        {
                            "id": "safety_1",
                            "name": "飞石距离",
                            "unit": "m",
                            "is_positive": False,
                            "min_value": 50,
                            "max_value": 200,
                        }
                    ],
                },
            ]
        }
        json.dump(data, self.temp_file, ensure_ascii=False)
        self.temp_file.close()
        self.controller = EvaluationController(self.temp_file_path)

    def tearDown(self):
        path = Path(self.temp_file_path)
        if path.exists():
            path.unlink()

    def load_and_select_all(self):
        self.controller.load_indicators()
        self.controller.update_selected_indicators(["tech_1", "tech_2", "safety_1"])

    def set_complete_data(self):
        self.controller.set_indicator_weights({"tech_1": 0.3, "tech_2": 0.3, "safety_1": 0.4})
        self.controller.set_category_weights({"technical": 0.6, "safety": 0.4})
        self.controller.set_indicator_ranges({
            "tech_1": {"excellent": (0, 5), "good": (5, 10), "average": (10, 20), "poor": (20, 30)},
            "tech_2": {"excellent": (90, 95), "good": (85, 89), "average": (75, 84), "poor": (60, 74)},
            "safety_1": {"excellent": (50, 80), "good": (80, 120), "average": (120, 160), "poor": (160, 200)},
        })
        self.controller.set_measured_values({"tech_1": 8, "tech_2": 88, "safety_1": 75})

    def test_initialization_and_load(self):
        self.assertIsNotNone(self.controller.evaluation_model)
        self.assertEqual(self.controller.selected_indicators, [])

        self.controller.load_indicators()
        self.assertEqual(len(self.controller.get_indicator_categories()), 2)
        self.assertEqual(len(self.controller.get_all_indicators()), 3)

    def test_load_errors_raise(self):
        controller = EvaluationController(str(Path(self.temp_file_path).with_suffix(".missing")))
        controller.load_indicators()
        self.assertGreater(len(controller.get_all_indicators()), 0)

    def test_indicator_selection(self):
        self.controller.load_indicators()
        self.controller.update_selected_indicators(["tech_1", "safety_1"])

        self.assertEqual([indicator.id for indicator in self.controller.selected_indicators], ["tech_1", "safety_1"])
        with self.assertRaises(ValueError):
            self.controller.update_selected_indicators(["missing"])

    def test_weight_calculation_methods(self):
        self.load_and_select_all()

        equal = self.controller.calculate_weights("Equal")
        self.assertAlmostEqual(sum(equal.values()), 1.0, places=6)

        expert = self.controller.calculate_weights(
            "Expert",
            category_weights={"technical": 0.6, "safety": 0.4},
            indicator_weights={
                "technical": {"tech_1": 0.5, "tech_2": 0.5},
                "safety": {"safety_1": 1.0},
            },
        )
        self.assertAlmostEqual(sum(expert.values()), 1.0, places=6)
        self.assertAlmostEqual(expert["safety_1"], 0.4, places=6)

        ahp = self.controller.calculate_weights(
            "AHP",
            comparison_matrix=np.array([
                [1.0, 2.0, 4.0],
                [0.5, 1.0, 2.0],
                [0.25, 0.5, 1.0],
            ]),
        )
        self.assertGreater(ahp["tech_1"], ahp["tech_2"])

        entropy = self.controller.calculate_weights(
            "Entropy",
            entropy_data=np.array([
                [10.0, 85.0, 100.0],
                [15.0, 90.0, 120.0],
                [8.0, 88.0, 75.0],
            ]),
        )
        self.assertAlmostEqual(sum(entropy.values()), 1.0, places=6)

        with self.assertRaises(ValueError):
            self.controller.calculate_weights("Entropy")

    def test_evaluation_flow_and_validation(self):
        self.load_and_select_all()
        self.assertGreater(len(self.controller.validate_evaluation_data()), 0)

        self.set_complete_data()
        self.assertEqual(self.controller.validate_evaluation_data(), [])

        result = self.controller.calculate_evaluation("Expert")
        self.assertIsInstance(result, EvaluationResult)
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)

        summary = self.controller.get_evaluation_summary()
        self.assertTrue(summary["ready_for_evaluation"])

    def test_reset_export_import(self):
        self.load_and_select_all()
        self.set_complete_data()

        exported = self.controller.export_evaluation_data()
        self.assertIn("selected_indicators", exported)
        self.assertIn("weights", exported)
        self.assertIn("measured_values", exported)

        self.controller.reset_evaluation_data()
        self.assertEqual(self.controller.selected_indicators, [])

    def test_set_invalid_weights_raises(self):
        self.load_and_select_all()
        with self.assertRaises(ValueError):
            self.controller.set_indicator_weights({"tech_1": 0.5})


if __name__ == "__main__":
    unittest.main()
