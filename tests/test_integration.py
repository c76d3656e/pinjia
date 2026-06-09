#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.abspath("src"))

from src.controllers.evaluation_controller import EvaluationController
from models.evaluation import EvaluationGrade
from src.utils.config import ConfigManager
from src.utils.logger import setup_logger
from src.utils.report_generator import ReportConfig, ReportGenerator


class TestSystemIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.indicators_file = os.path.join(self.temp_dir, "indicators.json")
        data = {
            "categories": [
                {
                    "id": "technical",
                    "name": "技术指标",
                    "indicators": [
                        {"id": "tech_1", "name": "大块率", "unit": "%", "is_positive": False, "min_value": 0, "max_value": 30},
                        {"id": "tech_2", "name": "抛掷率", "unit": "%", "is_positive": True, "min_value": 60, "max_value": 95},
                    ],
                },
                {
                    "id": "safety",
                    "name": "安全指标",
                    "indicators": [
                        {"id": "safety_1", "name": "飞石距离", "unit": "m", "is_positive": False, "min_value": 50, "max_value": 200}
                    ],
                },
            ]
        }
        with open(self.indicators_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.controller = EvaluationController(self.indicators_file)
        self.report_generator = ReportGenerator(ReportConfig(project_name="集成测试项目", project_location="测试矿山"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def prepare_complete_evaluation(self):
        self.controller.load_indicators()
        self.controller.update_selected_indicators(["tech_1", "tech_2", "safety_1"])
        self.controller.set_indicator_weights({"tech_1": 0.3, "tech_2": 0.3, "safety_1": 0.4})
        self.controller.set_indicator_ranges({
            "tech_1": {"excellent": (0, 5), "good": (5, 10), "average": (10, 20), "poor": (20, 30)},
            "tech_2": {"excellent": (90, 95), "good": (85, 89), "average": (75, 84), "poor": (60, 74)},
            "safety_1": {"excellent": (50, 80), "good": (80, 120), "average": (120, 160), "poor": (160, 200)},
        })
        self.controller.set_measured_values({"tech_1": 8, "tech_2": 88, "safety_1": 75})

    def test_complete_evaluation_workflow(self):
        self.prepare_complete_evaluation()

        errors = self.controller.validate_evaluation_data()
        self.assertEqual(errors, [])

        result = self.controller.calculate_evaluation("Expert")
        self.assertIsInstance(result.final_grade, EvaluationGrade)
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)

        indicators = self.controller.get_all_indicators()
        categories = self.controller.get_indicator_categories()
        text_report = self.report_generator.generate_text_report(result, indicators, categories)
        html_report = self.report_generator.generate_html_report(result, indicators, categories)
        json_report = self.report_generator.generate_json_report(result, indicators, categories)

        self.assertIn("集成测试项目", text_report)
        self.assertIn("<html", html_report)
        self.assertIn("evaluation_summary", json.loads(json_report))

        exported = self.controller.export_evaluation_data()
        self.controller.reset_evaluation_data()
        self.assertIn("weights", exported)
        self.assertEqual(self.controller.selected_indicators, [])

    def test_error_handling(self):
        controller = EvaluationController(os.path.join(self.temp_dir, "missing.json"))
        controller.load_indicators()
        self.assertGreater(len(controller.get_all_indicators()), 0)

        self.controller.load_indicators()
        self.controller.update_selected_indicators(["tech_1"])
        self.assertGreater(len(self.controller.validate_evaluation_data()), 0)
        with self.assertRaises(ValueError):
            self.controller.calculate_evaluation("Expert")

    def test_configuration_and_logging(self):
        config_path = os.path.join(self.temp_dir, "settings.ini")
        config = ConfigManager(config_path)
        config.set("App", "Title", "集成测试应用")
        config.save()
        config.reload()
        self.assertEqual(config.get("App", "Title"), "集成测试应用")
        self.assertTrue(config.validate_config())

        log_file = os.path.join(self.temp_dir, "test.log")
        logger = setup_logger(
            name="integration_test",
            level="DEBUG",
            log_to_file=True,
            log_to_console=False,
            log_file=log_file,
        )
        logger.info("加载指标数据")
        self.assertTrue(os.path.exists(log_file))

    def test_performance_smoke(self):
        start = time.time()
        self.prepare_complete_evaluation()
        result = self.controller.calculate_evaluation("Expert")
        elapsed = time.time() - start

        self.assertLess(elapsed, 2.0)
        self.assertGreater(result.total_score, 0)


if __name__ == "__main__":
    unittest.main()
