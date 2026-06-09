#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评价控制器

负责爆破效果评价的业务逻辑处理，包括:
1. 指标体系管理
2. 权重计算算法实现
3. 综合评价计算
4. 数据验证和处理

作者: 开发团队
版本: 1.0.0
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import numpy as np

from models.indicators import Indicator, IndicatorCategory, IndicatorManager
from models.evaluation import (
    EvaluationModel, EvaluationResult, EvaluationRange, 
    WeightMethod, EvaluationGrade
)
from utils.logger import LoggerMixin


class EvaluationController(LoggerMixin):
    """
    评价控制器
    
    系统的核心控制器，负责协调各个模块完成爆破效果评价。
    采用MVC架构中的Controller角色，处理业务逻辑。
    
    Attributes:
        indicator_manager: 指标管理器
        evaluation_model: 评价模型
        selected_indicators: 当前选中的指标列表
        current_weights: 当前权重设置
        current_ranges: 当前范围设置
        current_values: 当前实测值
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化评价控制器
        
        Args:
            config_file: 指标配置文件路径
        """
        # 初始化指标管理器
        self.indicator_manager = IndicatorManager(config_file)
        
        # 初始化评价模型
        self.evaluation_model = EvaluationModel()
        
        # 当前状态
        self.selected_indicators: List[Indicator] = []
        self.current_weights: Dict[str, float] = {}
        self.current_category_weights: Dict[str, float] = {}
        self.current_ranges: Dict[str, EvaluationRange] = {}
        self.current_values: Dict[str, float] = {}
        
        self.logger.info("评价控制器初始化完成")
    
    def load_indicators(self) -> None:
        """
        加载指标体系
        
        从配置文件加载指标体系，如果文件不存在则创建默认指标体系。
        
        Raises:
            Exception: 指标加载失败
        """
        try:
            self.indicator_manager.load_from_file()
            self.logger.info("指标体系加载成功")
        except FileNotFoundError:
            self.logger.info("指标配置文件不存在，创建默认指标体系")
            self._create_default_indicators()
            self.save_indicators()
        except Exception as e:
            self.logger.error(f"指标体系加载失败: {e}")
            raise
    
    def _create_default_indicators(self) -> None:
        """
        创建默认指标体系
        
        根据开发手册中的指标定义创建默认的指标体系。
         包含爆破质量指标、爆破安全指标、穿爆成本指标等分类。
        """
        # 爆破质量指标
        technical_category = IndicatorCategory(
            id="technical",
            name="爆破质量指标",
            description="评价爆破质量效果的相关指标"
        )
        
        technical_indicators = [
            Indicator("technical_1", "大块率", "%", "爆破后大块石料所占比例", False),
            Indicator("technical_2", "根底率", "%", "爆破后根底残留比例", False),
            Indicator("technical_6", "松散系数", "", "爆破后岩石松散程度系数", True),
            Indicator("technical_3", "后冲距离", "m", "爆破后岩石向后抛掷距离", True),
            Indicator("technical_5", "抛掷率", "%", "爆破岩石抛掷到指定区域的比例", True),
            Indicator("technical_4", "前冲距离", "m", "爆破后岩石向前抛掷距离", True)
        ]
        
        for indicator in technical_indicators:
            technical_category.add_indicator(indicator)
        
        # 爆破安全指标
        safety_category = IndicatorCategory(
            id="safety",
            name="爆破安全指标",
            description="评价爆破安全性的相关指标"
        )
        
        safety_indicators = [
            Indicator("safety_1", "最远飞石距离", "m", "爆破产生的飞石最远距离", False),
            Indicator("safety_2", "峰值振动速度", "cm/s", "爆破引起的地面振动速度峰值", False)
        ]
        
        for indicator in safety_indicators:
            safety_category.add_indicator(indicator)
        
        # 穿爆成本指标
        economic_category = IndicatorCategory(
            id="economic",
            name="穿爆成本指标",
            description="评价穿爆成本效益的相关指标"
        )
        
        economic_indicators = [
            Indicator("economic_1", "炸药单耗", "kg/m³", "单位体积岩石的炸药消耗量", False),
            Indicator("economic_2", "延米爆破量", "m³/m", "单位钻孔长度的爆破岩石量", True)
        ]
        
        for indicator in economic_indicators:
            economic_category.add_indicator(indicator)
        
        # 添加到管理器
        self.indicator_manager.add_category(technical_category)
        self.indicator_manager.add_category(safety_category)
        self.indicator_manager.add_category(economic_category)
        
        self.logger.info("默认指标体系创建完成")
    
    def save_indicators(self) -> None:
        """
        保存指标体系到文件
        
        Raises:
            Exception: 保存失败
        """
        try:
            self.indicator_manager.save_to_file()
            self.logger.info("指标体系保存成功")
        except Exception as e:
            self.logger.error(f"指标体系保存失败: {e}")
            raise
    
    def get_indicator_categories(self) -> List[IndicatorCategory]:
        """
        获取所有指标分类
        
        Returns:
            List[IndicatorCategory]: 指标分类列表
        """
        return self.indicator_manager.categories
    
    def get_all_indicators(self) -> List[Indicator]:
        """
        获取所有指标
        
        Returns:
            List[Indicator]: 指标列表
        """
        return self.indicator_manager.get_all_indicators()
    
    def get_indicator_by_id(self, indicator_id: str) -> Optional[Indicator]:
        """
        根据ID获取指标
        
        Args:
            indicator_id: 指标ID
            
        Returns:
            Optional[Indicator]: 指标实例
        """
        return self.indicator_manager.get_indicator(indicator_id)
    
    def update_selected_indicators(self, indicator_ids: List[str]) -> None:
        """
        更新选中的指标
        
        Args:
            indicator_ids: 选中的指标ID列表
            
        Raises:
            ValueError: 指标ID无效
        """
        selected_indicators = []
        
        for indicator_id in indicator_ids:
            indicator = self.indicator_manager.get_indicator(indicator_id)
            if indicator is None:
                raise ValueError(f"无效的指标ID: {indicator_id}")
            selected_indicators.append(indicator)
        
        self.selected_indicators = selected_indicators
        self.evaluation_model.set_indicators(selected_indicators)
        
        self.logger.info(f"更新选中指标: {len(selected_indicators)}个")
    
    def calculate_weights(
        self,
        method: str,
        category_weights: Optional[Dict[str, float]] = None,
        indicator_weights: Optional[Dict[str, Dict[str, float]]] = None,
        comparison_matrix: Optional[np.ndarray] = None,
        entropy_data: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        计算指标权重
        
        Args:
            method: 计算方法 ('AHP', 'Entropy', 'Expert', 'Equal')
            category_weights: 一级指标(分类)权重
            indicator_weights: 二级指标权重 {category_id: {indicator_id: weight}}
            comparison_matrix: 判断矩阵 (AHP方法使用)
            entropy_data: 熵权法样本矩阵，行是样本，列对应选中指标
            
        Returns:
            Dict[str, float]: 最终权重 {indicator_id: weight}
            
        Raises:
            ValueError: 参数无效或计算失败
        """
        if not self.selected_indicators:
            raise ValueError("未选择评价指标")
        
        weight_method = WeightMethod(method)
        
        if weight_method == WeightMethod.EQUAL:
            # 等权重法
            return self._calculate_equal_weights()
        
        elif weight_method == WeightMethod.EXPERT:
            # 专家打分法
            if category_weights is None or indicator_weights is None:
                raise ValueError("专家打分法需要提供分类权重和指标权重")
            return self._calculate_expert_weights(category_weights, indicator_weights)
        
        elif weight_method == WeightMethod.AHP:
            # 层次分析法
            if comparison_matrix is None:
                raise ValueError("AHP方法需要提供判断矩阵")
            return self._calculate_ahp_weights(comparison_matrix)
        
        elif weight_method == WeightMethod.ENTROPY:
            if entropy_data is None:
                raise ValueError("熵权法需要提供真实样本数据矩阵")
            return self._calculate_entropy_weights(entropy_data)
        
        else:
            raise ValueError(f"不支持的权重计算方法: {method}")
    
    def _calculate_equal_weights(self) -> Dict[str, float]:
        """
        计算等权重
        
        Returns:
            Dict[str, float]: 权重字典
        """
        weight = 1.0 / len(self.selected_indicators)
        weights = {indicator.id: weight for indicator in self.selected_indicators}
        
        self.logger.info("使用等权重法计算权重")
        return weights
    
    def _calculate_expert_weights(
        self,
        category_weights: Dict[str, float],
        indicator_weights: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        计算专家打分权重
        
        Args:
            category_weights: 分类权重
            indicator_weights: 指标权重
            
        Returns:
            Dict[str, float]: 最终权重
        """
        final_weights = {}
        
        # 按分类组织指标
        category_indicators = {}
        for indicator in self.selected_indicators:
            category_id = indicator.category_id
            if category_id not in category_indicators:
                category_indicators[category_id] = []
            category_indicators[category_id].append(indicator)
        
        # 计算最终权重 = 分类权重 × 指标权重
        for category_id, indicators in category_indicators.items():
            category_weight = category_weights.get(category_id, 0)
            
            for indicator in indicators:
                indicator_weight = indicator_weights.get(category_id, {}).get(indicator.id, 0)
                final_weights[indicator.id] = category_weight * indicator_weight
        
        # 归一化
        total_weight = sum(final_weights.values())
        if total_weight > 0:
            final_weights = {k: v / total_weight for k, v in final_weights.items()}
        
        self.logger.info("使用专家打分法计算权重")
        return final_weights
    
    def _calculate_ahp_weights(self, comparison_matrix: np.ndarray) -> Dict[str, float]:
        """
        计算AHP权重
        
        Args:
            comparison_matrix: 判断矩阵
            
        Returns:
            Dict[str, float]: 权重字典
        """
        indicator_ids = [indicator.id for indicator in self.selected_indicators]
        weights = self.evaluation_model.calculate_ahp_weights(comparison_matrix, indicator_ids)
        
        self.logger.info("使用AHP法计算权重")
        return weights
    
    def _calculate_entropy_weights(self, data_matrix: np.ndarray) -> Dict[str, float]:
        """
        计算熵权法权重
        
        注意: 熵权法必须基于真实样本数据，不能使用模拟数据。
        
        Returns:
            Dict[str, float]: 权重字典
        """
        indicator_ids = [indicator.id for indicator in self.selected_indicators]
        benefit_flags = [indicator.is_positive for indicator in self.selected_indicators]
        weights = self.evaluation_model.calculate_entropy_weights(data_matrix, indicator_ids, benefit_flags)
        
        self.logger.info("使用熵权法计算权重")
        return weights
    
    def set_indicator_weights(self, weights: Dict[str, float]) -> None:
        """
        设置指标权重
        
        Args:
            weights: 权重字典
        """
        self.current_weights = weights.copy()
        self.evaluation_model.set_weights(weights)
        self.logger.info(f"设置指标权重: {len(weights)}个")
    
    def set_category_weights(self, category_weights: Dict[str, float]) -> None:
        """
        设置分类权重
        
        Args:
            category_weights: 分类权重字典
        """
        self.current_category_weights = category_weights.copy()
        self.evaluation_model.set_category_weights(category_weights)
        self.logger.info(f"设置分类权重: {len(category_weights)}个")
    
    def set_indicator_ranges(self, ranges: Dict[str, Dict[str, Tuple[float, float]]]) -> None:
        """
        设置指标评价范围
        
        Args:
            ranges: 范围字典 {indicator_id: {grade: (min, max)}}
        """
        evaluation_ranges = {}
        
        for indicator_id, grade_ranges in ranges.items():
            eval_range = EvaluationRange(
                excellent=grade_ranges.get('excellent', (90, 100)),
                good=grade_ranges.get('good', (80, 89)),
                average=grade_ranges.get('average', (70, 79)),
                poor=grade_ranges.get('poor', (60, 69))
            )
            evaluation_ranges[indicator_id] = eval_range
        
        self.current_ranges = evaluation_ranges
        self.evaluation_model.set_ranges(evaluation_ranges)
        self.logger.info(f"设置指标范围: {len(evaluation_ranges)}个")
    
    def set_measured_values(self, values: Dict[str, float]) -> None:
        """
        设置实测值
        
        Args:
            values: 实测值字典
        """
        self.current_values = values.copy()
        self.evaluation_model.set_measured_values(values)
        self.logger.info(f"设置实测值: {len(values)}个")
    
    def calculate_evaluation(self, weight_method: str = "Expert") -> EvaluationResult:
        """
        执行综合评价
        
        Args:
            weight_method: 权重计算方法
            
        Returns:
            EvaluationResult: 评价结果
            
        Raises:
            ValueError: 数据不完整或计算失败
        """
        # 验证数据完整性
        errors = self.evaluation_model.validate_data()
        if errors:
            raise ValueError(f"数据验证失败: {'; '.join(errors)}")
        
        # 执行评价计算
        try:
            method = WeightMethod(weight_method)
            result = self.evaluation_model.calculate_evaluation(method)
            
            self.logger.info(f"综合评价计算完成: {result.final_grade.value} ({result.total_score:.2f}分)")
            return result
            
        except Exception as e:
            self.logger.error(f"综合评价计算失败: {e}")
            raise
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """
        获取评价状态摘要
        
        Returns:
            Dict[str, Any]: 状态摘要
        """
        return {
            'selected_indicators_count': len(self.selected_indicators),
            'weights_set': len(self.current_weights),
            'ranges_set': len(self.current_ranges),
            'values_set': len(self.current_values),
            'ready_for_evaluation': (
                len(self.selected_indicators) > 0 and
                len(self.current_weights) > 0 and
                len(self.current_ranges) > 0 and
                len(self.current_values) > 0
            )
        }
    
    def validate_evaluation_data(self) -> List[str]:
        """
        验证评价数据的完整性
        
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        if not self.selected_indicators:
            errors.append("未选择评价指标")
        
        if not self.current_weights:
            errors.append("未设置指标权重")
        
        if not self.current_ranges:
            errors.append("未设置指标范围")
        
        if not self.current_values:
            errors.append("未设置实测值")
        
        # 检查数据一致性
        if self.selected_indicators:
            selected_ids = {ind.id for ind in self.selected_indicators}
            
            missing_weights = selected_ids - set(self.current_weights.keys())
            if missing_weights:
                errors.append(f"缺少权重设置: {', '.join(missing_weights)}")
            
            missing_ranges = selected_ids - set(self.current_ranges.keys())
            if missing_ranges:
                errors.append(f"缺少范围设置: {', '.join(missing_ranges)}")
            
            missing_values = selected_ids - set(self.current_values.keys())
            if missing_values:
                errors.append(f"缺少实测值: {', '.join(missing_values)}")
        
        return errors
    
    def reset_evaluation_data(self) -> None:
        """
        重置评价数据
        
        清空所有评价相关的数据，回到初始状态。
        """
        self.selected_indicators.clear()
        self.current_weights.clear()
        self.current_category_weights.clear()
        self.current_ranges.clear()
        self.current_values.clear()
        
        # 重置评价模型
        self.evaluation_model = EvaluationModel()
        
        self.logger.info("评价数据已重置")
    
    def export_evaluation_data(self) -> Dict[str, Any]:
        """
        导出评价数据
        
        Returns:
            Dict[str, Any]: 评价数据字典
        """
        return {
            'selected_indicators': [ind.to_dict() for ind in self.selected_indicators],
            'weights': self.current_weights,
            'category_weights': self.current_category_weights,
            'ranges': {
                ind_id: {
                    'excellent': eval_range.excellent,
                    'good': eval_range.good,
                    'average': eval_range.average,
                    'poor': eval_range.poor
                }
                for ind_id, eval_range in self.current_ranges.items()
            },
            'measured_values': self.current_values
        }
    
    def import_evaluation_data(self, data: Dict[str, Any]) -> None:
        """
        导入评价数据
        
        Args:
            data: 评价数据字典
        """
        # 导入选中指标
        if 'selected_indicators' in data:
            indicators = [Indicator.from_dict(ind_data) for ind_data in data['selected_indicators']]
            self.selected_indicators = indicators
            self.evaluation_model.set_indicators(indicators)
        
        # 导入权重
        if 'weights' in data:
            self.set_indicator_weights(data['weights'])
        
        if 'category_weights' in data:
            self.set_category_weights(data['category_weights'])
        
        # 导入范围
        if 'ranges' in data:
            self.set_indicator_ranges(data['ranges'])
        
        # 导入实测值
        if 'measured_values' in data:
            self.set_measured_values(data['measured_values'])
        
        self.logger.info("评价数据导入完成")
