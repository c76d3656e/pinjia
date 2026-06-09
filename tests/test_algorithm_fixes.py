#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权重与综合评价算法修复专项测试。
"""

import unittest
import numpy as np

from demo_app import app, app_state, calculate_ahp_weights, calculate_indicator_score_new
from src.models.evaluation import EvaluationModel, EvaluationRange, WeightMethod
from src.models.indicators import Indicator


class TestAlgorithmFixes(unittest.TestCase):
    def test_demo_ahp_rejects_non_reciprocal_matrix(self):
        weights = calculate_ahp_weights([
            [1.0, 3.0, 4.0],
            [0.5, 1.0, 2.0],
            [0.25, 0.5, 1.0],
        ])

        self.assertIsNone(weights)

    def test_demo_ahp_rejects_inconsistent_matrix(self):
        weights = calculate_ahp_weights([
            [1.0, 9.0, 1.0],
            [1 / 9, 1.0, 9.0],
            [1.0, 1 / 9, 1.0],
        ])

        self.assertIsNone(weights)

    def test_demo_ahp_returns_normalized_weights(self):
        weights = calculate_ahp_weights([
            [1.0, 2.0, 4.0],
            [0.5, 1.0, 2.0],
            [0.25, 0.5, 1.0],
        ])

        self.assertIsNotNone(weights)
        self.assertAlmostEqual(sum(weights), 1.0, places=6)
        self.assertGreater(weights[0], weights[1])
        self.assertGreater(weights[1], weights[2])

    def test_piecewise_score_respects_lower_is_better_direction(self):
        range_data = {
            "excellent": {"operator": "≤", "value": 5},
            "good": {"min": 5, "max": 10},
            "average": {"min": 10, "max": 15},
            "poor": {"min": 15, "max": 20},
            "verypoor": {"operator": "≥", "value": 20},
        }

        good_low, _ = calculate_indicator_score_new(6, range_data)
        good_high, _ = calculate_indicator_score_new(9, range_data)

        self.assertGreater(good_low, good_high)

    def test_piecewise_score_respects_higher_is_better_direction(self):
        range_data = {
            "excellent": {"operator": "≥", "value": 100},
            "good": {"min": 80, "max": 100},
            "average": {"min": 60, "max": 80},
            "poor": {"min": 40, "max": 60},
            "verypoor": {"operator": "≤", "value": 40},
        }

        good_low, _ = calculate_indicator_score_new(85, range_data)
        good_high, _ = calculate_indicator_score_new(95, range_data)

        self.assertGreater(good_high, good_low)

    def test_entropy_weights_use_real_data_and_indicator_direction(self):
        model = EvaluationModel()
        data = np.array([
            [10.0, 100.0],
            [20.0, 80.0],
            [40.0, 60.0],
        ])

        weights = model.calculate_entropy_weights(
            data,
            ["benefit", "cost"],
            benefit_flags=[True, False],
        )

        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        self.assertGreater(weights["benefit"], 0)
        self.assertGreater(weights["cost"], 0)

    def test_demo_entropy_requires_data(self):
        original_selected = app_state["selected_indicators"]
        try:
            app_state["selected_indicators"] = [
                {"id": "technical_1", "name": "大块率", "is_positive": False},
                {"id": "technical_6", "name": "松散系数", "is_positive": True},
            ]

            with app.test_client() as client:
                response = client.post("/api/weights/calculate", json={"method": "entropy"})

            data = response.get_json()
            self.assertFalse(data["success"])
            self.assertIn("熵权法", data["message"])
        finally:
            app_state["selected_indicators"] = original_selected

    def test_model_evaluation_uses_final_indicator_weights_once(self):
        indicators = [
            Indicator(id="a", name="A", category_id="c1"),
            Indicator(id="b", name="B", category_id="c1"),
            Indicator(id="c", name="C", category_id="c2"),
        ]
        model = EvaluationModel()
        model.set_indicators(indicators)
        model.set_weights({"a": 0.2, "b": 0.3, "c": 0.5})
        model.set_category_weights({"c1": 0.5, "c2": 0.5})
        model.set_ranges({
            "a": EvaluationRange((90, 100), (80, 89), (70, 79), (0, 69)),
            "b": EvaluationRange((90, 100), (80, 89), (70, 79), (0, 69)),
            "c": EvaluationRange((90, 100), (80, 89), (70, 79), (0, 69)),
        })
        model.set_measured_values({"a": 95, "b": 85, "c": 75})

        result = model.calculate_evaluation(WeightMethod.EXPERT)

        expected = 95.0 * 0.2 + 85.0 * 0.3 + 75.0 * 0.5
        self.assertAlmostEqual(result.total_score, expected, places=6)


if __name__ == "__main__":
    unittest.main()
