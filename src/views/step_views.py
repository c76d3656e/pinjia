#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
露天台阶爆破效果综合评价系统 - 步骤视图组件

本文件包含系统的各个步骤视图组件:
1. Step1View - 指标选择界面
2. Step2View - 权重设置界面
3. Step3View - 范围设置界面
4. Step4View - 实测值输入界面
5. Step5View - 综合评价界面

作者: 开发团队
版本: 1.0.0
创建时间: 2025年1月
"""

import logging
from typing import Dict, List, Optional, Any, Callable

import rio
from rio import Component

from controllers.evaluation_controller import EvaluationController
from models.indicators import Indicator, IndicatorCategory
from models.evaluation import WeightMethod, EvaluationResult
from utils.logger import LoggerMixin


class Step1View(Component, LoggerMixin):
    """
    步骤1: 指标选择界面
    
    功能职责:
    - 显示指标体系树状结构
    - 支持指标的选择和取消选择
    - 实时更新选中指标列表
    - 传递选中结果给控制器
    """
    
    def __init__(
        self,
        controller: EvaluationController,
        on_selection_change: Optional[Callable[[List[Indicator]], None]] = None
    ):
        super().__init__()
        self.controller = controller
        self.on_selection_change = on_selection_change
        self.selected_indicators: List[str] = []
        
    def build(self) -> Component:
        """构建指标选择界面"""
        try:
            categories = self.controller.get_indicator_categories()
            
            if not categories:
                return self._build_empty_state()
            
            return rio.Column(
                children=[
                    # 标题和说明
                    rio.Text(
                        "步骤1: 选择评价指标",
                        style=rio.TextStyle(
                            font_size=1.4,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "请从下方指标体系中选择需要参与评价的指标。建议每个分类至少选择一个指标。",
                        style=rio.TextStyle(font_size=0.9)
                    ),
                    rio.Separator(),
                    
                    # 指标选择区域
                    rio.ScrollContainer(
                        content=rio.Column(
                            children=[
                                self._build_category_section(category)
                                for category in categories
                            ],
                            spacing=1.5
                        ),
                        height=25
                    ),
                    
                    # 选中指标统计
                    self._build_selection_summary()
                ],
                spacing=1
            )
            
        except Exception as e:
            self.logger.error(f"构建指标选择界面失败: {e}", exc_info=True)
            return self._build_error_state(str(e))
    
    def _build_category_section(self, category: IndicatorCategory) -> Component:
        """构建指标分类区域"""
        return rio.Card(
            content=rio.Column(
                children=[
                    # 分类标题
                    rio.Row(
                        children=[
                            rio.Icon(
                                icon="material/folder",
                                width=1.2,
                                height=1.2
                            ),
                            rio.Text(
                                category.name,
                                style=rio.TextStyle(
                                    font_size=1.1,
                                    font_weight="bold"
                                )
                            ),
                            rio.Spacer(),
                            rio.Text(
                                f"{len(category.indicators)}个指标",
                                style=rio.TextStyle(
                                    font_size=0.8,
                                    fill=rio.Color.GREY
                                )
                            )
                        ],
                        spacing=0.5
                    ),
                    
                    # 指标列表
                    rio.Column(
                        children=[
                            self._build_indicator_item(indicator)
                            for indicator in category.indicators
                        ],
                        spacing=0.5
                    )
                ],
                spacing=1
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_indicator_item(self, indicator: Indicator) -> Component:
        """构建单个指标项"""
        is_selected = indicator.id in self.selected_indicators
        
        return rio.Row(
            children=[
                rio.Checkbox(
                    is_on=is_selected,
                    on_change=lambda event, ind_id=indicator.id: self._on_indicator_toggle(ind_id, event.is_on)
                ),
                rio.Column(
                    children=[
                        rio.Text(
                            indicator.name,
                            style=rio.TextStyle(
                                font_weight="bold" if is_selected else "normal"
                            )
                        ),
                        rio.Row(
                            children=[
                                rio.Text(
                                    f"单位: {indicator.unit or '无'}",
                                    style=rio.TextStyle(
                                        font_size=0.8,
                                        fill=rio.Color.GREY
                                    )
                                ),
                                rio.Text(
                                    f"类型: {'正向' if indicator.is_positive else '负向'}",
                                    style=rio.TextStyle(
                                        font_size=0.8,
                                        fill=rio.Color.GREEN if indicator.is_positive else rio.Color.RED
                                    )
                                )
                            ],
                            spacing=1
                        )
                    ],
                    spacing=0.2
                ),
                rio.Spacer()
            ],
            spacing=0.5
        )
    
    def _build_selection_summary(self) -> Component:
        """构建选中指标统计"""
        selected_count = len(self.selected_indicators)
        total_count = len(self.controller.get_all_indicators())
        
        return rio.Card(
            content=rio.Row(
                children=[
                    rio.Icon(
                        icon="material/check_circle",
                        width=1.2,
                        height=1.2,
                        fill=rio.Color.GREEN if selected_count > 0 else rio.Color.GREY
                    ),
                    rio.Text(
                        f"已选择 {selected_count} / {total_count} 个指标",
                        style=rio.TextStyle(
                            font_weight="bold",
                            fill=rio.Color.GREEN if selected_count > 0 else rio.Color.GREY
                        )
                    ),
                    rio.Spacer(),
                    rio.Button(
                        text="全选",
                        on_press=self._on_select_all,
                        style=rio.ButtonStyle.MINOR
                    ),
                    rio.Button(
                        text="清空",
                        on_press=self._on_clear_all,
                        style=rio.ButtonStyle.MINOR
                    )
                ],
                spacing=1
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_empty_state(self) -> Component:
        """构建空状态界面"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/warning",
                    width=3,
                    height=3,
                    fill=rio.Color.ORANGE
                ),
                rio.Text(
                    "未找到指标数据",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    "请检查指标配置文件是否正确加载",
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _build_error_state(self, error_message: str) -> Component:
        """构建错误状态界面"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/error",
                    width=3,
                    height=3,
                    fill=rio.Color.RED
                ),
                rio.Text(
                    "加载指标数据失败",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    error_message,
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _on_indicator_toggle(self, indicator_id: str, is_selected: bool) -> None:
        """处理指标选择状态变化"""
        try:
            if is_selected:
                if indicator_id not in self.selected_indicators:
                    self.selected_indicators.append(indicator_id)
            else:
                if indicator_id in self.selected_indicators:
                    self.selected_indicators.remove(indicator_id)
            
            # 更新控制器
            selected_indicators = [
                indicator for indicator in self.controller.get_all_indicators()
                if indicator.id in self.selected_indicators
            ]
            
            self.controller.update_selected_indicators(selected_indicators)
            
            # 通知回调
            if self.on_selection_change:
                self.on_selection_change(selected_indicators)
            
            self.logger.info(f"指标选择更新: {len(self.selected_indicators)}个指标")
            
        except Exception as e:
            self.logger.error(f"更新指标选择失败: {e}", exc_info=True)
    
    def _on_select_all(self) -> None:
        """全选所有指标"""
        try:
            all_indicators = self.controller.get_all_indicators()
            self.selected_indicators = [indicator.id for indicator in all_indicators]
            
            self.controller.update_selected_indicators(all_indicators)
            
            if self.on_selection_change:
                self.on_selection_change(all_indicators)
            
            self.force_refresh()
            
        except Exception as e:
            self.logger.error(f"全选指标失败: {e}", exc_info=True)
    
    def _on_clear_all(self) -> None:
        """清空所有选择"""
        try:
            self.selected_indicators = []
            
            self.controller.update_selected_indicators([])
            
            if self.on_selection_change:
                self.on_selection_change([])
            
            self.force_refresh()
            
        except Exception as e:
            self.logger.error(f"清空指标选择失败: {e}", exc_info=True)


class Step2View(Component, LoggerMixin):
    """
    步骤2: 权重设置界面
    
    功能职责:
    - 权重计算方法选择
    - 权重输入界面管理
    - 权重计算结果显示
    """
    
    def __init__(
        self,
        controller: EvaluationController,
        on_weights_calculated: Optional[Callable[[Dict[str, float]], None]] = None
    ):
        super().__init__()
        self.controller = controller
        self.on_weights_calculated = on_weights_calculated
        
        # 界面状态
        self.weight_method = WeightMethod.EQUAL
        self.current_view = "input"  # 'input' 或 'result'
        self.weight_results: Optional[Dict[str, float]] = None
        
        # 输入数据
        self.category_weights: Dict[str, float] = {}
        self.indicator_weights: Dict[str, float] = {}
        self.matrix_inputs: Dict[str, Dict[str, float]] = {}
    
    def build(self) -> Component:
        """构建权重设置界面"""
        try:
            selected_indicators = self.controller.get_selected_indicators()
            
            if not selected_indicators:
                return self._build_no_indicators_state()
            
            return rio.Column(
                children=[
                    # 标题和说明
                    rio.Text(
                        "步骤2: 设置指标权重",
                        style=rio.TextStyle(
                            font_size=1.4,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "请选择权重计算方法并设置相应的权重参数。",
                        style=rio.TextStyle(font_size=0.9)
                    ),
                    rio.Separator(),
                    
                    # 方法选择
                    self._build_method_selection(),
                    
                    # 主要内容区域
                    self._build_content_area()
                ],
                spacing=1
            )
            
        except Exception as e:
            self.logger.error(f"构建权重设置界面失败: {e}", exc_info=True)
            return self._build_error_state(str(e))
    
    def _build_method_selection(self) -> Component:
        """构建方法选择区域"""
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "权重计算方法",
                        style=rio.TextStyle(
                            font_size=1.1,
                            font_weight="bold"
                        )
                    ),
                    rio.Dropdown(
                        label="选择方法",
                        options=[
                            ("等权重法", WeightMethod.EQUAL),
                            ("专家打分法", WeightMethod.EXPERT),
                            ("层次分析法(AHP)", WeightMethod.AHP),
                            ("熵权法", WeightMethod.ENTROPY)
                        ],
                        selected_value=self.weight_method,
                        on_change=self._on_method_change
                    ),
                    self._build_method_description()
                ],
                spacing=0.5
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_method_description(self) -> Component:
        """构建方法说明"""
        descriptions = {
            WeightMethod.EQUAL: "所有指标权重相等，适用于各指标重要性相近的情况。",
            WeightMethod.EXPERT: "根据专家经验直接设置权重值，适用于有明确专业判断的情况。",
            WeightMethod.AHP: "通过两两比较构建判断矩阵计算权重，适用于需要系统性分析的情况。",
            WeightMethod.ENTROPY: "基于数据的变异程度自动计算权重，需要提供历史数据。"
        }
        
        return rio.Text(
            descriptions.get(self.weight_method, ""),
            style=rio.TextStyle(
                font_size=0.8,
                fill=rio.Color.GREY
            )
        )
    
    def _build_content_area(self) -> Component:
        """构建主要内容区域"""
        if self.current_view == "result" and self.weight_results:
            return self._build_result_view()
        else:
            return self._build_input_view()
    
    def _build_input_view(self) -> Component:
        """构建输入视图"""
        if self.weight_method == WeightMethod.EQUAL:
            return self._build_equal_weight_view()
        elif self.weight_method == WeightMethod.EXPERT:
            return self._build_expert_weight_view()
        elif self.weight_method == WeightMethod.AHP:
            return self._build_ahp_weight_view()
        elif self.weight_method == WeightMethod.ENTROPY:
            return self._build_entropy_weight_view()
        else:
            return rio.Text("未知的权重计算方法")
    
    def _build_equal_weight_view(self) -> Component:
        """构建等权重视图"""
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Icon(
                        icon="material/balance",
                        width=2,
                        height=2,
                        fill=rio.Color.BLUE
                    ),
                    rio.Text(
                        "等权重法",
                        style=rio.TextStyle(
                            font_size=1.2,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "所有选中的指标将被赋予相等的权重。",
                        style=rio.TextStyle(fill=rio.Color.GREY)
                    ),
                    rio.Button(
                        text="计算权重",
                        on_press=self._on_calculate_equal_weights,
                        style=rio.ButtonStyle.PRIMARY
                    )
                ],
                spacing=1,
                align_x=0.5
            ),
            margin=rio.Margin.all(1)
        )
    
    def _build_expert_weight_view(self) -> Component:
        """构建专家权重视图"""
        categories = self.controller.get_selected_categories()
        
        return rio.ScrollContainer(
            content=rio.Column(
                children=[
                    self._build_category_weight_input(category)
                    for category in categories
                ] + [
                    rio.Button(
                        text="计算权重",
                        on_press=self._on_calculate_expert_weights,
                        style=rio.ButtonStyle.PRIMARY
                    )
                ],
                spacing=1
            ),
            height=20
        )
    
    def _build_category_weight_input(self, category: IndicatorCategory) -> Component:
        """构建分类权重输入"""
        selected_indicators = [
            ind for ind in category.indicators 
            if ind.id in [si.id for si in self.controller.get_selected_indicators()]
        ]
        
        if not selected_indicators:
            return rio.Container()  # 空容器
        
        return rio.Card(
            content=rio.Column(
                children=[
                    # 分类标题
                    rio.Text(
                        category.name,
                        style=rio.TextStyle(
                            font_size=1.1,
                            font_weight="bold"
                        )
                    ),
                    
                    # 分类权重输入
                    rio.NumberInput(
                        label=f"{category.name} 权重",
                        value=self.category_weights.get(category.id, 1.0),
                        minimum=0.1,
                        maximum=10.0,
                        step=0.1,
                        on_change=lambda event, cat_id=category.id: self._on_category_weight_change(cat_id, event.value)
                    ),
                    
                    # 指标权重输入
                    rio.Text(
                        "指标权重:",
                        style=rio.TextStyle(font_weight="bold")
                    ),
                    rio.Column(
                        children=[
                            rio.NumberInput(
                                label=indicator.name,
                                value=self.indicator_weights.get(indicator.id, 1.0),
                                minimum=0.1,
                                maximum=10.0,
                                step=0.1,
                                on_change=lambda event, ind_id=indicator.id: self._on_indicator_weight_change(ind_id, event.value)
                            )
                            for indicator in selected_indicators
                        ],
                        spacing=0.5
                    )
                ],
                spacing=1
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_ahp_weight_view(self) -> Component:
        """构建AHP权重视图"""
        return rio.Text(
            "AHP方法界面开发中...",
            style=rio.TextStyle(
                font_size=1.1,
                fill=rio.Color.ORANGE
            )
        )
    
    def _build_entropy_weight_view(self) -> Component:
        """构建熵权法视图"""
        return rio.Text(
            "熵权法需要历史数据，暂未实现。",
            style=rio.TextStyle(
                font_size=1.1,
                fill=rio.Color.ORANGE
            )
        )
    
    def _build_result_view(self) -> Component:
        """构建结果视图"""
        if not self.weight_results:
            return rio.Text("无权重结果")
        
        return rio.Column(
            children=[
                rio.Row(
                    children=[
                        rio.Text(
                            "权重计算结果",
                            style=rio.TextStyle(
                                font_size=1.2,
                                font_weight="bold"
                            )
                        ),
                        rio.Spacer(),
                        rio.Button(
                            text="重新设置",
                            on_press=self._on_reset_weights,
                            style=rio.ButtonStyle.MINOR
                        )
                    ]
                ),
                
                rio.ScrollContainer(
                    content=self._build_weight_results_table(),
                    height=15
                )
            ],
            spacing=1
        )
    
    def _build_weight_results_table(self) -> Component:
        """构建权重结果表格"""
        if not self.weight_results:
            return rio.Text("无数据")
        
        rows = []
        for indicator_id, weight in self.weight_results.items():
            indicator = self.controller.get_indicator_by_id(indicator_id)
            if indicator:
                rows.append(
                    rio.Row(
                        children=[
                            rio.Text(
                                indicator.name,
                                style=rio.TextStyle(font_weight="bold")
                            ),
                            rio.Spacer(),
                            rio.Text(
                                f"{weight:.4f}",
                                style=rio.TextStyle(
                                    font_family="monospace"
                                )
                            )
                        ]
                    )
                )
        
        return rio.Column(
            children=rows,
            spacing=0.5
        )
    
    def _build_no_indicators_state(self) -> Component:
        """构建无指标状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/warning",
                    width=3,
                    height=3,
                    fill=rio.Color.ORANGE
                ),
                rio.Text(
                    "请先选择评价指标",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    "返回步骤1选择需要评价的指标",
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _build_error_state(self, error_message: str) -> Component:
        """构建错误状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/error",
                    width=3,
                    height=3,
                    fill=rio.Color.RED
                ),
                rio.Text(
                    "权重设置出错",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    error_message,
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _on_method_change(self, event) -> None:
        """处理方法变化"""
        self.weight_method = event.value
        self.current_view = "input"
        self.weight_results = None
        self.force_refresh()
    
    def _on_category_weight_change(self, category_id: str, value: float) -> None:
        """处理分类权重变化"""
        self.category_weights[category_id] = value
    
    def _on_indicator_weight_change(self, indicator_id: str, value: float) -> None:
        """处理指标权重变化"""
        self.indicator_weights[indicator_id] = value
    
    def _on_calculate_equal_weights(self) -> None:
        """计算等权重"""
        try:
            weights = self.controller.calculate_weights(
                method=WeightMethod.EQUAL
            )
            
            self.weight_results = weights
            self.current_view = "result"
            
            if self.on_weights_calculated:
                self.on_weights_calculated(weights)
            
            self.force_refresh()
            
        except Exception as e:
            self.logger.error(f"计算等权重失败: {e}", exc_info=True)
    
    def _on_calculate_expert_weights(self) -> None:
        """计算专家权重"""
        try:
            weights = self.controller.calculate_weights(
                method=WeightMethod.EXPERT,
                category_weights=self.category_weights,
                indicator_weights=self.indicator_weights
            )
            
            self.weight_results = weights
            self.current_view = "result"
            
            if self.on_weights_calculated:
                self.on_weights_calculated(weights)
            
            self.force_refresh()
            
        except Exception as e:
            self.logger.error(f"计算专家权重失败: {e}", exc_info=True)
    
    def _on_reset_weights(self) -> None:
        """重置权重设置"""
        self.current_view = "input"
        self.weight_results = None
        self.force_refresh()


class Step3View(Component, LoggerMixin):
    """
    步骤3: 指标范围设置界面
    
    功能职责:
    - 设置各指标的评价范围
    - 定义优良中差的数值区间
    """
    
    def __init__(
        self,
        controller: EvaluationController,
        on_ranges_set: Optional[Callable[[Dict[str, List[float]]], None]] = None
    ):
        super().__init__()
        self.controller = controller
        self.on_ranges_set = on_ranges_set
        self.indicator_ranges: Dict[str, List[float]] = {}
    
    def build(self) -> Component:
        """构建范围设置界面"""
        try:
            selected_indicators = self.controller.get_selected_indicators()
            
            if not selected_indicators:
                return self._build_no_indicators_state()
            
            if not self.controller.has_weights():
                return self._build_no_weights_state()
            
            return rio.Column(
                children=[
                    # 标题和说明
                    rio.Text(
                        "步骤3: 设置指标范围",
                        style=rio.TextStyle(
                            font_size=1.4,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "请为每个指标设置评价范围，定义优秀、良好、中等、较差的数值区间。",
                        style=rio.TextStyle(font_size=0.9)
                    ),
                    rio.Separator(),
                    
                    # 范围设置表格
                    rio.ScrollContainer(
                        content=rio.Column(
                            children=[
                                self._build_indicator_range_input(indicator)
                                for indicator in selected_indicators
                            ] + [
                                rio.Button(
                                    text="保存范围设置",
                                    on_press=self._on_save_ranges,
                                    style=rio.ButtonStyle.PRIMARY
                                )
                            ],
                            spacing=1
                        ),
                        height=25
                    )
                ],
                spacing=1
            )
            
        except Exception as e:
            self.logger.error(f"构建范围设置界面失败: {e}", exc_info=True)
            return self._build_error_state(str(e))
    
    def _build_indicator_range_input(self, indicator: Indicator) -> Component:
        """构建单个指标的范围输入"""
        current_ranges = self.indicator_ranges.get(indicator.id, [0, 25, 50, 75, 100])
        
        return rio.Card(
            content=rio.Column(
                children=[
                    # 指标信息
                    rio.Row(
                        children=[
                            rio.Text(
                                indicator.name,
                                style=rio.TextStyle(
                                    font_size=1.1,
                                    font_weight="bold"
                                )
                            ),
                            rio.Spacer(),
                            rio.Text(
                                f"单位: {indicator.unit or '无'}",
                                style=rio.TextStyle(
                                    font_size=0.8,
                                    fill=rio.Color.GREY
                                )
                            ),
                            rio.Text(
                                f"{'正向' if indicator.is_positive else '负向'}指标",
                                style=rio.TextStyle(
                                    font_size=0.8,
                                    fill=rio.Color.GREEN if indicator.is_positive else rio.Color.RED
                                )
                            )
                        ]
                    ),
                    
                    # 范围输入
                    rio.Text(
                        "评价范围 (从差到优):",
                        style=rio.TextStyle(font_weight="bold")
                    ),
                    rio.Row(
                        children=[
                            rio.Column(
                                children=[
                                    rio.Text("最差值", style=rio.TextStyle(font_size=0.8)),
                                    rio.NumberInput(
                                        value=current_ranges[0],
                                        on_change=lambda event, ind_id=indicator.id, idx=0: self._on_range_change(ind_id, idx, event.value)
                                    )
                                ],
                                spacing=0.2
                            ),
                            rio.Column(
                                children=[
                                    rio.Text("较差值", style=rio.TextStyle(font_size=0.8)),
                                    rio.NumberInput(
                                        value=current_ranges[1],
                                        on_change=lambda event, ind_id=indicator.id, idx=1: self._on_range_change(ind_id, idx, event.value)
                                    )
                                ],
                                spacing=0.2
                            ),
                            rio.Column(
                                children=[
                                    rio.Text("中等值", style=rio.TextStyle(font_size=0.8)),
                                    rio.NumberInput(
                                        value=current_ranges[2],
                                        on_change=lambda event, ind_id=indicator.id, idx=2: self._on_range_change(ind_id, idx, event.value)
                                    )
                                ],
                                spacing=0.2
                            ),
                            rio.Column(
                                children=[
                                    rio.Text("良好值", style=rio.TextStyle(font_size=0.8)),
                                    rio.NumberInput(
                                        value=current_ranges[3],
                                        on_change=lambda event, ind_id=indicator.id, idx=3: self._on_range_change(ind_id, idx, event.value)
                                    )
                                ],
                                spacing=0.2
                            ),
                            rio.Column(
                                children=[
                                    rio.Text("最优值", style=rio.TextStyle(font_size=0.8)),
                                    rio.NumberInput(
                                        value=current_ranges[4],
                                        on_change=lambda event, ind_id=indicator.id, idx=4: self._on_range_change(ind_id, idx, event.value)
                                    )
                                ],
                                spacing=0.2
                            )
                        ],
                        spacing=1
                    )
                ],
                spacing=1
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_no_indicators_state(self) -> Component:
        """构建无指标状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/warning",
                    width=3,
                    height=3,
                    fill=rio.Color.ORANGE
                ),
                rio.Text(
                    "请先选择评价指标",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    "返回步骤1选择需要评价的指标",
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _build_no_weights_state(self) -> Component:
        """构建无权重状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/warning",
                    width=3,
                    height=3,
                    fill=rio.Color.ORANGE
                ),
                rio.Text(
                    "请先设置指标权重",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    "返回步骤2设置指标权重",
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _build_error_state(self, error_message: str) -> Component:
        """构建错误状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/error",
                    width=3,
                    height=3,
                    fill=rio.Color.RED
                ),
                rio.Text(
                    "范围设置出错",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    error_message,
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _on_range_change(self, indicator_id: str, index: int, value: float) -> None:
        """处理范围值变化"""
        if indicator_id not in self.indicator_ranges:
            self.indicator_ranges[indicator_id] = [0, 25, 50, 75, 100]
        
        self.indicator_ranges[indicator_id][index] = value
    
    def _on_save_ranges(self) -> None:
        """保存范围设置"""
        try:
            # 验证范围设置
            if not self._validate_ranges():
                return
            
            # 保存到控制器
            self.controller.set_indicator_ranges(self.indicator_ranges)
            
            # 通知回调
            if self.on_ranges_set:
                self.on_ranges_set(self.indicator_ranges)
            
            self.logger.info("指标范围设置已保存")
            
        except Exception as e:
            self.logger.error(f"保存范围设置失败: {e}", exc_info=True)
    
    def _validate_ranges(self) -> bool:
        """验证范围设置的合理性"""
        for indicator_id, ranges in self.indicator_ranges.items():
            if len(ranges) != 5:
                return False
            
            # 检查是否递增
            for i in range(1, len(ranges)):
                if ranges[i] <= ranges[i-1]:
                    return False
        
        return True


class Step4View(Component, LoggerMixin):
    """
    步骤4: 实测值输入界面
    
    功能职责:
    - 录入各指标的实际测量值
    - 数据验证和格式检查
    """
    
    def __init__(
        self,
        controller: EvaluationController,
        on_values_set: Optional[Callable[[Dict[str, float]], None]] = None
    ):
        super().__init__()
        self.controller = controller
        self.on_values_set = on_values_set
        self.measured_values: Dict[str, float] = {}
    
    def build(self) -> Component:
        """构建实测值输入界面"""
        try:
            selected_indicators = self.controller.get_selected_indicators()
            
            if not selected_indicators:
                return self._build_no_indicators_state()
            
            if not self.controller.has_ranges():
                return self._build_no_ranges_state()
            
            return rio.Column(
                children=[
                    # 标题和说明
                    rio.Text(
                        "步骤4: 输入实测值",
                        style=rio.TextStyle(
                            font_size=1.4,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "请输入各指标的实际测量值。系统将根据设置的范围对数值进行验证。",
                        style=rio.TextStyle(font_size=0.9)
                    ),
                    rio.Separator(),
                    
                    # 实测值输入表格
                    rio.ScrollContainer(
                        content=rio.Column(
                            children=[
                                self._build_indicator_value_input(indicator)
                                for indicator in selected_indicators
                            ] + [
                                rio.Button(
                                    text="保存实测值",
                                    on_press=self._on_save_values,
                                    style=rio.ButtonStyle.PRIMARY
                                )
                            ],
                            spacing=1
                        ),
                        height=25
                    )
                ],
                spacing=1
            )
            
        except Exception as e:
            self.logger.error(f"构建实测值输入界面失败: {e}", exc_info=True)
            return self._build_error_state(str(e))
    
    def _build_indicator_value_input(self, indicator: Indicator) -> Component:
        """构建单个指标的实测值输入"""
        current_value = self.measured_values.get(indicator.id, 0.0)
        ranges = self.controller.get_indicator_ranges().get(indicator.id, [0, 25, 50, 75, 100])
        
        return rio.Card(
            content=rio.Column(
                children=[
                    # 指标信息
                    rio.Row(
                        children=[
                            rio.Text(
                                indicator.name,
                                style=rio.TextStyle(
                                    font_size=1.1,
                                    font_weight="bold"
                                )
                            ),
                            rio.Spacer(),
                            rio.Text(
                                f"单位: {indicator.unit or '无'}",
                                style=rio.TextStyle(
                                    font_size=0.8,
                                    fill=rio.Color.GREY
                                )
                            )
                        ]
                    ),
                    
                    # 范围提示
                    rio.Text(
                        f"参考范围: {ranges[0]} ~ {ranges[-1]}",
                        style=rio.TextStyle(
                            font_size=0.8,
                            fill=rio.Color.GREY
                        )
                    ),
                    
                    # 实测值输入
                    rio.NumberInput(
                        label="实测值",
                        value=current_value,
                        on_change=lambda event, ind_id=indicator.id: self._on_value_change(ind_id, event.value)
                    )
                ],
                spacing=0.5
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_no_indicators_state(self) -> Component:
        """构建无指标状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/warning",
                    width=3,
                    height=3,
                    fill=rio.Color.ORANGE
                ),
                rio.Text(
                    "请先选择评价指标",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    "返回步骤1选择需要评价的指标",
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _build_no_ranges_state(self) -> Component:
        """构建无范围状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/warning",
                    width=3,
                    height=3,
                    fill=rio.Color.ORANGE
                ),
                rio.Text(
                    "请先设置指标范围",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    "返回步骤3设置指标评价范围",
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _build_error_state(self, error_message: str) -> Component:
        """构建错误状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/error",
                    width=3,
                    height=3,
                    fill=rio.Color.RED
                ),
                rio.Text(
                    "实测值输入出错",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    error_message,
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _on_value_change(self, indicator_id: str, value: float) -> None:
        """处理实测值变化"""
        self.measured_values[indicator_id] = value
    
    def _on_save_values(self) -> None:
        """保存实测值"""
        try:
            # 验证实测值
            if not self._validate_values():
                return
            
            # 保存到控制器
            self.controller.set_measured_values(self.measured_values)
            
            # 通知回调
            if self.on_values_set:
                self.on_values_set(self.measured_values)
            
            self.logger.info("实测值已保存")
            
        except Exception as e:
            self.logger.error(f"保存实测值失败: {e}", exc_info=True)
    
    def _validate_values(self) -> bool:
        """验证实测值的有效性"""
        selected_indicators = self.controller.get_selected_indicators()
        
        for indicator in selected_indicators:
            if indicator.id not in self.measured_values:
                return False
            
            value = self.measured_values[indicator.id]
            if value is None or value < 0:
                return False
        
        return True


class Step5View(Component, LoggerMixin):
    """
    步骤5: 综合评价界面
    
    功能职责:
    - 执行综合评价计算
    - 显示评价结果
    - 生成评价报告
    """
    
    def __init__(
        self,
        controller: EvaluationController,
        on_evaluation_complete: Optional[Callable[[EvaluationResult], None]] = None
    ):
        super().__init__()
        self.controller = controller
        self.on_evaluation_complete = on_evaluation_complete
        self.evaluation_result: Optional[EvaluationResult] = None
    
    def build(self) -> Component:
        """构建综合评价界面"""
        try:
            if not self.controller.can_evaluate():
                return self._build_incomplete_state()
            
            if self.evaluation_result:
                return self._build_result_view()
            else:
                return self._build_evaluation_view()
            
        except Exception as e:
            self.logger.error(f"构建综合评价界面失败: {e}", exc_info=True)
            return self._build_error_state(str(e))
    
    def _build_evaluation_view(self) -> Component:
        """构建评价执行界面"""
        return rio.Column(
            children=[
                # 标题和说明
                rio.Text(
                    "步骤5: 综合评价",
                    style=rio.TextStyle(
                        font_size=1.4,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    "所有数据已准备完毕，点击下方按钮开始综合评价计算。",
                    style=rio.TextStyle(font_size=0.9)
                ),
                rio.Separator(),
                
                # 数据摘要
                self._build_data_summary(),
                
                # 评价按钮
                rio.Row(
                    children=[
                        rio.Spacer(),
                        rio.Button(
                            text="开始综合评价",
                            on_press=self._on_start_evaluation,
                            style=rio.ButtonStyle.PRIMARY
                        ),
                        rio.Spacer()
                    ]
                )
            ],
            spacing=2
        )
    
    def _build_data_summary(self) -> Component:
        """构建数据摘要"""
        selected_indicators = self.controller.get_selected_indicators()
        
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "评价数据摘要",
                        style=rio.TextStyle(
                            font_size=1.1,
                            font_weight="bold"
                        )
                    ),
                    
                    rio.Row(
                        children=[
                            rio.Column(
                                children=[
                                    rio.Text("选中指标", style=rio.TextStyle(font_weight="bold")),
                                    rio.Text(f"{len(selected_indicators)}个")
                                ]
                            ),
                            rio.Column(
                                children=[
                                    rio.Text("权重方法", style=rio.TextStyle(font_weight="bold")),
                                    rio.Text("已设置")
                                ]
                            ),
                            rio.Column(
                                children=[
                                    rio.Text("评价范围", style=rio.TextStyle(font_weight="bold")),
                                    rio.Text("已设置")
                                ]
                            ),
                            rio.Column(
                                children=[
                                    rio.Text("实测值", style=rio.TextStyle(font_weight="bold")),
                                    rio.Text("已输入")
                                ]
                            )
                        ],
                        spacing=2
                    )
                ],
                spacing=1
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_result_view(self) -> Component:
        """构建结果显示界面"""
        if not self.evaluation_result:
            return rio.Text("无评价结果")
        
        return rio.Column(
            children=[
                # 标题
                rio.Text(
                    "综合评价结果",
                    style=rio.TextStyle(
                        font_size=1.4,
                        font_weight="bold"
                    )
                ),
                
                # 总体评价
                self._build_overall_result(),
                
                # 详细结果
                rio.ScrollContainer(
                    content=rio.Column(
                        children=[
                            self._build_category_results(),
                            self._build_indicator_results()
                        ],
                        spacing=1
                    ),
                    height=20
                ),
                
                # 操作按钮
                rio.Row(
                    children=[
                        rio.Button(
                            text="重新评价",
                            on_press=self._on_reset_evaluation,
                            style=rio.ButtonStyle.MINOR
                        ),
                        rio.Spacer(),
                        rio.Button(
                            text="生成报告",
                            on_press=self._on_generate_report,
                            style=rio.ButtonStyle.PRIMARY
                        )
                    ]
                )
            ],
            spacing=1
        )
    
    def _build_overall_result(self) -> Component:
        """构建总体评价结果"""
        if not self.evaluation_result:
            return rio.Container()
        
        grade_colors = {
            "优秀": rio.Color.GREEN,
            "良好": rio.Color.BLUE,
            "中等": rio.Color.ORANGE,
            "较差": rio.Color.RED
        }
        
        grade_text = self.evaluation_result.overall_grade.value
        grade_color = grade_colors.get(grade_text, rio.Color.GREY)
        
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "总体评价等级",
                        style=rio.TextStyle(
                            font_size=1.2,
                            font_weight="bold"
                        )
                    ),
                    rio.Row(
                        children=[
                            rio.Text(
                                grade_text,
                                style=rio.TextStyle(
                                    font_size=2.0,
                                    font_weight="bold",
                                    fill=grade_color
                                )
                            ),
                            rio.Spacer(),
                            rio.Column(
                                children=[
                                    rio.Text(
                                        f"综合得分: {self.evaluation_result.overall_score:.2f}",
                                        style=rio.TextStyle(
                                            font_size=1.1,
                                            font_weight="bold"
                                        )
                                    ),
                                    rio.Text(
                                        f"评价时间: {self.evaluation_result.evaluation_time.strftime('%Y-%m-%d %H:%M:%S')}",
                                        style=rio.TextStyle(
                                            font_size=0.8,
                                            fill=rio.Color.GREY
                                        )
                                    )
                                ],
                                align_x=1.0
                            )
                        ]
                    )
                ],
                spacing=1
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_category_results(self) -> Component:
        """构建分类结果"""
        if not self.evaluation_result or not self.evaluation_result.category_results:
            return rio.Container()
        
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "分类评价结果",
                        style=rio.TextStyle(
                            font_size=1.1,
                            font_weight="bold"
                        )
                    )
                ] + [
                    rio.Row(
                        children=[
                            rio.Text(
                                result.category_name,
                                style=rio.TextStyle(font_weight="bold")
                            ),
                            rio.Spacer(),
                            rio.Text(
                                f"{result.weighted_score:.2f}",
                                style=rio.TextStyle(font_family="monospace")
                            ),
                            rio.Text(
                                result.grade.value,
                                style=rio.TextStyle(
                                    font_weight="bold",
                                    fill=rio.Color.GREEN if result.grade.value == "优秀" else rio.Color.BLUE
                                )
                            )
                        ]
                    )
                    for result in self.evaluation_result.category_results
                ],
                spacing=0.5
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_indicator_results(self) -> Component:
        """构建指标结果"""
        if not self.evaluation_result or not self.evaluation_result.indicator_results:
            return rio.Container()
        
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "指标评价结果",
                        style=rio.TextStyle(
                            font_size=1.1,
                            font_weight="bold"
                        )
                    )
                ] + [
                    rio.Row(
                        children=[
                            rio.Text(
                                result.indicator_name,
                                style=rio.TextStyle(font_weight="bold")
                            ),
                            rio.Spacer(),
                            rio.Text(
                                f"{result.measured_value:.2f}",
                                style=rio.TextStyle(font_family="monospace")
                            ),
                            rio.Text(
                                f"{result.score:.2f}",
                                style=rio.TextStyle(font_family="monospace")
                            ),
                            rio.Text(
                                result.grade.value,
                                style=rio.TextStyle(
                                    font_weight="bold",
                                    fill=rio.Color.GREEN if result.grade.value == "优秀" else rio.Color.BLUE
                                )
                            )
                        ]
                    )
                    for result in self.evaluation_result.indicator_results
                ],
                spacing=0.5
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_incomplete_state(self) -> Component:
        """构建数据不完整状态"""
        missing_items = []
        
        if not self.controller.get_selected_indicators():
            missing_items.append("选择评价指标")
        if not self.controller.has_weights():
            missing_items.append("设置指标权重")
        if not self.controller.has_ranges():
            missing_items.append("设置指标范围")
        if not self.controller.has_measured_values():
            missing_items.append("输入实测值")
        
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/warning",
                    width=3,
                    height=3,
                    fill=rio.Color.ORANGE
                ),
                rio.Text(
                    "数据不完整",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    f"请完成以下步骤: {', '.join(missing_items)}",
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _build_error_state(self, error_message: str) -> Component:
        """构建错误状态"""
        return rio.Column(
            children=[
                rio.Spacer(),
                rio.Icon(
                    icon="material/error",
                    width=3,
                    height=3,
                    fill=rio.Color.RED
                ),
                rio.Text(
                    "综合评价出错",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold"
                    )
                ),
                rio.Text(
                    error_message,
                    style=rio.TextStyle(fill=rio.Color.GREY)
                ),
                rio.Spacer()
            ],
            spacing=1,
            align_x=0.5
        )
    
    def _on_start_evaluation(self) -> None:
        """开始综合评价"""
        try:
            self.logger.info("开始执行综合评价...")
            
            # 执行评价计算
            result = self.controller.calculate_evaluation()
            
            if result:
                self.evaluation_result = result
                
                # 通知回调
                if self.on_evaluation_complete:
                    self.on_evaluation_complete(result)
                
                self.logger.info(f"综合评价完成，总体得分: {result.overall_score:.2f}")
                self.force_refresh()
            else:
                self.logger.error("综合评价计算失败")
                
        except Exception as e:
            self.logger.error(f"执行综合评价失败: {e}", exc_info=True)
    
    def _on_reset_evaluation(self) -> None:
        """重置评价"""
        self.evaluation_result = None
        self.force_refresh()
    
    def _on_generate_report(self) -> None:
        """生成评价报告"""
        try:
            if not self.evaluation_result:
                return
            
            # 生成报告
            report_summary = self.controller.get_evaluation_summary()
            
            self.logger.info("评价报告生成完成")
            
            # 这里可以添加报告下载或显示逻辑
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}", exc_info=True)