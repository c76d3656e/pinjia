#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import unittest
from pathlib import Path

from src.models.indicators import Indicator, IndicatorCategory, IndicatorManager


class TestIndicator(unittest.TestCase):
    def setUp(self):
        self.indicator = Indicator(
            id="test_1",
            name="测试指标",
            unit="%",
            description="测试",
            is_positive=True,
            category_id="cat",
            min_value=0.0,
            max_value=100.0,
            default_weight=0.2,
        )

    def test_indicator_creation_and_validation(self):
        self.assertEqual(self.indicator.id, "test_1")
        self.assertEqual(self.indicator.name, "测试指标")

        with self.assertRaises(ValueError):
            Indicator(id="", name="测试")
        with self.assertRaises(ValueError):
            Indicator(id="x", name="")
        with self.assertRaises(ValueError):
            Indicator(id="x", name="测试", min_value=10, max_value=1)
        with self.assertRaises(ValueError):
            Indicator(id="x", name="测试", default_weight=1.5)

    def test_serialization(self):
        data = self.indicator.to_dict()
        restored = Indicator.from_dict(data)

        self.assertEqual(restored.id, self.indicator.id)
        self.assertEqual(restored.is_positive, self.indicator.is_positive)
        self.assertEqual(restored.default_weight, self.indicator.default_weight)

    def test_validate_value_and_normalize(self):
        self.assertTrue(self.indicator.validate_value(50))
        self.assertFalse(self.indicator.validate_value(-1))
        self.assertFalse(self.indicator.validate_value(101))

        self.assertAlmostEqual(self.indicator.normalize_value(0), 0.0)
        self.assertAlmostEqual(self.indicator.normalize_value(50), 0.5)
        self.assertAlmostEqual(self.indicator.normalize_value(100), 1.0)

        negative = Indicator("neg", "反向", is_positive=False, min_value=0, max_value=100)
        # 当前标准化函数只做线性映射，不按方向反转；反向处理在评分/熵权中完成。
        self.assertAlmostEqual(negative.normalize_value(0), 0.0)
        self.assertAlmostEqual(negative.normalize_value(100), 1.0)


class TestIndicatorCategory(unittest.TestCase):
    def setUp(self):
        self.category = IndicatorCategory("cat", "分类", default_weight=0.5)
        self.indicator = Indicator("i1", "指标1")

    def test_category_creation_and_validation(self):
        self.assertEqual(self.category.id, "cat")
        self.assertEqual(self.category.get_indicator_count(), 0)

        with self.assertRaises(ValueError):
            IndicatorCategory("", "分类")
        with self.assertRaises(ValueError):
            IndicatorCategory("cat", "")
        with self.assertRaises(ValueError):
            IndicatorCategory("cat", "分类", default_weight=-0.1)

    def test_indicator_management(self):
        self.category.add_indicator(self.indicator)
        self.assertEqual(self.category.get_indicator_count(), 1)
        self.assertEqual(self.indicator.category_id, "cat")

        with self.assertRaises(ValueError):
            self.category.add_indicator(self.indicator)

        self.assertIs(self.category.get_indicator("i1"), self.indicator)
        self.assertIsNone(self.category.get_indicator("missing"))
        self.assertTrue(self.category.remove_indicator("i1"))
        self.assertFalse(self.category.remove_indicator("missing"))

    def test_serialization(self):
        self.category.add_indicator(self.indicator)
        data = self.category.to_dict()
        restored = IndicatorCategory.from_dict(data)

        self.assertEqual(restored.id, "cat")
        self.assertEqual(len(restored.indicators), 1)
        self.assertEqual(restored.indicators[0].category_id, "cat")


class TestIndicatorManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        self.manager = IndicatorManager(self.temp_file_path)

        self.category = IndicatorCategory("cat", "分类")
        self.indicator = Indicator("i1", "指标1")

    def tearDown(self):
        path = Path(self.temp_file_path)
        if path.exists():
            path.unlink()

    def test_manager_creation(self):
        self.assertEqual(str(self.manager.config_file), self.temp_file_path)
        self.assertEqual(self.manager.categories, [])

    def test_category_and_indicator_access(self):
        self.category.add_indicator(self.indicator)
        self.manager.add_category(self.category)

        self.assertEqual(self.manager.get_category("cat"), self.category)
        self.assertEqual(self.manager.get_indicator("i1"), self.indicator)
        self.assertEqual(self.manager.get_indicators_by_category("cat"), [self.indicator])
        self.assertEqual(self.manager.get_all_indicators(), [self.indicator])

        with self.assertRaises(ValueError):
            self.manager.add_category(self.category)

        self.assertTrue(self.manager.remove_category("cat"))
        self.assertFalse(self.manager.remove_category("missing"))

    def test_file_operations(self):
        self.category.add_indicator(self.indicator)
        self.manager.add_category(self.category)
        self.manager.save_to_file()

        with open(self.temp_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("categories", data)

        new_manager = IndicatorManager(self.temp_file_path)
        new_manager.load_from_file()
        self.assertEqual(len(new_manager.categories), 1)
        self.assertIsNotNone(new_manager.get_indicator("i1"))

    def test_validation_and_load_errors(self):
        self.category.add_indicator(self.indicator)
        self.manager.add_category(self.category)
        self.assertEqual(self.manager.validate_indicators(), [])

        empty = IndicatorCategory("empty", "空分类")
        self.manager.add_category(empty)
        self.assertTrue(any("没有指标" in error for error in self.manager.validate_indicators()))

        Path(self.temp_file_path).unlink()
        with self.assertRaises(FileNotFoundError):
            self.manager.load_from_file()

        Path(self.temp_file_path).write_text("invalid json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.manager.load_from_file()


if __name__ == "__main__":
    unittest.main()
