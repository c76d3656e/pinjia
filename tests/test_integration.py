#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试

测试系统各模块之间的集成功能。
包括端到端的评价流程、数据流转、错误处理等。

作者: 开发团队
版本: 1.0.0
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, MagicMock

from src.controllers.evaluation_controller import EvaluationController
from src.models.evaluation import WeightMethod, EvaluationGrade
from src.utils.config import ConfigManager
from src.utils.logger import setup_logger, get_logger
from src.utils.report_generator import ReportGenerator, ReportConfig


class TestSystemIntegration(unittest.TestCase):
    """
    系统集成测试
    
    测试整个系统的集成功能。
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建测试环境和数据。
        """
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试指标文件
        self.indicators_file = os.path.join(self.temp_dir, "indicators.json")
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
                    "weight": 0.25
                },
                {
                    "id": "economic",
                    "name": "经济指标",
                    "description": "爆破经济效益相关指标",
                    "weight": 0.15
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
                    "weight": 0.4
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
                    "weight": 0.3
                },
                {
                    "id": "tech_3",
                    "name": "根底率",
                    "unit": "%",
                    "description": "爆破后根底残留比例",
                    "is_positive": False,
                    "category_id": "technical",
                    "min_value": 0.0,
                    "max_value": 15.0,
                    "weight": 0.3
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
                    "weight": 0.5
                },
                {
                    "id": "safety_2",
                    "name": "地震波强度",
                    "unit": "mm/s",
                    "description": "爆破引起的地震波峰值速度",
                    "is_positive": False,
                    "category_id": "safety",
                    "min_value": 0.0,
                    "max_value": 20.0,
                    "weight": 0.5
                },
                {
                    "id": "economic_1",
                    "name": "炸药单耗",
                    "unit": "kg/m³",
                    "description": "单位体积岩石的炸药消耗量",
                    "is_positive": False,
                    "category_id": "economic",
                    "min_value": 0.2,
                    "max_value": 0.8,
                    "weight": 1.0
                }
            ]
        }
        
        # 写入指标文件
        with open(self.indicators_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_indicators_data, f, ensure_ascii=False, indent=2)
        
        # 创建配置文件
        self.config_file = os.path.join(self.temp_dir, "config.json")
        self.config_manager = ConfigManager(self.config_file)
        
        # 创建日志文件
        self.log_file = os.path.join(self.temp_dir, "test.log")
        
        # 初始化控制器
        self.controller = EvaluationController()
        
        # 初始化报告生成器
        self.report_generator = ReportGenerator()
    
    def tearDown(self):
        """
        测试后清理
        
        删除临时文件和目录。
        """
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_evaluation_workflow(self):
        """
        测试完整的评价工作流程
        
        从加载指标到生成报告的完整流程。
        """
        # 步骤1: 加载指标数据
        success = self.controller.load_indicators(self.indicators_file)
        self.assertTrue(success, "指标数据加载失败")
        
        # 验证指标加载
        categories = self.controller.get_all_categories()
        indicators = self.controller.get_all_indicators()
        self.assertEqual(len(categories), 3, "分类数量不正确")
        self.assertEqual(len(indicators), 6, "指标数量不正确")
        
        # 步骤2: 选择评价指标
        selected_indicator_ids = ["tech_1", "tech_2", "safety_1", "safety_2", "economic_1"]
        self.controller.update_selected_indicators(selected_indicator_ids)
        
        selected_indicators = self.controller.get_selected_indicators()
        self.assertEqual(len(selected_indicators), 5, "选中指标数量不正确")
        
        # 步骤3: 设置权重
        # 使用专家打分法设置指标权重
        indicator_weights = {
            "tech_1": 0.25,
            "tech_2": 0.20,
            "safety_1": 0.20,
            "safety_2": 0.20,
            "economic_1": 0.15
        }
        success = self.controller.set_indicator_weights(indicator_weights)
        self.assertTrue(success, "指标权重设置失败")
        
        # 设置分类权重
        category_weights = {
            "technical": 0.50,
            "safety": 0.35,
            "economic": 0.15
        }
        success = self.controller.set_category_weights(category_weights)
        self.assertTrue(success, "分类权重设置失败")
        
        # 步骤4: 设置评价范围
        evaluation_ranges = {
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
            },
            "safety_2": {
                "excellent": (0, 5),
                "good": (5, 10),
                "average": (10, 15),
                "poor": (15, 20)
            },
            "economic_1": {
                "excellent": (0.2, 0.35),
                "good": (0.35, 0.45),
                "average": (0.45, 0.6),
                "poor": (0.6, 0.8)
            }
        }
        success = self.controller.set_evaluation_ranges(evaluation_ranges)
        self.assertTrue(success, "评价范围设置失败")
        
        # 步骤5: 输入实测值
        measured_values = {
            "tech_1": 8.5,      # 一般等级
            "tech_2": 87.0,     # 良好等级
            "safety_1": 95.0,   # 良好等级
            "safety_2": 6.5,    # 良好等级
            "economic_1": 0.42  # 良好等级
        }
        success = self.controller.set_measured_values(measured_values)
        self.assertTrue(success, "实测值设置失败")
        
        # 步骤6: 验证数据完整性
        validation_errors = self.controller.validate_evaluation_data()
        self.assertEqual(len(validation_errors), 0, f"数据验证失败: {validation_errors}")
        
        # 步骤7: 执行评价计算
        evaluation_result = self.controller.execute_evaluation(WeightMethod.EXPERT)
        self.assertIsNotNone(evaluation_result, "评价计算失败")
        
        # 验证评价结果
        self.assertGreaterEqual(evaluation_result.total_score, 0, "总分不能为负")
        self.assertLessEqual(evaluation_result.total_score, 100, "总分不能超过100")
        self.assertIsInstance(evaluation_result.final_grade, EvaluationGrade, "评价等级类型错误")
        self.assertEqual(len(evaluation_result.indicator_results), 5, "指标结果数量不正确")
        self.assertEqual(len(evaluation_result.category_results), 3, "分类结果数量不正确")
        
        # 步骤8: 生成评价报告
        report_config = ReportConfig(
            project_name="集成测试爆破项目",
            location="测试矿山",
            date="2024-01-15",
            evaluator="系统测试员",
            organization="测试机构"
        )
        
        # 生成文本报告
        text_report = self.report_generator.generate_text_report(
            evaluation_result, report_config
        )
        self.assertIsInstance(text_report, str, "文本报告生成失败")
        self.assertGreater(len(text_report), 100, "文本报告内容过短")
        
        # 生成HTML报告
        html_report = self.report_generator.generate_html_report(
            evaluation_result, report_config
        )
        self.assertIsInstance(html_report, str, "HTML报告生成失败")
        self.assertIn("<html>", html_report, "HTML报告格式错误")
        
        # 生成JSON报告
        json_report = self.report_generator.generate_json_report(
            evaluation_result, report_config
        )
        self.assertIsInstance(json_report, str, "JSON报告生成失败")
        
        # 验证JSON报告可解析
        try:
            json_data = json.loads(json_report)
            self.assertIn("report_info", json_data, "JSON报告结构错误")
            self.assertIn("evaluation_summary", json_data, "JSON报告结构错误")
        except json.JSONDecodeError:
            self.fail("JSON报告格式错误")
        
        # 步骤9: 导出和导入评价数据
        export_data = self.controller.export_evaluation_data()
        self.assertIsInstance(export_data, dict, "导出数据格式错误")
        self.assertIn("selected_indicators", export_data, "导出数据缺少选中指标")
        self.assertIn("indicator_weights", export_data, "导出数据缺少指标权重")
        
        # 重置控制器并重新加载指标
        self.controller.reset()
        self.controller.load_indicators(self.indicators_file)
        
        # 导入评价数据
        import_success = self.controller.import_evaluation_data(export_data)
        self.assertTrue(import_success, "导入评价数据失败")
        
        # 验证导入后的数据
        imported_indicators = self.controller.get_selected_indicators()
        self.assertEqual(len(imported_indicators), 5, "导入后指标数量不正确")
        
        imported_weights = self.controller.get_indicator_weights()
        self.assertEqual(len(imported_weights), 5, "导入后权重数量不正确")
        
        print(f"\n=== 集成测试完成 ===")
        print(f"总分: {evaluation_result.total_score:.2f}")
        print(f"等级: {evaluation_result.final_grade.value}")
        print(f"权重方法: {evaluation_result.weight_method.value}")
        print(f"指标数量: {len(evaluation_result.indicator_results)}")
        print(f"分类数量: {len(evaluation_result.category_results)}")
    
    def test_different_weight_methods_comparison(self):
        """
        测试不同权重方法的比较
        
        验证不同权重计算方法的结果差异。
        """
        # 准备基础数据
        self.controller.load_indicators(self.indicators_file)
        self.controller.update_selected_indicators(["tech_1", "tech_2", "safety_1"])
        
        # 设置评价范围
        evaluation_ranges = {
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
        self.controller.set_evaluation_ranges(evaluation_ranges)
        
        # 设置实测值
        measured_values = {
            "tech_1": 8.0,
            "tech_2": 88.0,
            "safety_1": 95.0
        }
        self.controller.set_measured_values(measured_values)
        
        # 设置分类权重
        category_weights = {"technical": 0.7, "safety": 0.3}
        self.controller.set_category_weights(category_weights)
        
        # 测试等权重法
        result_equal = self.controller.execute_evaluation(WeightMethod.EQUAL)
        self.assertIsNotNone(result_equal, "等权重法评价失败")
        
        # 测试专家打分法
        expert_weights = {"tech_1": 0.4, "tech_2": 0.3, "safety_1": 0.3}
        self.controller.set_indicator_weights(expert_weights)
        result_expert = self.controller.execute_evaluation(WeightMethod.EXPERT)
        self.assertIsNotNone(result_expert, "专家打分法评价失败")
        
        # 比较结果
        print(f"\n=== 权重方法比较 ===")
        print(f"等权重法总分: {result_equal.total_score:.2f}")
        print(f"专家打分法总分: {result_expert.total_score:.2f}")
        print(f"分数差异: {abs(result_equal.total_score - result_expert.total_score):.2f}")
        
        # 验证结果合理性
        self.assertGreaterEqual(result_equal.total_score, 0)
        self.assertLessEqual(result_equal.total_score, 100)
        self.assertGreaterEqual(result_expert.total_score, 0)
        self.assertLessEqual(result_expert.total_score, 100)
    
    def test_error_handling_and_recovery(self):
        """
        测试错误处理和恢复机制
        
        验证系统在各种错误情况下的处理能力。
        """
        # 测试加载不存在的文件
        success = self.controller.load_indicators("nonexistent_file.json")
        self.assertFalse(success, "应该无法加载不存在的文件")
        
        # 测试加载无效JSON文件
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        success = self.controller.load_indicators(invalid_file)
        self.assertFalse(success, "应该无法加载无效JSON文件")
        
        # 正确加载指标后测试各种错误情况
        self.controller.load_indicators(self.indicators_file)
        
        # 测试设置无效权重
        invalid_weights = {"tech_1": 0.3, "tech_2": 0.3}  # 权重和不为1
        success = self.controller.set_indicator_weights(invalid_weights)
        self.assertFalse(success, "应该拒绝无效权重")
        
        # 测试在数据不完整时执行评价
        result = self.controller.execute_evaluation(WeightMethod.EXPERT)
        self.assertIsNone(result, "数据不完整时不应该执行评价")
        
        # 测试数据验证
        errors = self.controller.validate_evaluation_data()
        self.assertGreater(len(errors), 0, "应该检测到数据不完整错误")
        
        print(f"\n=== 错误处理测试 ===")
        print(f"检测到 {len(errors)} 个数据验证错误:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    
    def test_configuration_integration(self):
        """
        测试配置管理集成
        
        验证配置管理与其他模块的集成。
        """
        # 加载配置
        self.config_manager.load_config()
        
        # 验证默认配置
        app_name = self.config_manager.get("app.name")
        self.assertIsNotNone(app_name, "应用名称不能为空")
        
        server_port = self.config_manager.get("server.port")
        self.assertIsInstance(server_port, int, "服务器端口应该是整数")
        
        # 修改配置
        self.config_manager.set("app.name", "集成测试应用")
        self.config_manager.set("evaluation.precision", 3)
        
        # 保存配置
        success = self.config_manager.save_config()
        self.assertTrue(success, "配置保存失败")
        
        # 重新加载验证
        self.config_manager.reload_config()
        new_app_name = self.config_manager.get("app.name")
        self.assertEqual(new_app_name, "集成测试应用", "配置修改未生效")
        
        print(f"\n=== 配置管理测试 ===")
        print(f"应用名称: {new_app_name}")
        print(f"服务器端口: {server_port}")
        print(f"评价精度: {self.config_manager.get('evaluation.precision')}")
    
    def test_logging_integration(self):
        """
        测试日志系统集成
        
        验证日志记录功能的集成。
        """
        # 设置日志
        logger = setup_logger(
            name="integration_test",
            level="DEBUG",
            log_file=self.log_file,
            console_output=False
        )
        
        # 记录各种级别的日志
        logger.debug("调试信息: 开始集成测试")
        logger.info("信息: 加载指标数据")
        logger.warning("警告: 测试警告消息")
        logger.error("错误: 测试错误消息")
        
        # 验证日志文件存在
        self.assertTrue(os.path.exists(self.log_file), "日志文件未创建")
        
        # 读取日志内容
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 验证日志内容
        self.assertIn("集成测试", log_content, "日志内容不正确")
        self.assertIn("加载指标数据", log_content, "日志内容不正确")
        
        print(f"\n=== 日志系统测试 ===")
        print(f"日志文件: {self.log_file}")
        print(f"日志大小: {os.path.getsize(self.log_file)} 字节")
    
    def test_performance_and_scalability(self):
        """
        测试性能和可扩展性
        
        验证系统在处理大量数据时的性能。
        """
        import time
        
        # 加载指标数据
        start_time = time.time()
        self.controller.load_indicators(self.indicators_file)
        load_time = time.time() - start_time
        
        # 选择所有指标
        all_indicator_ids = [ind.id for ind in self.controller.get_all_indicators()]
        self.controller.update_selected_indicators(all_indicator_ids)
        
        # 设置权重（等权重）
        start_time = time.time()
        weights = self.controller.calculate_weights(WeightMethod.EQUAL)
        weight_calc_time = time.time() - start_time
        
        self.controller.set_indicator_weights(weights)
        
        # 设置分类权重
        category_weights = {"technical": 0.5, "safety": 0.3, "economic": 0.2}
        self.controller.set_category_weights(category_weights)
        
        # 设置评价范围和实测值
        ranges = {}
        values = {}
        for indicator in self.controller.get_selected_indicators():
            ranges[indicator.id] = {
                "excellent": (indicator.min_value, indicator.min_value + 0.2 * (indicator.max_value - indicator.min_value)),
                "good": (indicator.min_value + 0.2 * (indicator.max_value - indicator.min_value), indicator.min_value + 0.5 * (indicator.max_value - indicator.min_value)),
                "average": (indicator.min_value + 0.5 * (indicator.max_value - indicator.min_value), indicator.min_value + 0.8 * (indicator.max_value - indicator.min_value)),
                "poor": (indicator.min_value + 0.8 * (indicator.max_value - indicator.min_value), indicator.max_value)
            }
            # 设置中等水平的实测值
            values[indicator.id] = indicator.min_value + 0.6 * (indicator.max_value - indicator.min_value)
        
        self.controller.set_evaluation_ranges(ranges)
        self.controller.set_measured_values(values)
        
        # 执行评价计算
        start_time = time.time()
        result = self.controller.execute_evaluation(WeightMethod.EXPERT)
        evaluation_time = time.time() - start_time
        
        # 生成报告
        report_config = ReportConfig(
            project_name="性能测试项目",
            location="测试地点",
            date="2024-01-15",
            evaluator="性能测试员",
            organization="测试机构"
        )
        
        start_time = time.time()
        text_report = self.report_generator.generate_text_report(result, report_config)
        report_time = time.time() - start_time
        
        # 验证性能指标
        self.assertLess(load_time, 1.0, "指标加载时间过长")
        self.assertLess(weight_calc_time, 0.5, "权重计算时间过长")
        self.assertLess(evaluation_time, 2.0, "评价计算时间过长")
        self.assertLess(report_time, 1.0, "报告生成时间过长")
        
        print(f"\n=== 性能测试结果 ===")
        print(f"指标加载时间: {load_time:.3f} 秒")
        print(f"权重计算时间: {weight_calc_time:.3f} 秒")
        print(f"评价计算时间: {evaluation_time:.3f} 秒")
        print(f"报告生成时间: {report_time:.3f} 秒")
        print(f"处理指标数量: {len(all_indicator_ids)}")
        print(f"评价总分: {result.total_score:.2f}")


if __name__ == '__main__':
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestSystemIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print(f"集成测试完成")
    print(f"{'='*50}")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback}")
    
    # 测试总结
    if len(result.failures) == 0 and len(result.errors) == 0:
        print(f"\n🎉 所有集成测试通过！系统各模块集成正常。")
    else:
        print(f"\n❌ 集成测试发现问题，请检查失败的测试用例。")