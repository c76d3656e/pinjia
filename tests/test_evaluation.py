#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import numpy as np

from src.models.evaluation import (
    EvaluationModel,
    EvaluationRange,
    EvaluationResult,
    IndicatorResult,
    CategoryResult,
    WeightMethod,
    EvaluationGrade,
)
from src.models.indicators import Indicator


class TestEvaluationRange(unittest.TestCase):
    def test_grade_and_score(self):
        eval_range = EvaluationRange((90, 100), (80, 89), (70, 79), (0, 69))

        self.assertEqual(eval_range.get_grade(95), EvaluationGrade.EXCELLENT)
        self.assertEqual(eval_range.get_grade(85), EvaluationGrade.GOOD)
        self.assertEqual(eval_range.get_grade(75), EvaluationGrade.AVERAGE)
        self.assertEqual(eval_range.get_grade(65), EvaluationGrade.POOR)
        self.assertEqual(eval_range.get_score(85), 85.0)


class TestEvaluationResultModels(unittest.TestCase):
    def test_indicator_and_category_result_helpers(self):
        indicator = Indicator("i1", "指标1", category_id="c1")
        indicator_result = IndicatorResult(
            indicator=indicator,
            measured_value=88.0,
            weight=0.25,
            score=85.0,
            grade=EvaluationGrade.GOOD,
            weighted_score=21.25,
        )

        self.assertEqual(indicator_result.indicator_id, "i1")
        self.assertEqual(indicator_result.normalized_value, 88.0)
        self.assertEqual(indicator_result.get_weighted_score(), 21.25)

        category = CategoryResult(
            category=type("Category", (), {"id": "c1", "name": "分类1"})(),
            indicator_results=[indicator_result],
            weight=0.25,
            total_score=85.0,
            weighted_score=21.25,
            grade=EvaluationGrade.GOOD,
        )

        self.assertEqual(category.category_id, "c1")
        self.assertEqual(category.score, 85.0)
        self.assertEqual(category.get_weighted_score(), 21.25)

        result = EvaluationResult(
            category_results=[category],
            total_score=21.25,
            final_grade=EvaluationGrade.BAD,
            weight_method=WeightMethod.EXPERT,
        )
        self.assertEqual(result.indicator_results, [indicator_result])


class TestEvaluationModel(unittest.TestCase):
    def setUp(self):
        self.indicators = [
            Indicator("tech_1", "大块率", "%", is_positive=False, category_id="technical"),
            Indicator("tech_2", "抛掷率", "%", is_positive=True, category_id="technical"),
            Indicator("safety_1", "飞石距离", "m", is_positive=False, category_id="safety"),
        ]
        self.model = EvaluationModel()
        self.model.set_indicators(self.indicators)
        self.model.set_weights({"tech_1": 0.3, "tech_2": 0.3, "safety_1": 0.4})
        self.model.set_category_weights({"technical": 0.6, "safety": 0.4})
        self.model.set_ranges({
            "tech_1": EvaluationRange((0, 5), (5, 10), (10, 20), (20, 30)),
            "tech_2": EvaluationRange((90, 95), (85, 89), (75, 84), (60, 74)),
            "safety_1": EvaluationRange((50, 80), (80, 120), (120, 160), (160, 200)),
        })
        self.model.set_measured_values({"tech_1": 8.0, "tech_2": 88.0, "safety_1": 75.0})

    def test_validate_data(self):
        self.assertEqual(self.model.validate_data(), [])

        model = EvaluationModel()
        model.set_indicators(self.indicators)
        errors = model.validate_data()
        self.assertTrue(any("缺少权重设置" in error for error in errors))

    def test_ahp_weights_calculation(self):
        matrix = np.array([
            [1.0, 2.0, 4.0],
            [0.5, 1.0, 2.0],
            [0.25, 0.5, 1.0],
        ])
        weights = self.model.calculate_ahp_weights(matrix, ["a", "b", "c"])

        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        self.assertGreater(weights["a"], weights["b"])
        self.assertGreater(weights["b"], weights["c"])

    def test_ahp_rejects_bad_matrix(self):
        with self.assertRaises(ValueError):
            self.model.calculate_ahp_weights(
                np.array([[1.0, 3.0], [0.5, 1.0]]),
                ["a", "b"],
            )

    def test_entropy_weights_calculation(self):
        data = np.array([
            [10.0, 90.0, 100.0],
            [15.0, 85.0, 120.0],
            [8.0, 88.0, 75.0],
        ])
        weights = self.model.calculate_entropy_weights(
            data,
            ["tech_1", "tech_2", "safety_1"],
            benefit_flags=[False, True, False],
        )

        self.assertEqual(set(weights), {"tech_1", "tech_2", "safety_1"})
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        for weight in weights.values():
            self.assertGreaterEqual(weight, 0)

    def test_comprehensive_evaluation_uses_final_weights_once(self):
        result = self.model.calculate_evaluation(WeightMethod.EXPERT)

        self.assertIsInstance(result, EvaluationResult)
        self.assertEqual(len(result.indicator_results), 3)
        self.assertEqual(len(result.category_results), 2)

        expected = 85.0 * 0.3 + 85.0 * 0.3 + 95.0 * 0.4
        self.assertAlmostEqual(result.total_score, expected, places=6)
        self.assertEqual(result.final_grade, EvaluationGrade.GOOD)

    def test_edge_cases_single_indicator(self):
        model = EvaluationModel()
        model.set_indicators([self.indicators[0]])
        model.set_weights({"tech_1": 1.0})
        model.set_ranges({"tech_1": self.model.ranges["tech_1"]})
        model.set_measured_values({"tech_1": 8.0})

        result = model.calculate_evaluation(WeightMethod.EXPERT)
        self.assertEqual(len(result.indicator_results), 1)
        self.assertEqual(len(result.category_results), 1)


if __name__ == "__main__":
    unittest.main()
