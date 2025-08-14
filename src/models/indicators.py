#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指标数据模型

定义爆破效果评价指标的数据结构，包括:
1. 指标类 (Indicator)
2. 指标分类类 (IndicatorCategory)
3. 相关的数据验证和操作方法

作者: 开发团队
版本: 1.0.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
from pathlib import Path


@dataclass
class Indicator:
    """
    爆破效果评价指标
    
    表示单个评价指标的数据结构，包含指标的基本信息和属性。
    
    Attributes:
        id: 指标唯一标识符
        name: 指标名称
        unit: 计量单位
        description: 指标描述
        is_positive: 是否为正向指标 (True=越大越好, False=越小越好)
        category_id: 所属分类ID
        min_value: 最小值 (可选)
        max_value: 最大值 (可选)
        default_weight: 默认权重 (可选)
    """
    
    id: str
    name: str
    unit: str = ""
    description: str = ""
    is_positive: bool = True
    category_id: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_weight: Optional[float] = None
    
    def __post_init__(self):
        """
        数据验证和初始化后处理
        """
        # 验证ID不为空
        if not self.id or not self.id.strip():
            raise ValueError("指标ID不能为空")
        
        # 验证名称不为空
        if not self.name or not self.name.strip():
            raise ValueError("指标名称不能为空")
        
        # 验证数值范围
        if (self.min_value is not None and 
            self.max_value is not None and 
            self.min_value >= self.max_value):
            raise ValueError("最小值必须小于最大值")
        
        # 验证权重范围
        if (self.default_weight is not None and 
            (self.default_weight < 0 or self.default_weight > 1)):
            raise ValueError("默认权重必须在0-1之间")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 指标数据字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'description': self.description,
            'is_positive': self.is_positive,
            'category_id': self.category_id,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'default_weight': self.default_weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Indicator':
        """
        从字典创建指标实例
        
        Args:
            data: 指标数据字典
            
        Returns:
            Indicator: 指标实例
        """
        return cls(
            id=data['id'],
            name=data['name'],
            unit=data.get('unit', ''),
            description=data.get('description', ''),
            is_positive=data.get('is_positive', True),
            category_id=data.get('category_id'),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            default_weight=data.get('default_weight')
        )
    
    def validate_value(self, value: float) -> bool:
        """
        验证指标值是否在有效范围内
        
        Args:
            value: 指标值
            
        Returns:
            bool: 是否有效
        """
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True
    
    def normalize_value(self, value: float, target_range: tuple = (0, 1)) -> float:
        """
        标准化指标值
        
        将指标值标准化到指定范围内。
        
        Args:
            value: 原始指标值
            target_range: 目标范围 (min, max)
            
        Returns:
            float: 标准化后的值
        """
        if self.min_value is None or self.max_value is None:
            return value
        
        # 线性标准化
        normalized = (value - self.min_value) / (self.max_value - self.min_value)
        
        # 映射到目标范围
        target_min, target_max = target_range
        return target_min + normalized * (target_max - target_min)
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 指标的字符串描述
        """
        unit_str = f" ({self.unit})" if self.unit else ""
        return f"{self.name}{unit_str}"
    
    def __repr__(self) -> str:
        """
        详细字符串表示
        
        Returns:
            str: 指标的详细描述
        """
        return f"Indicator(id='{self.id}', name='{self.name}', unit='{self.unit}')"


@dataclass
class IndicatorCategory:
    """
    指标分类
    
    表示指标分类的数据结构，用于组织和管理相关指标。
    
    Attributes:
        id: 分类唯一标识符
        name: 分类名称
        description: 分类描述
        indicators: 包含的指标列表
        default_weight: 默认权重 (可选)
    """
    
    id: str
    name: str
    description: str = ""
    indicators: List[Indicator] = field(default_factory=list)
    default_weight: Optional[float] = None
    
    def __post_init__(self):
        """
        数据验证和初始化后处理
        """
        # 验证ID不为空
        if not self.id or not self.id.strip():
            raise ValueError("分类ID不能为空")
        
        # 验证名称不为空
        if not self.name or not self.name.strip():
            raise ValueError("分类名称不能为空")
        
        # 验证权重范围
        if (self.default_weight is not None and 
            (self.default_weight < 0 or self.default_weight > 1)):
            raise ValueError("默认权重必须在0-1之间")
        
        # 设置指标的分类ID
        for indicator in self.indicators:
            indicator.category_id = self.id
    
    def add_indicator(self, indicator: Indicator) -> None:
        """
        添加指标到分类
        
        Args:
            indicator: 要添加的指标
        """
        # 检查指标ID是否重复
        if any(ind.id == indicator.id for ind in self.indicators):
            raise ValueError(f"指标ID重复: {indicator.id}")
        
        # 设置分类ID
        indicator.category_id = self.id
        
        # 添加到列表
        self.indicators.append(indicator)
    
    def remove_indicator(self, indicator_id: str) -> bool:
        """
        从分类中移除指标
        
        Args:
            indicator_id: 指标ID
            
        Returns:
            bool: 是否成功移除
        """
        for i, indicator in enumerate(self.indicators):
            if indicator.id == indicator_id:
                del self.indicators[i]
                return True
        return False
    
    def get_indicator(self, indicator_id: str) -> Optional[Indicator]:
        """
        根据ID获取指标
        
        Args:
            indicator_id: 指标ID
            
        Returns:
            Optional[Indicator]: 指标实例，如果不存在则返回None
        """
        for indicator in self.indicators:
            if indicator.id == indicator_id:
                return indicator
        return None
    
    def get_indicator_count(self) -> int:
        """
        获取指标数量
        
        Returns:
            int: 指标数量
        """
        return len(self.indicators)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 分类数据字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'indicators': [indicator.to_dict() for indicator in self.indicators],
            'default_weight': self.default_weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndicatorCategory':
        """
        从字典创建分类实例
        
        Args:
            data: 分类数据字典
            
        Returns:
            IndicatorCategory: 分类实例
        """
        indicators = []
        for indicator_data in data.get('indicators', []):
            indicator = Indicator.from_dict(indicator_data)
            indicators.append(indicator)
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            indicators=indicators,
            default_weight=data.get('default_weight')
        )
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 分类的字符串描述
        """
        return f"{self.name} ({len(self.indicators)}个指标)"
    
    def __repr__(self) -> str:
        """
        详细字符串表示
        
        Returns:
            str: 分类的详细描述
        """
        return f"IndicatorCategory(id='{self.id}', name='{self.name}', indicators={len(self.indicators)})"


