#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评价模型单元测试

测试评价相关的数据模型和计算功能。
包括评价模型、权重计算、综合评价等。

作者: 开发团队
版本: 1.0.0
"""

import unittest
import numpy as np
from typing import Dict, List

from src.models.evaluation import (
    EvaluationModel, EvaluationResult, EvaluationRange,
    IndicatorResult, CategoryResult, WeightMethod, EvaluationGrade
)
from src.models.indicators import Indicator, IndicatorCategory


class TestEvaluationRange(unittest.TestCase):
    """
    评价范围测试
    
    测试EvaluationRange类的功能。
    """
    
    def setUp(self):
        """
        测试前准备
        """
        self.eval_range = EvaluationRange(
            excellent=(90, 100),
            good=(80, 89),
            average=(70, 79),
            poor=(0, 69)
        )
    
    def test_range_creation(self):
        """
        测试范围创建
        """
        self.assertEqual(self.eval_range.excellent, (90, 100))
        self.assertEqual(self.eval_range.good, (80, 89))
        self.assertEqual(self.eval_range.average, (70, 79))
        self.assertEqual(self.eval_range.poor, (0, 69))
    
    def test_get_grade(self):
        """
        测试等级判定
        """
        self.assertEqual(self.eval_range.get_grade(95), EvaluationGrade.EXCELLENT)
        self.assertEqual(self.eval_range.get_grade(85), EvaluationGrade.GOOD)
        self.assertEqual(self.eval_range.get_grade(75), EvaluationGrade.AVERAGE)
        self.assertEqual(self.eval_range.get_grade(65), EvaluationGrade.POOR)
        
        # 边界值测试
        self.assertEqual(self.eval_range.get_grade(90), EvaluationGrade.EXCELLENT)
        self.assertEqual(self.eval_range.get_grade(89), EvaluationGrade.GOOD)
        self.assertEqual(self.eval_range.get_grade(80), EvaluationGrade.GOOD)
        self.assertEqual(self.eval_range.get_grade(79), EvaluationGrade.AVERAGE)
    
    def test_range_validation(self):
        """
        测试范围验证
        """
        errors = self.eval_range.validate()
        self.assertEqual(len(errors), 0)
        
        # 测试无效范围
        invalid_range = EvaluationRange(
            excellent=(100, 90),  # 最小值大于最大值
            good=(80, 89),
            average=(70, 79),
            poor=(0, 69)
        )
        errors = invalid_range.validate()
        self.assertGreater(len(errors), 0)


class TestIndicatorResult(unittest.TestCase):
    """
    指标结果测试
    
    测试IndicatorResult类的功能。
    """
    
    def test_result_creation(self):
        """
        测试结果创建
        """
        result = IndicatorResult(
            indicator_id="test_1",
            measured_value=85.0,
            normalized_value=0.85,
            score=85.0,
            grade=EvaluationGrade.GOOD,
            weight=0.2
        )
        
        self.assertEqual(result.indicator_id, "test_1")
        self.assertEqual(result.measured_value, 85.0)
        self.assertEqual(result.normalized_value, 0.85)
        self.assertEqual(result.score, 85.0)
        self.assertEqual(result.grade, EvaluationGrade.GOOD)
        self.assertEqual(result.weight, 0.2)
    
    def test_weighted_score(self):
        """
        测试加权得分计算
        """
        result = IndicatorResult(
            indicator_id="test_1",
            measured_value=80.0,
            normalized_value=0.8,
            score=80.0,
            grade=EvaluationGrade.GOOD,
            weight=0.3
        )
        
        expected_weighted_score = 80.0 * 0.3
        self.assertAlmostEqual(result.get_weighted_score(), expected_weighted_score)


class TestCategoryResult(unittest.TestCase):
    """
    分类结果测试
    
    测试CategoryResult类的功能。
    """
    
    def test_category_result_creation(self):
        """
        测试分类结果创建
        """
        indicator_results = [
            IndicatorResult("ind_1", 80.0, 0.8, 80.0, EvaluationGrade.GOOD, 0.5),
            IndicatorResult("ind_2", 90.0, 0.9, 90.0, EvaluationGrade.EXCELLENT, 0.5)
        ]
        
        category_result = CategoryResult(
            category_id="test_category",
            score=85.0,
            grade=EvaluationGrade.GOOD,
            weight=0.4,
            indicator_results=indicator_results
        )
        
        self.assertEqual(category_result.category_id, "test_category")
        self.assertEqual(category_result.score, 85.0)
        self.assertEqual(category_result.grade, EvaluationGrade.GOOD)
        self.assertEqual(category_result.weight, 0.4)
        self.assertEqual(len(category_result.indicator_results), 2)
    
    def test_weighted_score(self):
        """
        测试分类加权得分计算
        """
        category_result = CategoryResult(
            category_id="test_category",
            score=85.0,
            grade=EvaluationGrade.GOOD,
            weight=0.3,
            indicator_results=[]
        )
        
        expected_weighted_score = 85.0 * 0.3
        self.assertAlmostEqual(category_result.get_weighted_score(), expected_weighted_score)


class TestEvaluationModel(unittest.TestCase):
    """
    评价模型测试
    
    测试EvaluationModel类的核心功能。
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建测试用的指标和评价模型。
        """
        # 创建测试指标
        self.indicators = [
            Indicator(
                id="tech_1",
                name="大块率",
                unit="%",
                description="爆破后大块石料所占比例",
                is_positive=False,  # 反向指标
                category_id="technical",
                min_value=0.0,
                max_value=30.0
            ),
            Indicator(
                id="tech_2",
                name="抛掷率",
                unit="%",
                description="爆破岩石抛掷到指定区域的比例",
                is_positive=True,  # 正向指标
                category_id="technical",
                min_value=60.0,
                max_value=95.0
            ),
            Indicator(
                id="safety_1",
                name="飞石距离",
                unit="m",
                description="爆破产生的飞石最远距离",
                is_positive=False,  # 反向指标
                category_id="safety",
                min_value=50.0,
                max_value=200.0
            )
        ]
        
        # 创建评价模型
        self.model = EvaluationModel()
        self.model.set_indicators(self.indicators)
        
        # 设置权重
        self.weights = {
            "tech_1": 0.3,
            "tech_2": 0.3,
            "safety_1": 0.4
        }
        self.model.set_weights(self.weights)
        
        # 设置分类权重
        self.category_weights = {
            "technical": 0.6,
            "safety": 0.4
        }
        self.model.set_category_weights(self.category_weights)
        
        # 设置评价范围
        self.ranges = {
            "tech_1": EvaluationRange((0, 5), (5, 10), (10, 20), (20, 30)),
            "tech_2": EvaluationRange((90, 95), (85, 89), (75, 84), (60, 74)),
            "safety_1": EvaluationRange((50, 80), (80, 120), (120, 160), (160, 200))
        }
        self.model.set_ranges(self.ranges)
        
        # 设置实测值
        self.measured_values = {
            "tech_1": 8.0,   # 一般等级
            "tech_2": 88.0,  # 良好等级
            "safety_1": 75.0  # 优秀等级
        }
        self.model.set_measured_values(self.measured_values)
    
    def test_model_initialization(self):
        """
        测试模型初始化
        """
        model = EvaluationModel()
        self.assertEqual(len(model.indicators), 0)
        self.assertEqual(len(model.weights), 0)
        self.assertEqual(len(model.category_weights), 0)
        self.assertEqual(len(model.ranges), 0)
        self.assertEqual(len(model.measured_values), 0)
    
    def test_set_indicators(self):
        """
        测试设置指标
        """
        self.assertEqual(len(self.model.indicators), 3)
        self.assertEqual(self.model.indicators[0].id, "tech_1")
        self.assertEqual(self.model.indicators[1].id, "tech_2")
        self.assertEqual(self.model.indicators[2].id, "safety_1")
    
    def test_set_weights(self):
        """
        测试设置权重
        """
        self.assertEqual(len(self.model.weights), 3)
        self.assertEqual(self.model.weights["tech_1"], 0.3)
        self.assertEqual(self.model.weights["tech_2"], 0.3)
        self.assertEqual(self.model.weights["safety_1"], 0.4)
    
    def test_set_ranges(self):
        """
        测试设置范围
        """
        self.assertEqual(len(self.model.ranges), 3)
        self.assertIn("tech_1", self.model.ranges)
        self.assertIn("tech_2", self.model.ranges)
        self.assertIn("safety_1", self.model.ranges)
    
    def test_set_measured_values(self):
        """
        测试设置实测值
        """
        self.assertEqual(len(self.model.measured_values), 3)
        self.assertEqual(self.model.measured_values["tech_1"], 8.0)
        self.assertEqual(self.model.measured_values["tech_2"], 88.0)
        self.assertEqual(self.model.measured_values["safety_1"], 75.0)
    
    def test_data_validation(self):
        """
        测试数据验证
        """
        # 测试完整数据
        errors = self.model.validate_data()
        self.assertEqual(len(errors), 0)
        
        # 测试缺少指标
        model_no_indicators = EvaluationModel()
        errors = model_no_indicators.validate_data()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("未设置评价指标" in error for error in errors))
        
        # 测试缺少权重
        model_no_weights = EvaluationModel()
        model_no_weights.set_indicators(self.indicators)
        errors = model_no_weights.validate_data()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("未设置指标权重" in error for error in errors))
    
    def test_ahp_weights_calculation(self):
        """
        测试AHP权重计算
        """
        # 创建3x3判断矩阵
        comparison_matrix = np.array([
            [1.0, 2.0, 3.0],
            [0.5, 1.0, 2.0],
            [1/3, 0.5, 1.0]
        ])
        
        indicator_ids = ["tech_1", "tech_2", "safety_1"]
        weights = self.model.calculate_ahp_weights(comparison_matrix, indicator_ids)
        
        # 验证权重
        self.assertEqual(len(weights), 3)
        self.assertIn("tech_1", weights)
        self.assertIn("tech_2", weights)
        self.assertIn("safety_1", weights)
        
        # 验证权重和为1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # 验证权重大小关系（tech_1 > tech_2 > safety_1）
        self.assertGreater(weights["tech_1"], weights["tech_2"])
        self.assertGreater(weights["tech_2"], weights["safety_1"])
    
    def test_entropy_weights_calculation(self):
        """
        测试熵权法权重计算
        """
        # 创建测试数据矩阵 (5个样本, 3个指标)
        data_matrix = np.array([
            [10.0, 85.0, 100.0],
            [15.0, 90.0, 120.0],
            [8.0, 88.0, 75.0],
            [12.0, 82.0, 110.0],
            [6.0, 92.0, 95.0]
        ])
        
        indicator_ids = ["tech_1", "tech_2", "safety_1"]
        weights = self.model.calculate_entropy_weights(data_matrix, indicator_ids)
        
        # 验证权重
        self.assertEqual(len(weights), 3)
        self.assertIn("tech_1", weights)
        self.assertIn("tech_2", weights)
        self.assertIn("safety_1", weights)
        
        # 验证权重和为1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # 验证权重为正数
        for weight in weights.values():
            self.assertGreater(weight, 0)
    
    def test_calculate_indicator_score(self):
        """
        测试指标得分计算
        """
        # 测试正向指标 (tech_2: 抛掷率)
        indicator = self.indicators[1]  # tech_2
        measured_value = 88.0
        eval_range = self.ranges["tech_2"]
        
        score = self.model._calculate_indicator_score(
            indicator, measured_value, eval_range
        )
        
        # 88分应该在良好等级范围内
        self.assertGreaterEqual(score, 80)
        self.assertLessEqual(score, 89)
        
        # 测试反向指标 (tech_1: 大块率)
        indicator = self.indicators[0]  # tech_1
        measured_value = 8.0
        eval_range = self.ranges["tech_1"]
        
        score = self.model._calculate_indicator_score(
            indicator, measured_value, eval_range
        )
        
        # 8%大块率应该在一般等级范围内
        self.assertGreaterEqual(score, 70)
        self.assertLessEqual(score, 79)
    
    def test_comprehensive_evaluation(self):
        """
        测试综合评价计算
        """
        result = self.model.calculate_evaluation(WeightMethod.EXPERT)
        
        # 验证结果结构
        self.assertIsInstance(result, EvaluationResult)
        self.assertEqual(len(result.indicator_results), 3)
        self.assertEqual(len(result.category_results), 2)  # technical, safety
        
        # 验证总分范围
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)
        
        # 验证等级
        self.assertIsInstance(result.final_grade, EvaluationGrade)
        
        # 验证指标结果
        for ind_result in result.indicator_results:
            self.assertIsInstance(ind_result, IndicatorResult)
            self.assertIn(ind_result.indicator_id, ["tech_1", "tech_2", "safety_1"])
            self.assertGreaterEqual(ind_result.score, 0)
            self.assertLessEqual(ind_result.score, 100)
        
        # 验证分类结果
        for cat_result in result.category_results:
            self.assertIsInstance(cat_result, CategoryResult)
            self.assertIn(cat_result.category_id, ["technical", "safety"])
            self.assertGreaterEqual(cat_result.score, 0)
            self.assertLessEqual(cat_result.score, 100)
    
    def test_evaluation_with_different_methods(self):
        """
        测试不同权重方法的评价
        """
        # 测试专家打分法
        result_expert = self.model.calculate_evaluation(WeightMethod.EXPERT)
        self.assertIsInstance(result_expert, EvaluationResult)
        self.assertEqual(result_expert.weight_method, WeightMethod.EXPERT)
        
        # 测试等权重法
        result_equal = self.model.calculate_evaluation(WeightMethod.EQUAL)
        self.assertIsInstance(result_equal, EvaluationResult)
        self.assertEqual(result_equal.weight_method, WeightMethod.EQUAL)
        
        # 验证不同方法的结果可能不同
        # (除非所有权重都相等，否则结果应该不同)
        if not all(w == 1/3 for w in self.weights.values()):
            self.assertNotAlmostEqual(
                result_expert.total_score, 
                result_equal.total_score,
                places=1
            )
    
    def test_evaluation_summary_generation(self):
        """
        测试评价总结生成
        """
        result = self.model.calculate_evaluation(WeightMethod.EXPERT)
        
        # 验证总结不为空
        self.assertIsNotNone(result.summary)
        self.assertGreater(len(result.summary), 0)
        
        # 验证总结包含关键信息
        summary = result.summary.lower()
        self.assertIn("评价", result.summary)
        
        # 根据得分验证总结内容
        if result.total_score >= 90:
            self.assertIn("优秀", result.summary)
        elif result.total_score >= 80:
            self.assertIn("良好", result.summary)
        elif result.total_score >= 70:
            self.assertIn("一般", result.summary)
        else:
            self.assertIn("较差", result.summary)
    
    def test_edge_cases(self):
        """
        测试边界情况
        """
        # 测试单个指标
        single_indicator = [self.indicators[0]]
        model = EvaluationModel()
        model.set_indicators(single_indicator)
        model.set_weights({"tech_1": 1.0})
        model.set_category_weights({"technical": 1.0})
        model.set_ranges({"tech_1": self.ranges["tech_1"]})
        model.set_measured_values({"tech_1": 8.0})
        
        result = model.calculate_evaluation(WeightMethod.EXPERT)
        self.assertEqual(len(result.indicator_results), 1)
        self.assertEqual(len(result.category_results), 1)
        
        # 测试极值
        extreme_values = {
            "tech_1": 0.0,    # 最小值
            "tech_2": 95.0,   # 最大值
            "safety_1": 50.0  # 最小值
        }
        self.model.set_measured_values(extreme_values)
        
        result = self.model.calculate_evaluation(WeightMethod.EXPERT)
        self.assertIsInstance(result, EvaluationResult)
        
        # 验证极值处理
        for ind_result in result.indicator_results:
            self.assertGreaterEqual(ind_result.score, 0)
            self.assertLessEqual(ind_result.score, 100)


if __name__ == '__main__':
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestEvaluationRange))
    test_suite.addTest(unittest.makeSuite(TestIndicatorResult))
    test_suite.addTest(unittest.makeSuite(TestCategoryResult))
    test_suite.addTest(unittest.makeSuite(TestEvaluationModel))
    
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