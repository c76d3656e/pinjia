#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制器单元测试

测试评价控制器的业务逻辑功能。
包括指标管理、权重计算、评价执行等。

作者: 开发团队
版本: 1.0.0
"""

import unittest
import tempfile
import os
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from src.controllers.evaluation_controller import EvaluationController
from src.models.indicators import Indicator, IndicatorCategory
from src.models.evaluation import WeightMethod, EvaluationGrade


class TestEvaluationController(unittest.TestCase):
    """
    评价控制器测试
    
    测试EvaluationController类的核心功能。
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建测试用的控制器和数据。
        """
        self.controller = EvaluationController()
        
        # 创建测试指标数据
        self.test_indicators_data = {
            "categories": [
                {
                    "id": "technical",
                    "name": "技术指标",
                    "description": "爆破技术效果相关指标",
                    "weight": 0.6
                },
                {
                    "id": "safety",
                    "name": "安全指标",
                    "description": "爆破安全相关指标",
                    "weight": 0.4
                }
            ],
            "indicators": [
                {
                    "id": "tech_1",
                    "name": "大块率",
                    "unit": "%",
                    "description": "爆破后大块石料所占比例",
                    "is_positive": False,
                    "category_id": "technical",
                    "min_value": 0.0,
                    "max_value": 30.0,
                    "weight": 0.5
                },
                {
                    "id": "tech_2",
                    "name": "抛掷率",
                    "unit": "%",
                    "description": "爆破岩石抛掷到指定区域的比例",
                    "is_positive": True,
                    "category_id": "technical",
                    "min_value": 60.0,
                    "max_value": 95.0,
                    "weight": 0.5
                },
                {
                    "id": "safety_1",
                    "name": "飞石距离",
                    "unit": "m",
                    "description": "爆破产生的飞石最远距离",
                    "is_positive": False,
                    "category_id": "safety",
                    "min_value": 50.0,
                    "max_value": 200.0,
                    "weight": 1.0
                }
            ]
        }
        
        # 创建临时文件用于测试
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        json.dump(self.test_indicators_data, self.temp_file, ensure_ascii=False, indent=2)
        self.temp_file.close()
    
    def tearDown(self):
        """
        测试后清理
        
        删除临时文件。
        """
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_controller_initialization(self):
        """
        测试控制器初始化
        """
        self.assertIsNotNone(self.controller.model)
        self.assertIsNotNone(self.controller.indicator_manager)
        self.assertEqual(len(self.controller.selected_indicators), 0)
        self.assertFalse(self.controller.is_data_loaded)
    
    def test_load_indicators_success(self):
        """
        测试成功加载指标
        """
        success = self.controller.load_indicators(self.temp_file.name)
        
        self.assertTrue(success)
        self.assertTrue(self.controller.is_data_loaded)
        self.assertEqual(len(self.controller.get_all_categories()), 2)
        self.assertEqual(len(self.controller.get_all_indicators()), 3)
    
    def test_load_indicators_file_not_found(self):
        """
        测试加载不存在的文件
        """
        success = self.controller.load_indicators("nonexistent_file.json")
        
        self.assertFalse(success)
        self.assertFalse(self.controller.is_data_loaded)
    
    def test_load_indicators_invalid_json(self):
        """
        测试加载无效JSON文件
        """
        # 创建无效JSON文件
        invalid_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        invalid_file.write("invalid json content")
        invalid_file.close()
        
        try:
            success = self.controller.load_indicators(invalid_file.name)
            self.assertFalse(success)
            self.assertFalse(self.controller.is_data_loaded)
        finally:
            os.unlink(invalid_file.name)
    
    def test_get_categories_and_indicators(self):
        """
        测试获取分类和指标信息
        """
        self.controller.load_indicators(self.temp_file.name)
        
        # 测试获取所有分类
        categories = self.controller.get_all_categories()
        self.assertEqual(len(categories), 2)
        
        category_ids = [cat.id for cat in categories]
        self.assertIn("technical", category_ids)
        self.assertIn("safety", category_ids)
        
        # 测试获取所有指标
        indicators = self.controller.get_all_indicators()
        self.assertEqual(len(indicators), 3)
        
        indicator_ids = [ind.id for ind in indicators]
        self.assertIn("tech_1", indicator_ids)
        self.assertIn("tech_2", indicator_ids)
        self.assertIn("safety_1", indicator_ids)
        
        # 测试按分类获取指标
        tech_indicators = self.controller.get_indicators_by_category("technical")
        self.assertEqual(len(tech_indicators), 2)
        
        safety_indicators = self.controller.get_indicators_by_category("safety")
        self.assertEqual(len(safety_indicators), 1)
    
    def test_indicator_selection(self):
        """
        测试指标选择功能
        """
        self.controller.load_indicators(self.temp_file.name)
        
        # 测试更新选中指标
        selected_ids = ["tech_1", "safety_1"]
        self.controller.update_selected_indicators(selected_ids)
        
        self.assertEqual(len(self.controller.selected_indicators), 2)
        self.assertIn("tech_1", self.controller.selected_indicators)
        self.assertIn("safety_1", self.controller.selected_indicators)
        
        # 测试获取选中指标
        selected_indicators = self.controller.get_selected_indicators()
        self.assertEqual(len(selected_indicators), 2)
        
        selected_indicator_ids = [ind.id for ind in selected_indicators]
        self.assertIn("tech_1", selected_indicator_ids)
        self.assertIn("safety_1", selected_indicator_ids)
    
    def test_weight_management(self):
        """
        测试权重管理功能
        """
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2", "safety_1"])
        
        # 测试设置指标权重
        weights = {
            "tech_1": 0.3,
            "tech_2": 0.3,
            "safety_1": 0.4
        }
        success = self.controller.set_indicator_weights(weights)
        self.assertTrue(success)
        
        # 测试获取指标权重
        retrieved_weights = self.controller.get_indicator_weights()
        self.assertEqual(len(retrieved_weights), 3)
        self.assertEqual(retrieved_weights["tech_1"], 0.3)
        self.assertEqual(retrieved_weights["tech_2"], 0.3)
        self.assertEqual(retrieved_weights["safety_1"], 0.4)
        
        # 测试设置分类权重
        category_weights = {
            "technical": 0.6,
            "safety": 0.4
        }
        success = self.controller.set_category_weights(category_weights)
        self.assertTrue(success)
        
        # 测试获取分类权重
        retrieved_cat_weights = self.controller.get_category_weights()
        self.assertEqual(len(retrieved_cat_weights), 2)
        self.assertEqual(retrieved_cat_weights["technical"], 0.6)
        self.assertEqual(retrieved_cat_weights["safety"], 0.4)
    
    def test_weight_calculation_methods(self):
        """
        测试权重计算方法
        """
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2", "safety_1"])
        
        # 测试等权重计算
        weights = self.controller.calculate_weights(WeightMethod.EQUAL)
        self.assertEqual(len(weights), 3)
        
        # 验证等权重（每个权重应该约等于1/3）
        for weight in weights.values():
            self.assertAlmostEqual(weight, 1/3, places=5)
        
        # 测试专家打分权重（使用默认权重）
        weights = self.controller.calculate_weights(WeightMethod.EXPERT)
        self.assertEqual(len(weights), 3)
        
        # 验证权重和为1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # 测试AHP权重计算
        comparison_matrix = np.array([
            [1.0, 2.0, 3.0],
            [0.5, 1.0, 2.0],
            [1/3, 0.5, 1.0]
        ])
        
        weights = self.controller.calculate_weights(
            WeightMethod.AHP, 
            comparison_matrix=comparison_matrix
        )
        self.assertEqual(len(weights), 3)
        
        # 验证权重和为1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
    
    def test_range_management(self):
        """
        测试评价范围管理
        """
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2"])
        
        # 测试设置评价范围
        ranges = {
            "tech_1": {
                "excellent": (0, 5),
                "good": (5, 10),
                "average": (10, 20),
                "poor": (20, 30)
            },
            "tech_2": {
                "excellent": (90, 95),
                "good": (85, 89),
                "average": (75, 84),
                "poor": (60, 74)
            }
        }
        
        success = self.controller.set_evaluation_ranges(ranges)
        self.assertTrue(success)
        
        # 测试获取评价范围
        retrieved_ranges = self.controller.get_evaluation_ranges()
        self.assertEqual(len(retrieved_ranges), 2)
        self.assertIn("tech_1", retrieved_ranges)
        self.assertIn("tech_2", retrieved_ranges)
    
    def test_measured_values_management(self):
        """
        测试实测值管理
        """
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2", "safety_1"])
        
        # 测试设置实测值
        measured_values = {
            "tech_1": 8.0,
            "tech_2": 88.0,
            "safety_1": 75.0
        }
        
        success = self.controller.set_measured_values(measured_values)
        self.assertTrue(success)
        
        # 测试获取实测值
        retrieved_values = self.controller.get_measured_values()
        self.assertEqual(len(retrieved_values), 3)
        self.assertEqual(retrieved_values["tech_1"], 8.0)
        self.assertEqual(retrieved_values["tech_2"], 88.0)
        self.assertEqual(retrieved_values["safety_1"], 75.0)
    
    def test_evaluation_execution(self):
        """
        测试评价执行
        """
        # 准备完整的评价数据
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2", "safety_1"])
        
        # 设置权重
        weights = {"tech_1": 0.3, "tech_2": 0.3, "safety_1": 0.4}
        self.controller.set_indicator_weights(weights)
        
        category_weights = {"technical": 0.6, "safety": 0.4}
        self.controller.set_category_weights(category_weights)
        
        # 设置评价范围
        ranges = {
            "tech_1": {
                "excellent": (0, 5),
                "good": (5, 10),
                "average": (10, 20),
                "poor": (20, 30)
            },
            "tech_2": {
                "excellent": (90, 95),
                "good": (85, 89),
                "average": (75, 84),
                "poor": (60, 74)
            },
            "safety_1": {
                "excellent": (50, 80),
                "good": (80, 120),
                "average": (120, 160),
                "poor": (160, 200)
            }
        }
        self.controller.set_evaluation_ranges(ranges)
        
        # 设置实测值
        measured_values = {"tech_1": 8.0, "tech_2": 88.0, "safety_1": 75.0}
        self.controller.set_measured_values(measured_values)
        
        # 执行评价
        result = self.controller.execute_evaluation(WeightMethod.EXPERT)
        
        # 验证评价结果
        self.assertIsNotNone(result)
        self.assertEqual(len(result.indicator_results), 3)
        self.assertEqual(len(result.category_results), 2)
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)
        self.assertIsInstance(result.final_grade, EvaluationGrade)
        
        # 验证评价摘要
        summary = self.controller.get_evaluation_summary()
        self.assertIsNotNone(summary)
        self.assertGreater(len(summary), 0)
    
    def test_data_validation(self):
        """
        测试数据验证功能
        """
        # 测试空数据验证
        errors = self.controller.validate_evaluation_data()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("未加载指标数据" in error for error in errors))
        
        # 加载指标但不选择
        self.controller.load_indicators(self.temp_file.name)
        errors = self.controller.validate_evaluation_data()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("未选择评价指标" in error for error in errors))
        
        # 选择指标但不设置权重
        self.controller.update_selected_indicators(["tech_1", "tech_2"])
        errors = self.controller.validate_evaluation_data()
        self.assertGreater(len(errors), 0)
        
        # 设置完整数据
        weights = {"tech_1": 0.5, "tech_2": 0.5}
        self.controller.set_indicator_weights(weights)
        
        category_weights = {"technical": 1.0}
        self.controller.set_category_weights(category_weights)
        
        ranges = {
            "tech_1": {
                "excellent": (0, 5),
                "good": (5, 10),
                "average": (10, 20),
                "poor": (20, 30)
            },
            "tech_2": {
                "excellent": (90, 95),
                "good": (85, 89),
                "average": (75, 84),
                "poor": (60, 74)
            }
        }
        self.controller.set_evaluation_ranges(ranges)
        
        measured_values = {"tech_1": 8.0, "tech_2": 88.0}
        self.controller.set_measured_values(measured_values)
        
        # 验证完整数据
        errors = self.controller.validate_evaluation_data()
        self.assertEqual(len(errors), 0)
    
    def test_reset_functionality(self):
        """
        测试重置功能
        """
        # 设置一些数据
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2"])
        
        weights = {"tech_1": 0.5, "tech_2": 0.5}
        self.controller.set_indicator_weights(weights)
        
        # 验证数据已设置
        self.assertTrue(self.controller.is_data_loaded)
        self.assertEqual(len(self.controller.selected_indicators), 2)
        self.assertEqual(len(self.controller.get_indicator_weights()), 2)
        
        # 执行重置
        self.controller.reset()
        
        # 验证数据已清空
        self.assertFalse(self.controller.is_data_loaded)
        self.assertEqual(len(self.controller.selected_indicators), 0)
        self.assertEqual(len(self.controller.get_indicator_weights()), 0)
        self.assertEqual(len(self.controller.get_category_weights()), 0)
        self.assertEqual(len(self.controller.get_evaluation_ranges()), 0)
        self.assertEqual(len(self.controller.get_measured_values()), 0)
    
    def test_export_import_functionality(self):
        """
        测试导出导入功能
        """
        # 准备评价数据
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2"])
        
        weights = {"tech_1": 0.6, "tech_2": 0.4}
        self.controller.set_indicator_weights(weights)
        
        category_weights = {"technical": 1.0}
        self.controller.set_category_weights(category_weights)
        
        measured_values = {"tech_1": 8.0, "tech_2": 88.0}
        self.controller.set_measured_values(measured_values)
        
        # 导出评价数据
        export_data = self.controller.export_evaluation_data()
        
        # 验证导出数据结构
        self.assertIn("selected_indicators", export_data)
        self.assertIn("indicator_weights", export_data)
        self.assertIn("category_weights", export_data)
        self.assertIn("measured_values", export_data)
        self.assertIn("export_time", export_data)
        
        # 验证导出数据内容
        self.assertEqual(len(export_data["selected_indicators"]), 2)
        self.assertEqual(export_data["indicator_weights"]["tech_1"], 0.6)
        self.assertEqual(export_data["measured_values"]["tech_2"], 88.0)
        
        # 重置控制器
        self.controller.reset()
        self.controller.load_indicators(self.temp_file.name)
        
        # 导入评价数据
        success = self.controller.import_evaluation_data(export_data)
        self.assertTrue(success)
        
        # 验证导入后的数据
        self.assertEqual(len(self.controller.selected_indicators), 2)
        self.assertEqual(self.controller.get_indicator_weights()["tech_1"], 0.6)
        self.assertEqual(self.controller.get_measured_values()["tech_2"], 88.0)
    
    def test_error_handling(self):
        """
        测试错误处理
        """
        # 测试在未加载数据时执行操作
        success = self.controller.set_indicator_weights({"test": 0.5})
        self.assertFalse(success)
        
        success = self.controller.set_measured_values({"test": 10.0})
        self.assertFalse(success)
        
        result = self.controller.execute_evaluation(WeightMethod.EXPERT)
        self.assertIsNone(result)
        
        # 测试无效权重
        self.controller.load_indicators(self.temp_file.name)
        self.controller.update_selected_indicators(["tech_1", "tech_2"])
        
        # 权重和不为1
        invalid_weights = {"tech_1": 0.3, "tech_2": 0.3}  # 和为0.6
        success = self.controller.set_indicator_weights(invalid_weights)
        self.assertFalse(success)
        
        # 包含未选择的指标
        invalid_weights = {"tech_1": 0.5, "tech_2": 0.3, "safety_1": 0.2}
        success = self.controller.set_indicator_weights(invalid_weights)
        self.assertFalse(success)
    
    def test_edge_cases(self):
        """
        测试边界情况
        """
        self.controller.load_indicators(self.temp_file.name)
        
        # 测试选择所有指标
        all_indicator_ids = [ind.id for ind in self.controller.get_all_indicators()]
        self.controller.update_selected_indicators(all_indicator_ids)
        self.assertEqual(len(self.controller.selected_indicators), 3)
        
        # 测试选择单个指标
        self.controller.update_selected_indicators(["tech_1"])
        self.assertEqual(len(self.controller.selected_indicators), 1)
        
        # 测试空选择
        self.controller.update_selected_indicators([])
        self.assertEqual(len(self.controller.selected_indicators), 0)
        
        # 测试选择不存在的指标
        self.controller.update_selected_indicators(["nonexistent_indicator"])
        self.assertEqual(len(self.controller.selected_indicators), 0)


if __name__ == '__main__':
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestEvaluationController))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    print(f"\n测试完成:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")