#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评价模型

定义爆破效果综合评价的数据结构和计算方法，包括:
1. 评价模型类 (EvaluationModel)
2. 评价结果类 (EvaluationResult)
3. 权重计算方法
4. 综合评价算法

作者: 开发团队
版本: 1.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import numpy as np
from datetime import datetime

from .indicators import Indicator, IndicatorCategory


class WeightMethod(Enum):
    """
    权重计算方法枚举
    """
    AHP = "AHP"  # 层次分析法
    ENTROPY = "Entropy"  # 熵权法
    EXPERT = "Expert"  # 专家打分法
    EQUAL = "Equal"  # 等权重法


class EvaluationGrade(Enum):
    """
    评价等级枚举
    """
    EXCELLENT = "优秀"  # 90-100
    GOOD = "良好"       # 80-89
    AVERAGE = "一般"    # 70-79
    POOR = "较差"       # 60-69
    BAD = "很差"        # 0-59


@dataclass
class EvaluationRange:
    """
    指标评价范围
    
    定义指标在不同评价等级下的数值范围。
    
    Attributes:
        excellent: 优秀范围 (min, max)
        good: 良好范围 (min, max)
        average: 一般范围 (min, max)
        poor: 较差范围 (min, max)
    """
    excellent: Tuple[float, float]
    good: Tuple[float, float]
    average: Tuple[float, float]
    poor: Tuple[float, float]
    
    def get_grade(self, value: float) -> EvaluationGrade:
        """
        根据数值获取评价等级
        
        Args:
            value: 指标值
            
        Returns:
            EvaluationGrade: 评价等级
        """
        if self.excellent[0] <= value <= self.excellent[1]:
            return EvaluationGrade.EXCELLENT
        elif self.good[0] <= value <= self.good[1]:
            return EvaluationGrade.GOOD
        elif self.average[0] <= value <= self.average[1]:
            return EvaluationGrade.AVERAGE
        elif self.poor[0] <= value <= self.poor[1]:
            return EvaluationGrade.POOR
        else:
            return EvaluationGrade.BAD
    
    def get_score(self, value: float) -> float:
        """
        根据数值获取评分 (0-100)
        
        Args:
            value: 指标值
            
        Returns:
            float: 评分
        """
        grade = self.get_grade(value)
        
        if grade == EvaluationGrade.EXCELLENT:
            return 95.0
        elif grade == EvaluationGrade.GOOD:
            return 85.0
        elif grade == EvaluationGrade.AVERAGE:
            return 75.0
        elif grade == EvaluationGrade.POOR:
            return 65.0
        else:
            return 50.0


@dataclass
class IndicatorResult:
    """
    单个指标的评价结果
    
    Attributes:
        indicator: 指标实例
        measured_value: 实测值
        weight: 权重
        score: 评分 (0-100)
        grade: 评价等级
        weighted_score: 加权评分
    """
    indicator: Indicator
    measured_value: float
    weight: float
    score: float
    grade: EvaluationGrade
    weighted_score: float


@dataclass
class CategoryResult:
    """
    分类评价结果
    
    Attributes:
        category: 分类实例
        indicator_results: 指标结果列表
        weight: 分类权重
        total_score: 分类总分
        weighted_score: 加权总分
        grade: 分类等级
    """
    category: IndicatorCategory
    indicator_results: List[IndicatorResult]
    weight: float
    total_score: float
    weighted_score: float
    grade: EvaluationGrade