class IndicatorManager:
    """
    指标管理器
    
    负责指标体系的管理，包括加载、保存、查询等操作。
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化指标管理器
        
        Args:
            config_file: 配置文件路径
        """
        if config_file is None:
            self.config_file = Path(__file__).parent.parent.parent / "indicators.json"
        else:
            self.config_file = Path(config_file)
        
        self.categories: List[IndicatorCategory] = []
        self.indicators: Dict[str, Indicator] = {}
    
    def load_from_file(self) -> None:
        """
        从文件加载指标体系
        
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON格式错误
            ValueError: 数据格式错误
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"指标配置文件不存在: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.categories.clear()
        self.indicators.clear()
        
        for category_data in data.get('categories', []):
            category = IndicatorCategory.from_dict(category_data)
            self.categories.append(category)
            
            # 建立指标索引
            for indicator in category.indicators:
                self.indicators[indicator.id] = indicator
    
    def save_to_file(self) -> None:
        """
        保存指标体系到文件
        
        Raises:
            IOError: 文件写入失败
        """
        # 确保目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'categories': [category.to_dict() for category in self.categories]
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def get_category(self, category_id: str) -> Optional[IndicatorCategory]:
        """
        根据ID获取分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            Optional[IndicatorCategory]: 分类实例
        """
        for category in self.categories:
            if category.id == category_id:
                return category
        return None
    
    def get_indicator(self, indicator_id: str) -> Optional[Indicator]:
        """
        根据ID获取指标
        
        Args:
            indicator_id: 指标ID
            
        Returns:
            Optional[Indicator]: 指标实例
        """
        return self.indicators.get(indicator_id)
    
    def get_all_indicators(self) -> List[Indicator]:
        """
        获取所有指标
        
        Returns:
            List[Indicator]: 指标列表
        """
        return list(self.indicators.values())
    
    def get_indicators_by_category(self, category_id: str) -> List[Indicator]:
        """
        根据分类ID获取指标列表
        
        Args:
            category_id: 分类ID
            
        Returns:
            List[Indicator]: 指标列表
        """
        category = self.get_category(category_id)
        return category.indicators if category else []
    
    def add_category(self, category: IndicatorCategory) -> None:
        """
        添加分类
        
        Args:
            category: 分类实例
            
        Raises:
            ValueError: 分类ID重复
        """
        if any(cat.id == category.id for cat in self.categories):
            raise ValueError(f"分类ID重复: {category.id}")
        
        self.categories.append(category)
        
        # 更新指标索引
        for indicator in category.indicators:
            self.indicators[indicator.id] = indicator
    
    def remove_category(self, category_id: str) -> bool:
        """
        移除分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            bool: 是否成功移除
        """
        for i, category in enumerate(self.categories):
            if category.id == category_id:
                # 从指标索引中移除
                for indicator in category.indicators:
                    self.indicators.pop(indicator.id, None)
                
                # 移除分类
                del self.categories[i]
                return True
        return False
    
    def validate_indicators(self) -> List[str]:
        """
        验证指标体系的完整性
        
        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors = []
        
        # 检查分类ID重复
        category_ids = [cat.id for cat in self.categories]
        if len(category_ids) != len(set(category_ids)):
            errors.append("存在重复的分类ID")
        
        # 检查指标ID重复
        indicator_ids = [ind.id for ind in self.indicators.values()]
        if len(indicator_ids) != len(set(indicator_ids)):
            errors.append("存在重复的指标ID")
        
        # 检查每个分类
        for category in self.categories:
            if not category.indicators:
                errors.append(f"分类 '{category.name}' 没有指标")
        
        return errors