#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath("src"))

from models.evaluation import EvaluationModel, EvaluationRange, WeightMethod, EvaluationGrade
from models.indicators import Indicator, IndicatorCategory
from src.utils.config import ConfigManager
from src.utils.logger import setup_logger, get_logger, set_log_level, LoggerMixin, log_function_call, log_exception, ContextLogger
from src.utils.report_generator import ReportConfig, ReportGenerator


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False)
        self.temp_file.close()
        os.unlink(self.temp_file.name)
        self.config = ConfigManager(self.temp_file.name)

    def tearDown(self):
        path = Path(self.temp_file.name)
        if path.exists():
            path.unlink()

    def test_config_lifecycle(self):
        self.assertEqual(str(self.config.config_file), self.temp_file.name)
        self.assertTrue(self.config.has_section("App"))

        self.config.set("App", "Title", "测试应用")
        self.assertEqual(self.config.get("App", "Title"), "测试应用")
        self.assertIsInstance(self.config.getint("Server", "Port"), int)
        self.assertIsInstance(self.config.getboolean("UI", "ShowProgress"), bool)

        self.config.save()
        reloaded = ConfigManager(self.temp_file.name)
        self.assertEqual(reloaded.get("App", "Title"), "测试应用")
        self.assertTrue(reloaded.validate_config())

    def test_missing_option_fallback(self):
        self.assertEqual(self.config.get("Missing", "Key", "fallback"), "fallback")
        self.assertEqual(self.config.getint("Missing", "Key", 7), 7)


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")

    def tearDown(self):
        for name in ["test_logger", "decorator_test", "exception_test"]:
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()
        if os.path.exists(self.log_file):
            os.unlink(self.log_file)
        os.rmdir(self.temp_dir)

    def test_setup_and_get_logger(self):
        logger = setup_logger(
            name="test_logger",
            level="DEBUG",
            log_to_file=True,
            log_to_console=False,
            log_file=self.log_file,
        )
        logger.debug("debug message")

        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(os.path.exists(self.log_file))
        self.assertIs(get_logger("test_logger"), logger)

    def test_set_log_level_sets_root(self):
        set_log_level("WARNING")
        self.assertEqual(logging.getLogger().level, logging.WARNING)

    def test_logger_mixin_and_context_logger(self):
        class Example(LoggerMixin):
            pass

        obj = Example()
        self.assertIsInstance(obj.logger, logging.Logger)

        context = ContextLogger(obj.logger, "ctx")
        context.info("message")

    def test_decorators(self):
        logger = logging.getLogger("exception_test")

        @log_function_call
        def add(a, b):
            return a + b

        @log_exception(logger, "failed")
        def fail():
            raise ValueError("boom")

        self.assertEqual(add(1, 2), 3)
        with self.assertRaises(ValueError):
            fail()


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.indicators = [
            Indicator("tech_1", "大块率", "%", category_id="technical"),
            Indicator("safety_1", "飞石距离", "m", category_id="safety"),
        ]
        self.categories = [
            IndicatorCategory("technical", "技术指标", indicators=[self.indicators[0]]),
            IndicatorCategory("safety", "安全指标", indicators=[self.indicators[1]]),
        ]
        model = EvaluationModel()
        model.set_indicators(self.indicators)
        model.set_weights({"tech_1": 0.4, "safety_1": 0.6})
        model.set_ranges({
            "tech_1": EvaluationRange((0, 5), (5, 10), (10, 20), (20, 30)),
            "safety_1": EvaluationRange((50, 80), (80, 120), (120, 160), (160, 200)),
        })
        model.set_measured_values({"tech_1": 8, "safety_1": 75})
        self.result = model.calculate_evaluation(WeightMethod.EXPERT)
        self.generator = ReportGenerator(ReportConfig(project_name="测试项目", project_location="测试地点"))

    def test_generate_reports(self):
        text = self.generator.generate_text_report(self.result, self.indicators, self.categories)
        html = self.generator.generate_html_report(self.result, self.indicators, self.categories)
        json_report = self.generator.generate_json_report(self.result, self.indicators, self.categories)

        self.assertIn("测试项目", text)
        self.assertIn("<html", html)
        data = json.loads(json_report)
        self.assertEqual(data["report_info"]["project_name"], "测试项目")
        self.assertIn("indicator_results", data)

    def test_recommendations(self):
        recommendations = self.generator._generate_recommendations(self.result)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    def test_grade_description(self):
        self.assertEqual(self.generator._get_grade_description(EvaluationGrade.GOOD), "良好")


if __name__ == "__main__":
    unittest.main()