@dataclass
class EvaluationResult:
    """
    综合评价结果
    
    Attributes:
        category_results: 分类结果列表
        total_score: 总分 (0-100)
        final_grade: 最终等级
        weight_method: 权重计算方法
        evaluation_time: 评价时间
        summary: 评价总结
    """
    category_results: List[CategoryResult]
    total_score: float
    final_grade: EvaluationGrade
    weight_method: WeightMethod
    evaluation_time: datetime = field(default_factory=datetime.now)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 结果数据字典
        """
        return {
            'total_score': self.total_score,
            'final_grade': self.final_grade.value,
            'weight_method': self.weight_method.value,
            'evaluation_time': self.evaluation_time.isoformat(),
            'summary': self.summary,
            'category_results': [
                {
                    'category_name': result.category.name,
                    'total_score': result.total_score,
                    'weighted_score': result.weighted_score,
                    'grade': result.grade.value,
                    'weight': result.weight,
                    'indicator_results': [
                        {
                            'indicator_name': ind_result.indicator.name,
                            'measured_value': ind_result.measured_value,
                            'score': ind_result.score,
                            'grade': ind_result.grade.value,
                            'weight': ind_result.weight,
                            'weighted_score': ind_result.weighted_score
                        }
                        for ind_result in result.indicator_results
                    ]
                }
                for result in self.category_results
            ]
        }


class EvaluationModel:
    """
    评价模型
    
    负责爆破效果的综合评价计算，包括:
    1. 指标权重管理
    2. 指标范围设置
    3. 实测值管理
    4. 综合评价计算
    
    Attributes:
        indicators: 参与评价的指标列表
        categories: 指标分类列表
        weights: 指标权重字典 {indicator_id: weight}
        category_weights: 分类权重字典 {category_id: weight}
        ranges: 指标范围字典 {indicator_id: EvaluationRange}
        measured_values: 实测值字典 {indicator_id: value}
    """
    
    def __init__(self):
        """
        初始化评价模型
        """
        self.indicators: List[Indicator] = []
        self.categories: List[IndicatorCategory] = []
        self.weights: Dict[str, float] = {}
        self.category_weights: Dict[str, float] = {}
        self.ranges: Dict[str, EvaluationRange] = {}
        self.measured_values: Dict[str, float] = {}
    
    def set_indicators(self, indicators: List[Indicator]) -> None:
        """
        设置参与评价的指标
        
        Args:
            indicators: 指标列表
        """
        self.indicators = indicators.copy()
        
        # 提取分类
        category_dict = {}
        for indicator in indicators:
            if indicator.category_id:
                if indicator.category_id not in category_dict:
                    # 创建分类（这里简化处理，实际应该从完整的分类数据创建）
                    category = IndicatorCategory(
                        id=indicator.category_id,
                        name=indicator.category_id,  # 简化处理
                        indicators=[]
                    )
                    category_dict[indicator.category_id] = category
                category_dict[indicator.category_id].indicators.append(indicator)
        
        self.categories = list(category_dict.values())
    
    def set_weights(self, weights: Dict[str, float]) -> None:
        """
        设置指标权重
        
        Args:
            weights: 权重字典 {indicator_id: weight}
        
        Raises:
            ValueError: 权重和不等于1或权重值无效
        """
        # 验证权重
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(f"权重和必须等于1，当前为: {total_weight}")
        
        for indicator_id, weight in weights.items():
            if weight < 0 or weight > 1:
                raise ValueError(f"权重值必须在0-1之间: {indicator_id} = {weight}")
        
        self.weights = weights.copy()
    
    def set_category_weights(self, category_weights: Dict[str, float]) -> None:
        """
        设置分类权重
        
        Args:
            category_weights: 分类权重字典 {category_id: weight}
        """
        self.category_weights = category_weights.copy()
    
    def set_ranges(self, ranges: Dict[str, EvaluationRange]) -> None:
        """
        设置指标评价范围
        
        Args:
            ranges: 范围字典 {indicator_id: EvaluationRange}
        """
        self.ranges = ranges.copy()
    
    def set_measured_values(self, measured_values: Dict[str, float]) -> None:
        """
        设置实测值
        
        Args:
            measured_values: 实测值字典 {indicator_id: value}
        """
        self.measured_values = measured_values.copy()
    
    def calculate_ahp_weights(
        self, 
        comparison_matrix: np.ndarray,
        items: List[str]
    ) -> Dict[str, float]:
        """
        使用层次分析法计算权重
        
        Args:
            comparison_matrix: 判断矩阵
            items: 项目列表（指标ID或分类ID）
            
        Returns:
            Dict[str, float]: 权重字典
            
        Raises:
            ValueError: 矩阵不满足一致性要求
        """
        n = len(items)
        if comparison_matrix.shape != (n, n):
            raise ValueError("判断矩阵维度不匹配")
        
        # 计算特征向量
        eigenvalues, eigenvectors = np.linalg.eig(comparison_matrix)
        max_eigenvalue = np.max(eigenvalues.real)
        max_eigenvector = eigenvectors[:, np.argmax(eigenvalues.real)].real
        
        # 归一化权重
        weights = max_eigenvector / np.sum(max_eigenvector)
        
        # 一致性检验
        ci = (max_eigenvalue - n) / (n - 1)
        ri_values = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
        ri = ri_values.get(n, 1.45)
        cr = ci / ri if ri > 0 else 0
        
        if cr > 0.1:
            raise ValueError(f"判断矩阵一致性不满足要求，CR = {cr:.3f} > 0.1")
        
        return dict(zip(items, weights))
    
    def calculate_entropy_weights(self, data_matrix: np.ndarray, items: List[str]) -> Dict[str, float]:
        """
        使用熵权法计算权重
        
        Args:
            data_matrix: 数据矩阵 (样本数 × 指标数)
            items: 指标列表
            
        Returns:
            Dict[str, float]: 权重字典
        """
        # 数据标准化
        normalized_data = data_matrix / np.sum(data_matrix, axis=0)
        
        # 计算熵值
        entropy = np.zeros(data_matrix.shape[1])
        for j in range(data_matrix.shape[1]):
            p = normalized_data[:, j]
            p = p[p > 0]  # 避免log(0)
            if len(p) > 0:
                entropy[j] = -np.sum(p * np.log(p)) / np.log(len(p))
        
        # 计算权重
        weights = (1 - entropy) / np.sum(1 - entropy)
        
        return dict(zip(items, weights))
    
    def calculate_evaluation(self, weight_method: WeightMethod) -> EvaluationResult:
        """
        执行综合评价计算
        
        Args:
            weight_method: 权重计算方法
            
        Returns:
            EvaluationResult: 评价结果
            
        Raises:
            ValueError: 数据不完整或计算错误
        """
        if not self.indicators:
            raise ValueError("未设置评价指标")
        
        if not self.weights:
            raise ValueError("未设置指标权重")
        
        if not self.ranges:
            raise ValueError("未设置指标范围")
        
        if not self.measured_values:
            raise ValueError("未设置实测值")
        
        # 计算各分类结果
        category_results = []
        
        for category in self.categories:
            indicator_results = []
            
            for indicator in category.indicators:
                if indicator.id not in self.measured_values:
                    continue
                
                measured_value = self.measured_values[indicator.id]
                weight = self.weights.get(indicator.id, 0)
                eval_range = self.ranges.get(indicator.id)
                
                if eval_range is None:
                    continue
                
                # 计算评分和等级
                score = eval_range.get_score(measured_value)
                grade = eval_range.get_grade(measured_value)
                weighted_score = score * weight
                
                indicator_result = IndicatorResult(
                    indicator=indicator,
                    measured_value=measured_value,
                    weight=weight,
                    score=score,
                    grade=grade,
                    weighted_score=weighted_score
                )
                indicator_results.append(indicator_result)
            
            if not indicator_results:
                continue
            
            # 计算分类总分
            total_score = sum(result.score * result.weight for result in indicator_results)
            category_weight = self.category_weights.get(category.id, 1.0)
            weighted_score = total_score * category_weight
            
            # 确定分类等级
            if total_score >= 90:
                category_grade = EvaluationGrade.EXCELLENT
            elif total_score >= 80:
                category_grade = EvaluationGrade.GOOD
            elif total_score >= 70:
                category_grade = EvaluationGrade.AVERAGE
            elif total_score >= 60:
                category_grade = EvaluationGrade.POOR
            else:
                category_grade = EvaluationGrade.BAD
            
            category_result = CategoryResult(
                category=category,
                indicator_results=indicator_results,
                weight=category_weight,
                total_score=total_score,
                weighted_score=weighted_score,
                grade=category_grade
            )
            category_results.append(category_result)
        
        # 计算总分
        total_score = sum(result.weighted_score for result in category_results)
        
        # 确定最终等级
        if total_score >= 90:
            final_grade = EvaluationGrade.EXCELLENT
        elif total_score >= 80:
            final_grade = EvaluationGrade.GOOD
        elif total_score >= 70:
            final_grade = EvaluationGrade.AVERAGE
        elif total_score >= 60:
            final_grade = EvaluationGrade.POOR
        else:
            final_grade = EvaluationGrade.BAD
        
        # 生成评价总结
        summary = self._generate_summary(category_results, total_score, final_grade)
        
        return EvaluationResult(
            category_results=category_results,
            total_score=total_score,
            final_grade=final_grade,
            weight_method=weight_method,
            summary=summary
        )
    
    def _generate_summary(self, category_results: List[CategoryResult], total_score: float, final_grade: EvaluationGrade) -> str:
        """
        生成评价总结
        
        Args:
            category_results: 分类结果列表
            total_score: 总分
            final_grade: 最终等级
            
        Returns:
            str: 评价总结
        """
        summary_parts = [
            f"综合评价结果: {final_grade.value} ({total_score:.2f}分)",
            "",
            "各分类评价结果:"
        ]
        
        for result in category_results:
            summary_parts.append(
                f"- {result.category.name}: {result.grade.value} ({result.total_score:.2f}分)"
            )
        
        summary_parts.extend([
            "",
            "主要特点:"
        ])
        
        # 分析各分类表现
        excellent_categories = [r for r in category_results if r.grade == EvaluationGrade.EXCELLENT]
        poor_categories = [r for r in category_results if r.grade in [EvaluationGrade.POOR, EvaluationGrade.BAD]]
        
        if excellent_categories:
            summary_parts.append(f"- 表现优秀的方面: {', '.join([r.category.name for r in excellent_categories])}")
        
        if poor_categories:
            summary_parts.append(f"- 需要改进的方面: {', '.join([r.category.name for r in poor_categories])}")
        
        return "\n".join(summary_parts)
    
    def validate_data(self) -> List[str]:
        """
        验证评价数据的完整性
        
        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors = []
        
        if not self.indicators:
            errors.append("未设置评价指标")
            return errors
        
        # 检查权重
        missing_weights = [ind.id for ind in self.indicators if ind.id not in self.weights]
        if missing_weights:
            errors.append(f"缺少权重设置的指标: {', '.join(missing_weights)}")
        
        # 检查范围
        missing_ranges = [ind.id for ind in self.indicators if ind.id not in self.ranges]
        if missing_ranges:
            errors.append(f"缺少范围设置的指标: {', '.join(missing_ranges)}")
        
        # 检查实测值
        missing_values = [ind.id for ind in self.indicators if ind.id not in self.measured_values]
        if missing_values:
            errors.append(f"缺少实测值的指标: {', '.join(missing_values)}")
        
        # 检查权重和
        if self.weights:
            total_weight = sum(self.weights.values())
            if abs(total_weight - 1.0) > 1e-6:
                errors.append(f"权重和不等于1: {total_weight:.6f}")
        
        return errors