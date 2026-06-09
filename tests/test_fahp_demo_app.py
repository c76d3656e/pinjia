#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAHP计算专项测试。
"""

import unittest

from demo_app import app, app_state, calculate_fahp_weights


class TestFAHPDemoApp(unittest.TestCase):
    def test_fahp_weights_use_fuzzy_complementary_formula(self):
        matrix = [
            [0.5, 0.6, 0.7],
            [0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5],
        ]

        weights, ci = calculate_fahp_weights(matrix)

        self.assertIsNotNone(weights)
        self.assertAlmostEqual(sum(weights), 1.0, places=6)
        self.assertAlmostEqual(weights[0], 0.3833333333, places=6)
        self.assertAlmostEqual(weights[1], 0.3333333333, places=6)
        self.assertAlmostEqual(weights[2], 0.2833333333, places=6)
        self.assertGreaterEqual(ci, 0.0)

    def test_fahp_final_weights_respect_level1_category_order(self):
        original_selected = app_state["selected_indicators"]
        original_weights = app_state["weights"]
        try:
            app_state["selected_indicators"] = [
                {"id": "technical_1", "name": "大块率"},
                {"id": "technical_2", "name": "根底率"},
                {"id": "economic_1", "name": "炸药单耗"},
                {"id": "economic_2", "name": "延米爆破量"},
            ]
            app_state["weights"] = {}

            payload = {
                "method": "fahp",
                "level1_categories": ["technical", "economic"],
                "level1_matrix": [
                    [0.5, 0.7],
                    [0.3, 0.5],
                ],
                "level2_matrices": {
                    "technical": [
                        [0.5, 0.6],
                        [0.4, 0.5],
                    ],
                    "economic": [
                        [0.5, 0.8],
                        [0.2, 0.5],
                    ],
                },
            }

            with app.test_client() as client:
                response = client.post("/api/weights/calculate", json=payload)

            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"], data.get("message"))

            weights = data["data"]
            self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
            self.assertAlmostEqual(weights["technical_1"], 0.33, places=6)
            self.assertAlmostEqual(weights["technical_2"], 0.27, places=6)
            self.assertAlmostEqual(weights["economic_1"], 0.26, places=6)
            self.assertAlmostEqual(weights["economic_2"], 0.14, places=6)
        finally:
            app_state["selected_indicators"] = original_selected
            app_state["weights"] = original_weights

    def test_fahp_accepts_closed_zero_to_one_range(self):
        matrix = [
            [0.5, 0.97, 1.0],
            [0.03, 0.5, 0.9],
            [0.0, 0.1, 0.5],
        ]

        weights, ci = calculate_fahp_weights(matrix)

        self.assertIsNotNone(weights)
        self.assertAlmostEqual(sum(weights), 1.0, places=6)
        self.assertGreater(weights[0], weights[1])
        self.assertGreater(weights[1], weights[2])
        self.assertGreaterEqual(ci, 0.0)


if __name__ == "__main__":
    unittest.main()
