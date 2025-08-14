#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指标模型单元测试

测试指标相关的数据模型和管理功能。
包括指标创建、验证、序列化、管理器功能等。

作者: 开发团队
版本: 1.0.0
"""

import unittest
import tempfile
import json
from pathlib import Path
from typing import Dict, Any

from src.models.indicators import Indicator, IndicatorCategory, IndicatorManager


class TestIndicator(unittest.TestCase):
    """
    指标类测试
    
    测试Indicator类的各种功能，包括:
    1. 实例创建和属性设置
    2. 数据验证
    3. 序列化和反序列化
    4. 值验证和标准化
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建测试用的指标实例。
        """
        self.indicator = Indicator(
            id="test_1",
            name="测试指标",
            unit="%",
            description="这是一个测试指标",
            is_positive=True,
            category_id="test_category",
            min_value=0.0,
            max_value=100.0,
            default_weight=0.1
        )
    
    def test_indicator_creation(self):
        """
        测试指标创建
        
        验证指标实例是否正确创建，属性是否正确设置。
        """
        self.assertEqual(self.indicator.id, "test_1")
        self.assertEqual(self.indicator.name, "测试指标")
        self.assertEqual(self.indicator.unit, "%")
        self.assertEqual(self.indicator.description, "这是一个测试指标")
        self.assertTrue(self.indicator.is_positive)
        self.assertEqual(self.indicator.category_id, "test_category")
        self.assertEqual(self.indicator.min_value, 0.0)
        self.assertEqual(self.indicator.max_value, 100.0)
        self.assertEqual(self.indicator.default_weight, 0.1)
    
    def test_indicator_validation(self):
        """
        测试指标数据验证
        
        验证指标数据验证功能是否正常工作。
        """
        # 测试有效数据
        errors = self.indicator.validate()
        self.assertEqual(len(errors), 0)
        
        # 测试无效ID
        invalid_indicator = Indicator(
            id="",  # 空ID
            name="测试指标",
            unit="%",
            description="测试"
        )
        errors = invalid_indicator.validate()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("ID不能为空" in error for error in errors))
        
        # 测试无效名称
        invalid_indicator = Indicator(
            id="test_1",
            name="",  # 空名称
            unit="%",
            description="测试"
        )
        errors = invalid_indicator.validate()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("名称不能为空" in error for error in errors))
        
        # 测试无效范围
        invalid_indicator = Indicator(
            id="test_1",
            name="测试指标",
            unit="%",
            description="测试",
            min_value=100.0,
            max_value=0.0  # 最大值小于最小值
        )
        errors = invalid_indicator.validate()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("最大值必须大于最小值" in error for error in errors))
    
    def test_indicator_serialization(self):
        """
        测试指标序列化
        
        验证指标的字典转换和JSON序列化功能。
        """
        # 测试to_dict
        indicator_dict = self.indicator.to_dict()
        
        expected_keys = {
            'id', 'name', 'unit', 'description', 'is_positive',
            'category_id', 'min_value', 'max_value', 'default_weight'
        }
        self.assertEqual(set(indicator_dict.keys()), expected_keys)
        
        # 测试from_dict
        restored_indicator = Indicator.from_dict(indicator_dict)
        
        self.assertEqual(restored_indicator.id, self.indicator.id)
        self.assertEqual(restored_indicator.name, self.indicator.name)
        self.assertEqual(restored_indicator.unit, self.indicator.unit)
        self.assertEqual(restored_indicator.description, self.indicator.description)
        self.assertEqual(restored_indicator.is_positive, self.indicator.is_positive)
        self.assertEqual(restored_indicator.category_id, self.indicator.category_id)
        self.assertEqual(restored_indicator.min_value, self.indicator.min_value)
        self.assertEqual(restored_indicator.max_value, self.indicator.max_value)
        self.assertEqual(restored_indicator.default_weight, self.indicator.default_weight)
    
    def test_value_validation(self):
        """
        测试值验证
        
        验证指标值验证功能是否正常工作。
        """
        # 测试有效值
        self.assertTrue(self.indicator.is_valid_value(50.0))
        self.assertTrue(self.indicator.is_valid_value(0.0))
        self.assertTrue(self.indicator.is_valid_value(100.0))
        
        # 测试无效值
        self.assertFalse(self.indicator.is_valid_value(-10.0))  # 小于最小值
        self.assertFalse(self.indicator.is_valid_value(110.0))  # 大于最大值
        
        # 测试None值
        self.assertFalse(self.indicator.is_valid_value(None))
    
    def test_value_normalization(self):
        """
        测试值标准化
        
        验证指标值标准化功能是否正确。
        """
        # 测试正向指标标准化
        self.assertAlmostEqual(self.indicator.normalize_value(0.0), 0.0)
        self.assertAlmostEqual(self.indicator.normalize_value(50.0), 0.5)
        self.assertAlmostEqual(self.indicator.normalize_value(100.0), 1.0)
        
        # 测试反向指标标准化
        negative_indicator = Indicator(
            id="test_2",
            name="反向指标",
            unit="%",
            description="测试反向指标",
            is_positive=False,
            min_value=0.0,
            max_value=100.0
        )
        
        self.assertAlmostEqual(negative_indicator.normalize_value(0.0), 1.0)
        self.assertAlmostEqual(negative_indicator.normalize_value(50.0), 0.5)
        self.assertAlmostEqual(negative_indicator.normalize_value(100.0), 0.0)


class TestIndicatorCategory(unittest.TestCase):
    """
    指标分类测试
    
    测试IndicatorCategory类的各种功能，包括:
    1. 分类创建和属性设置
    2. 指标管理功能
    3. 数据验证
    4. 序列化和反序列化
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建测试用的分类和指标实例。
        """
        self.category = IndicatorCategory(
            id="test_category",
            name="测试分类",
            description="这是一个测试分类",
            default_weight=0.3
        )
        
        self.indicator1 = Indicator(
            id="test_1",
            name="测试指标1",
            unit="%",
            description="测试指标1",
            category_id="test_category"
        )
        
        self.indicator2 = Indicator(
            id="test_2",
            name="测试指标2",
            unit="m",
            description="测试指标2",
            category_id="test_category"
        )
    
    def test_category_creation(self):
        """
        测试分类创建
        
        验证分类实例是否正确创建。
        """
        self.assertEqual(self.category.id, "test_category")
        self.assertEqual(self.category.name, "测试分类")
        self.assertEqual(self.category.description, "这是一个测试分类")
        self.assertEqual(self.category.default_weight, 0.3)
        self.assertEqual(len(self.category.indicators), 0)
    
    def test_indicator_management(self):
        """
        测试指标管理功能
        
        验证分类的指标添加、移除、获取功能。
        """
        # 测试添加指标
        self.category.add_indicator(self.indicator1)
        self.assertEqual(len(self.category.indicators), 1)
        self.assertIn(self.indicator1, self.category.indicators)
        
        # 测试添加重复指标
        self.category.add_indicator(self.indicator1)  # 重复添加
        self.assertEqual(len(self.category.indicators), 1)  # 数量不变
        
        # 测试添加多个指标
        self.category.add_indicator(self.indicator2)
        self.assertEqual(len(self.category.indicators), 2)
        
        # 测试获取指标
        retrieved_indicator = self.category.get_indicator("test_1")
        self.assertEqual(retrieved_indicator, self.indicator1)
        
        # 测试获取不存在的指标
        non_existent = self.category.get_indicator("non_existent")
        self.assertIsNone(non_existent)
        
        # 测试移除指标
        removed = self.category.remove_indicator("test_1")
        self.assertTrue(removed)
        self.assertEqual(len(self.category.indicators), 1)
        self.assertNotIn(self.indicator1, self.category.indicators)
        
        # 测试移除不存在的指标
        removed = self.category.remove_indicator("non_existent")
        self.assertFalse(removed)
    
    def test_category_validation(self):
        """
        测试分类数据验证
        
        验证分类数据验证功能。
        """
        # 测试有效数据
        errors = self.category.validate()
        self.assertEqual(len(errors), 0)
        
        # 测试无效ID
        invalid_category = IndicatorCategory(
            id="",  # 空ID
            name="测试分类",
            description="测试"
        )
        errors = invalid_category.validate()
        self.assertGreater(len(errors), 0)
        
        # 测试无效名称
        invalid_category = IndicatorCategory(
            id="test_category",
            name="",  # 空名称
            description="测试"
        )
        errors = invalid_category.validate()
        self.assertGreater(len(errors), 0)
    
    def test_category_serialization(self):
        """
        测试分类序列化
        
        验证分类的字典转换功能。
        """
        # 添加指标
        self.category.add_indicator(self.indicator1)
        self.category.add_indicator(self.indicator2)
        
        # 测试to_dict
        category_dict = self.category.to_dict()
        
        expected_keys = {'id', 'name', 'description', 'default_weight', 'indicators'}
        self.assertEqual(set(category_dict.keys()), expected_keys)
        self.assertEqual(len(category_dict['indicators']), 2)
        
        # 测试from_dict
        restored_category = IndicatorCategory.from_dict(category_dict)
        
        self.assertEqual(restored_category.id, self.category.id)
        self.assertEqual(restored_category.name, self.category.name)
        self.assertEqual(restored_category.description, self.category.description)
        self.assertEqual(restored_category.default_weight, self.category.default_weight)
        self.assertEqual(len(restored_category.indicators), 2)


class TestIndicatorManager(unittest.TestCase):
    """
    指标管理器测试
    
    测试IndicatorManager类的各种功能，包括:
    1. 管理器创建和初始化
    2. 分类和指标管理
    3. 文件加载和保存
    4. 数据验证
    """
    
    def setUp(self):
        """
        测试前准备
        
        创建临时文件和测试数据。
        """
        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # 创建管理器
        self.manager = IndicatorManager(self.temp_file_path)
        
        # 创建测试数据
        self.test_category = IndicatorCategory(
            id="test_category",
            name="测试分类",
            description="测试分类描述"
        )
        
        self.test_indicator = Indicator(
            id="test_1",
            name="测试指标",
            unit="%",
            description="测试指标描述",
            category_id="test_category"
        )
    
    def tearDown(self):
        """
        测试后清理
        
        删除临时文件。
        """
        temp_path = Path(self.temp_file_path)
        if temp_path.exists():
            temp_path.unlink()
    
    def test_manager_creation(self):
        """
        测试管理器创建
        
        验证管理器实例是否正确创建。
        """
        self.assertEqual(self.manager.config_file, self.temp_file_path)
        self.assertEqual(len(self.manager.categories), 0)
    
    def test_category_management(self):
        """
        测试分类管理功能
        
        验证分类的添加、获取、移除功能。
        """
        # 测试添加分类
        self.manager.add_category(self.test_category)
        self.assertEqual(len(self.manager.categories), 1)
        self.assertIn(self.test_category, self.manager.categories)
        
        # 测试获取分类
        retrieved_category = self.manager.get_category("test_category")
        self.assertEqual(retrieved_category, self.test_category)
        
        # 测试获取不存在的分类
        non_existent = self.manager.get_category("non_existent")
        self.assertIsNone(non_existent)
        
        # 测试移除分类
        removed = self.manager.remove_category("test_category")
        self.assertTrue(removed)
        self.assertEqual(len(self.manager.categories), 0)
        
        # 测试移除不存在的分类
        removed = self.manager.remove_category("non_existent")
        self.assertFalse(removed)
    
    def test_indicator_access(self):
        """
        测试指标访问功能
        
        验证通过管理器访问指标的功能。
        """
        # 添加分类和指标
        self.test_category.add_indicator(self.test_indicator)
        self.manager.add_category(self.test_category)
        
        # 测试获取所有指标
        all_indicators = self.manager.get_all_indicators()
        self.assertEqual(len(all_indicators), 1)
        self.assertIn(self.test_indicator, all_indicators)
        
        # 测试获取特定指标
        retrieved_indicator = self.manager.get_indicator("test_1")
        self.assertEqual(retrieved_indicator, self.test_indicator)
        
        # 测试获取不存在的指标
        non_existent = self.manager.get_indicator("non_existent")
        self.assertIsNone(non_existent)
    
    def test_file_operations(self):
        """
        测试文件操作
        
        验证文件加载和保存功能。
        """
        # 添加测试数据
        self.test_category.add_indicator(self.test_indicator)
        self.manager.add_category(self.test_category)
        
        # 测试保存到文件
        self.manager.save_to_file()
        
        # 验证文件存在
        temp_path = Path(self.temp_file_path)
        self.assertTrue(temp_path.exists())
        
        # 验证文件内容
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('categories', data)
        self.assertEqual(len(data['categories']), 1)
        
        # 测试从文件加载
        new_manager = IndicatorManager(self.temp_file_path)
        new_manager.load_from_file()
        
        self.assertEqual(len(new_manager.categories), 1)
        
        loaded_category = new_manager.get_category("test_category")
        self.assertIsNotNone(loaded_category)
        self.assertEqual(loaded_category.name, "测试分类")
        
        loaded_indicator = new_manager.get_indicator("test_1")
        self.assertIsNotNone(loaded_indicator)
        self.assertEqual(loaded_indicator.name, "测试指标")
    
    def test_data_validation(self):
        """
        测试数据验证
        
        验证管理器的数据验证功能。
        """
        # 添加有效数据
        self.test_category.add_indicator(self.test_indicator)
        self.manager.add_category(self.test_category)
        
        # 测试验证
        errors = self.manager.validate()
        self.assertEqual(len(errors), 0)
        
        # 添加无效数据
        invalid_category = IndicatorCategory(
            id="",  # 无效ID
            name="无效分类",
            description="测试"
        )
        self.manager.add_category(invalid_category)
        
        # 测试验证
        errors = self.manager.validate()
        self.assertGreater(len(errors), 0)
    
    def test_load_nonexistent_file(self):
        """
        测试加载不存在的文件
        
        验证加载不存在文件时的异常处理。
        """
        # 删除临时文件
        temp_path = Path(self.temp_file_path)
        if temp_path.exists():
            temp_path.unlink()
        
        # 测试加载不存在的文件
        with self.assertRaises(FileNotFoundError):
            self.manager.load_from_file()
    
    def test_load_invalid_json(self):
        """
        测试加载无效JSON文件
        
        验证加载无效JSON文件时的异常处理。
        """
        # 写入无效JSON
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        # 测试加载无效JSON
        with self.assertRaises(json.JSONDecodeError):
            self.manager.load_from_file()


if __name__ == '__main__':
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestIndicator))
    test_suite.addTest(unittest.makeSuite(TestIndicatorCategory))
    test_suite.addTest(unittest.makeSuite(TestIndicatorManager))
    
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