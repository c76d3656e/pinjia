#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块单元测试

测试工具模块的功能，包括配置管理、日志管理、报告生成等。

作者: 开发团队
版本: 1.0.0
"""

import unittest
import tempfile
import os
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from src.utils.config import ConfigManager
from src.utils.logger import (
    setup_logger, get_logger, set_log_level, 
    LoggerMixin, log_function_call, log_exception, ContextLogger
)
from src.utils.report_generator import ReportGenerator, ReportConfig
from src.models.evaluation import (
    EvaluationResult, IndicatorResult, CategoryResult, 
    EvaluationGrade, WeightMethod
)


class TestConfigManager(unittest.TestCase):
    """
    配置管理器测试
    
    测试ConfigManager类的功能。
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建临时配置文件。
        """
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        self.temp_file.close()
        
        self.config_manager = ConfigManager(self.temp_file.name)
    
    def tearDown(self):
        """
        测试后清理
        
        删除临时文件。
        """
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_config_manager_initialization(self):
        """
        测试配置管理器初始化
        """
        self.assertEqual(self.config_manager.config_file, self.temp_file.name)
        self.assertIsInstance(self.config_manager.config, dict)
    
    def test_create_default_config(self):
        """
        测试创建默认配置
        """
        default_config = self.config_manager._create_default_config()
        
        # 验证默认配置结构
        self.assertIn("app", default_config)
        self.assertIn("server", default_config)
        self.assertIn("evaluation", default_config)
        self.assertIn("ui", default_config)
        self.assertIn("logging", default_config)
        
        # 验证应用配置
        app_config = default_config["app"]
        self.assertIn("name", app_config)
        self.assertIn("version", app_config)
        self.assertIn("debug", app_config)
        
        # 验证服务器配置
        server_config = default_config["server"]
        self.assertIn("host", server_config)
        self.assertIn("port", server_config)
        self.assertIn("auto_open_browser", server_config)
        
        # 验证评价配置
        eval_config = default_config["evaluation"]
        self.assertIn("default_weight_method", eval_config)
        self.assertIn("precision", eval_config)
        
        # 验证UI配置
        ui_config = default_config["ui"]
        self.assertIn("theme", ui_config)
        self.assertIn("language", ui_config)
        
        # 验证日志配置
        log_config = default_config["logging"]
        self.assertIn("level", log_config)
        self.assertIn("format", log_config)
    
    def test_load_config_new_file(self):
        """
        测试加载新配置文件
        """
        # 删除临时文件以模拟新文件
        os.unlink(self.temp_file.name)
        
        config_manager = ConfigManager(self.temp_file.name)
        config_manager.load_config()
        
        # 验证文件已创建
        self.assertTrue(os.path.exists(self.temp_file.name))
        
        # 验证配置已加载
        self.assertIn("app", config_manager.config)
        self.assertIn("server", config_manager.config)
    
    def test_load_config_existing_file(self):
        """
        测试加载现有配置文件
        """
        # 创建测试配置
        test_config = {
            "app": {
                "name": "Test App",
                "version": "1.0.0"
            },
            "server": {
                "host": "localhost",
                "port": 8080
            }
        }
        
        # 写入配置文件
        with open(self.temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        # 加载配置
        self.config_manager.load_config()
        
        # 验证配置已正确加载
        self.assertEqual(self.config_manager.config["app"]["name"], "Test App")
        self.assertEqual(self.config_manager.config["server"]["port"], 8080)
    
    def test_save_config(self):
        """
        测试保存配置
        """
        # 修改配置
        self.config_manager.config["app"] = {
            "name": "Modified App",
            "version": "2.0.0"
        }
        
        # 保存配置
        success = self.config_manager.save_config()
        self.assertTrue(success)
        
        # 验证文件内容
        with open(self.temp_file.name, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config["app"]["name"], "Modified App")
        self.assertEqual(saved_config["app"]["version"], "2.0.0")
    
    def test_get_set_config(self):
        """
        测试获取和设置配置项
        """
        self.config_manager.load_config()
        
        # 测试获取配置项
        app_name = self.config_manager.get("app.name")
        self.assertIsNotNone(app_name)
        
        server_port = self.config_manager.get("server.port")
        self.assertIsInstance(server_port, int)
        
        # 测试获取不存在的配置项
        nonexistent = self.config_manager.get("nonexistent.key", "default")
        self.assertEqual(nonexistent, "default")
        
        # 测试设置配置项
        success = self.config_manager.set("app.name", "New App Name")
        self.assertTrue(success)
        
        # 验证设置结果
        new_name = self.config_manager.get("app.name")
        self.assertEqual(new_name, "New App Name")
        
        # 测试设置嵌套配置项
        success = self.config_manager.set("new.nested.key", "value")
        self.assertTrue(success)
        
        nested_value = self.config_manager.get("new.nested.key")
        self.assertEqual(nested_value, "value")
    
    def test_reload_config(self):
        """
        测试重新加载配置
        """
        self.config_manager.load_config()
        
        # 修改内存中的配置
        original_name = self.config_manager.get("app.name")
        self.config_manager.set("app.name", "Modified Name")
        
        # 重新加载配置
        self.config_manager.reload_config()
        
        # 验证配置已恢复
        reloaded_name = self.config_manager.get("app.name")
        self.assertEqual(reloaded_name, original_name)
    
    def test_validate_config(self):
        """
        测试配置验证
        """
        self.config_manager.load_config()
        
        # 测试有效配置
        errors = self.config_manager.validate_config()
        self.assertEqual(len(errors), 0)
        
        # 测试无效配置
        self.config_manager.config["server"]["port"] = "invalid_port"
        errors = self.config_manager.validate_config()
        self.assertGreater(len(errors), 0)
        
        # 测试缺少必需配置
        del self.config_manager.config["app"]["name"]
        errors = self.config_manager.validate_config()
        self.assertGreater(len(errors), 0)


class TestLogger(unittest.TestCase):
    """
    日志管理测试
    
    测试日志相关功能。
    """
    
    def setUp(self):
        """
        测试前准备
        """
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")
    
    def tearDown(self):
        """
        测试后清理
        """
        # 清理日志处理器
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        
        # 删除临时文件
        if os.path.exists(self.log_file):
            os.unlink(self.log_file)
        os.rmdir(self.temp_dir)
    
    def test_setup_logger(self):
        """
        测试日志设置
        """
        logger = setup_logger(
            name="test_logger",
            level="INFO",
            log_file=self.log_file,
            console_output=True
        )
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.INFO)
        
        # 验证处理器
        self.assertGreater(len(logger.handlers), 0)
    
    def test_get_logger(self):
        """
        测试获取日志记录器
        """
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        
        # 验证单例模式
        self.assertIs(logger1, logger2)
        
        # 验证不同名称的日志记录器
        logger3 = get_logger("another_module")
        self.assertIsNot(logger1, logger3)
    
    def test_set_log_level(self):
        """
        测试设置日志级别
        """
        logger = get_logger("test_level")
        
        # 设置DEBUG级别
        set_log_level("DEBUG")
        self.assertEqual(logger.level, logging.DEBUG)
        
        # 设置WARNING级别
        set_log_level("WARNING")
        self.assertEqual(logger.level, logging.WARNING)
    
    def test_logger_mixin(self):
        """
        测试日志混入类
        """
        class TestClass(LoggerMixin):
            def test_method(self):
                self.logger.info("Test message")
                return "result"
        
        test_obj = TestClass()
        
        # 验证日志记录器存在
        self.assertIsInstance(test_obj.logger, logging.Logger)
        
        # 验证日志记录器名称
        expected_name = f"{TestClass.__module__}.{TestClass.__name__}"
        self.assertEqual(test_obj.logger.name, expected_name)
    
    def test_log_function_call_decorator(self):
        """
        测试函数调用日志装饰器
        """
        @log_function_call
        def test_function(x, y=10):
            return x + y
        
        # 捕获日志输出
        with patch('src.utils.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            result = test_function(5, y=15)
            
            # 验证函数结果
            self.assertEqual(result, 20)
            
            # 验证日志调用
            self.assertTrue(mock_logger.debug.called)
    
    def test_log_exception_decorator(self):
        """
        测试异常日志装饰器
        """
        @log_exception
        def test_function_with_exception():
            raise ValueError("Test exception")
        
        # 捕获日志输出
        with patch('src.utils.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            with self.assertRaises(ValueError):
                test_function_with_exception()
            
            # 验证异常日志调用
            self.assertTrue(mock_logger.exception.called)
    
    def test_context_logger(self):
        """
        测试上下文日志记录器
        """
        with patch('src.utils.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            with ContextLogger("test_context", {"key": "value"}):
                pass
            
            # 验证进入和退出日志
            self.assertEqual(mock_logger.info.call_count, 2)


class TestReportGenerator(unittest.TestCase):
    """
    报告生成器测试
    
    测试ReportGenerator类的功能。
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建测试用的评价结果。
        """
        # 创建测试评价结果
        self.indicator_results = [
            IndicatorResult(
                indicator_id="tech_1",
                measured_value=8.0,
                normalized_value=0.75,
                score=75.0,
                grade=EvaluationGrade.AVERAGE,
                weight=0.3
            ),
            IndicatorResult(
                indicator_id="tech_2",
                measured_value=88.0,
                normalized_value=0.85,
                score=85.0,
                grade=EvaluationGrade.GOOD,
                weight=0.3
            ),
            IndicatorResult(
                indicator_id="safety_1",
                measured_value=75.0,
                normalized_value=0.95,
                score=95.0,
                grade=EvaluationGrade.EXCELLENT,
                weight=0.4
            )
        ]
        
        self.category_results = [
            CategoryResult(
                category_id="technical",
                score=80.0,
                grade=EvaluationGrade.GOOD,
                weight=0.6,
                indicator_results=self.indicator_results[:2]
            ),
            CategoryResult(
                category_id="safety",
                score=95.0,
                grade=EvaluationGrade.EXCELLENT,
                weight=0.4,
                indicator_results=self.indicator_results[2:]
            )
        ]
        
        self.evaluation_result = EvaluationResult(
            total_score=86.0,
            final_grade=EvaluationGrade.GOOD,
            weight_method=WeightMethod.EXPERT,
            indicator_results=self.indicator_results,
            category_results=self.category_results,
            summary="综合评价结果为良好等级"
        )
        
        # 创建报告配置
        self.report_config = ReportConfig(
            project_name="测试爆破项目",
            location="测试地点",
            date="2024-01-01",
            evaluator="测试评价员",
            organization="测试机构"
        )
        
        # 创建报告生成器
        self.generator = ReportGenerator()
    
    def test_report_config_creation(self):
        """
        测试报告配置创建
        """
        self.assertEqual(self.report_config.project_name, "测试爆破项目")
        self.assertEqual(self.report_config.location, "测试地点")
        self.assertEqual(self.report_config.date, "2024-01-01")
        self.assertEqual(self.report_config.evaluator, "测试评价员")
        self.assertEqual(self.report_config.organization, "测试机构")
    
    def test_generate_text_report(self):
        """
        测试生成文本报告
        """
        report = self.generator.generate_text_report(
            self.evaluation_result, 
            self.report_config
        )
        
        # 验证报告内容
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        
        # 验证报告包含关键信息
        self.assertIn("测试爆破项目", report)
        self.assertIn("测试地点", report)
        self.assertIn("86.0", report)  # 总分
        self.assertIn("良好", report)  # 等级
        
        # 验证包含指标信息
        self.assertIn("tech_1", report)
        self.assertIn("tech_2", report)
        self.assertIn("safety_1", report)
    
    def test_generate_html_report(self):
        """
        测试生成HTML报告
        """
        report = self.generator.generate_html_report(
            self.evaluation_result, 
            self.report_config
        )
        
        # 验证HTML结构
        self.assertIsInstance(report, str)
        self.assertIn("<html>", report)
        self.assertIn("</html>", report)
        self.assertIn("<head>", report)
        self.assertIn("<body>", report)
        
        # 验证报告内容
        self.assertIn("测试爆破项目", report)
        self.assertIn("86.0", report)
        self.assertIn("良好", report)
        
        # 验证表格结构
        self.assertIn("<table>", report)
        self.assertIn("<tr>", report)
        self.assertIn("<td>", report)
    
    def test_generate_json_report(self):
        """
        测试生成JSON报告
        """
        report = self.generator.generate_json_report(
            self.evaluation_result, 
            self.report_config
        )
        
        # 验证JSON结构
        self.assertIsInstance(report, str)
        
        # 解析JSON
        report_data = json.loads(report)
        
        # 验证报告结构
        self.assertIn("report_info", report_data)
        self.assertIn("evaluation_summary", report_data)
        self.assertIn("indicator_details", report_data)
        self.assertIn("category_results", report_data)
        self.assertIn("recommendations", report_data)
        
        # 验证报告内容
        self.assertEqual(report_data["report_info"]["project_name"], "测试爆破项目")
        self.assertEqual(report_data["evaluation_summary"]["total_score"], 86.0)
        self.assertEqual(len(report_data["indicator_details"]), 3)
        self.assertEqual(len(report_data["category_results"]), 2)
    
    def test_generate_recommendations(self):
        """
        测试生成改进建议
        """
        recommendations = self.generator._generate_recommendations(self.evaluation_result)
        
        # 验证建议结构
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # 验证建议内容
        for recommendation in recommendations:
            self.assertIsInstance(recommendation, str)
            self.assertGreater(len(recommendation), 0)
    
    def test_build_report_sections(self):
        """
        测试构建报告各部分
        """
        # 测试报告头
        header = self.generator._build_report_header(self.report_config)
        self.assertIn("测试爆破项目", header)
        self.assertIn("测试地点", header)
        
        # 测试评价概要
        summary = self.generator._build_evaluation_summary(self.evaluation_result)
        self.assertIn("86.0", summary)
        self.assertIn("良好", summary)
        
        # 测试指标详情
        details = self.generator._build_indicator_details(self.evaluation_result)
        self.assertIn("tech_1", details)
        self.assertIn("75.0", details)
        
        # 测试分类结果
        categories = self.generator._build_category_results(self.evaluation_result)
        self.assertIn("technical", categories)
        self.assertIn("safety", categories)
        
        # 测试报告尾部
        footer = self.generator._build_report_footer(self.report_config)
        self.assertIn("测试评价员", footer)
        self.assertIn("测试机构", footer)
    
    def test_edge_cases(self):
        """
        测试边界情况
        """
        # 测试空评价结果
        empty_result = EvaluationResult(
            total_score=0.0,
            final_grade=EvaluationGrade.POOR,
            weight_method=WeightMethod.EQUAL,
            indicator_results=[],
            category_results=[],
            summary="无评价结果"
        )
        
        report = self.generator.generate_text_report(empty_result, self.report_config)
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        
        # 测试单个指标结果
        single_result = EvaluationResult(
            total_score=85.0,
            final_grade=EvaluationGrade.GOOD,
            weight_method=WeightMethod.EXPERT,
            indicator_results=self.indicator_results[:1],
            category_results=self.category_results[:1],
            summary="单指标评价"
        )
        
        report = self.generator.generate_html_report(single_result, self.report_config)
        self.assertIn("<html>", report)
        self.assertIn("85.0", report)


if __name__ == '__main__':
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestConfigManager))
    test_suite.addTest(unittest.makeSuite(TestLogger))
    test_suite.addTest(unittest.makeSuite(TestReportGenerator))
    
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