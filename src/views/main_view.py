#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主视图组件

系统的主界面，负责整体布局和导航控制。
采用Rio框架的组件化开发模式，提供现代化的用户界面。

作者: 开发团队
版本: 1.0.0
"""

import rio
from typing import Optional, Dict, Any
from dataclasses import dataclass

from controllers.evaluation_controller import EvaluationController
from utils.logger import LoggerMixin


@dataclass
class AppState:
    """
    应用状态数据类
    
    用于在组件间共享应用状态信息。
    
    Attributes:
        current_step: 当前步骤 (1-5)
        evaluation_controller: 评价控制器实例
        is_loading: 是否正在加载
        error_message: 错误信息
        success_message: 成功信息
    """
    current_step: int = 1
    evaluation_controller: Optional[EvaluationController] = None
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""


@rio.i_know_what_im_doing
class MainView(rio.Component, LoggerMixin):
    """
    主视图组件
    
    系统的根组件，负责:
    1. 整体布局管理
    2. 步骤导航控制
    3. 状态管理
    4. 子组件协调
    
    Attributes:
        app_state: 应用状态
        step_titles: 步骤标题列表
    """
    
    # 组件状态
    app_state: AppState = AppState()
    
    def __post_init__(self):
        """
        初始化主视图组件
        """
        # 步骤标题
        self.step_titles = [
            "指标选择",
            "权重设置",
            "范围设置",
            "数据输入",
            "评价结果"
        ]

        # 初始化评价控制器
        self._initialize_controller()

        self.logger.info("主视图组件初始化完成")
    
    def _initialize_controller(self) -> None:
        """
        初始化评价控制器
        
        从应用上下文获取控制器实例并加载指标体系。
        """
        try:
            self.app_state.is_loading = True
            
            # 从应用上下文获取控制器
            from rio import get_app
            app = get_app()
            controller = app.evaluation_controller
            
            # 加载指标体系
            controller.load_indicators()
            
            self.app_state.evaluation_controller = controller
            self.app_state.success_message = "系统初始化成功"
            
        except Exception as e:
            self.logger.error(f"控制器初始化失败: {e}")
            self.app_state.error_message = f"系统初始化失败: {str(e)}"
            
        finally:
            self.app_state.is_loading = False
    
    def build(self) -> rio.Component:
        """
        构建主视图界面
        
        Returns:
            rio.Component: 主界面组件
        """
        return rio.Column(
            children=[
                # 顶部标题栏
                self._build_header(),
                
                # 步骤导航栏
                self._build_step_navigation(),
                
                # 消息提示区域
                self._build_message_area(),
                
                # 主内容区域
                self._build_main_content(),
                
                # 底部操作栏
                self._build_footer()
            ],
            spacing=1.0,
            margin=rio.Margin.all(2.0)
        )
    
    def _build_header(self) -> rio.Component:
        """
        构建顶部标题栏
        
        Returns:
            rio.Component: 标题栏组件
        """
        return rio.Card(
            content=rio.Row(
                children=[
                    # Remove icon to avoid cache issues
                    rio.Spacer(),
                    rio.Column(
                        children=[
                            rio.Text(
                                "露天台阶爆破效果综合评价系统",
                                style=rio.TextStyle(
                                    font_size=1.8,
                                    font_weight="bold"
                                )
                            ),
                            rio.Text(
                                "Open-pit Bench Blasting Effect Comprehensive Evaluation System",
                                style=rio.TextStyle(
                                    font_size=1.0,
                                    fill=rio.Color.NEUTRAL
                                )
                            )
                        ],
                        spacing=0.2
                    ),
                    rio.Spacer(),
                    rio.Button(
                        text="帮助",
                        # Remove icon to avoid cache issues
                        style=rio.ButtonStyle.MINOR,
                        on_press=self._show_help
                    )
                ],
                spacing=1.0
            ),
            margin=rio.Margin.all(1.0)
        )
    
    def _build_step_navigation(self) -> rio.Component:
        """
        构建步骤导航栏
        
        Returns:
            rio.Component: 导航栏组件
        """
        step_buttons = []
        
        for i, title in enumerate(self.step_titles, 1):
            # 确定按钮样式
            if i == self.app_state.current_step:
                style = rio.ButtonStyle.MAJOR
                prefix = "● "  # Use text instead of icon
            elif i < self.app_state.current_step:
                style = rio.ButtonStyle.MINOR
                prefix = "✓ "  # Use text instead of icon
            else:
                style = rio.ButtonStyle.PLAIN_TEXT
                prefix = "○ "  # Use text instead of icon
            
            step_buttons.append(
                rio.Button(
                    text=f"{prefix}{i}. {title}",
                    # Remove icon to avoid cache issues
                    style=style,
                    on_press=lambda step=i: self._navigate_to_step(step)
                )
            )
        
        return rio.Card(
            content=rio.Row(
                children=step_buttons,
                spacing=0.5
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _build_message_area(self) -> rio.Component:
        """
        构建消息提示区域
        
        Returns:
            rio.Component: 消息区域组件
        """
        children = []
        
        # 加载提示
        if self.app_state.is_loading:
            children.append(
                rio.Banner(
                    text="正在加载...",
                    style="info"
                )
            )
        
        # 错误消息
        if self.app_state.error_message:
            children.append(
                rio.Banner(
                    text=self.app_state.error_message,
                    style="danger"
                )
            )
        
        # 成功消息
        if self.app_state.success_message:
            children.append(
                rio.Banner(
                    text=self.app_state.success_message,
                    style="success"
                )
            )
        
        if not children:
            return rio.Spacer(height=0)
        
        return rio.Column(
            children=children,
            spacing=0.5,
            margin=rio.Margin.all(0.5)
        )
    
    def _build_main_content(self) -> rio.Component:
        """
        构建主内容区域
        
        Returns:
            rio.Component: 主内容组件
        """
        # 如果控制器未初始化，显示加载界面
        if self.app_state.evaluation_controller is None:
            return self._build_loading_content()
        
        # 根据当前步骤显示对应内容
        if self.app_state.current_step == 1:
            return self._build_indicator_selection_content()
        elif self.app_state.current_step == 2:
            return self._build_weight_setting_content()
        elif self.app_state.current_step == 3:
            return self._build_range_setting_content()
        elif self.app_state.current_step == 4:
            return self._build_data_input_content()
        elif self.app_state.current_step == 5:
            return self._build_evaluation_result_content()
        else:
            return self._build_error_content("无效的步骤")
    
    def _build_loading_content(self) -> rio.Component:
        """
        构建加载界面
        
        Returns:
            rio.Component: 加载界面组件
        """
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.ProgressIndicator(),
                    rio.Text(
                        "正在初始化系统...",
                        style=rio.TextStyle(font_size=1.2)
                    ),
                    rio.Text(
                        "请稍候",
                        style=rio.TextStyle(
                            fill=rio.Color.NEUTRAL,
                            font_size=1.0
                        )
                    )
                ],
                spacing=1.0,
                cross_axis_alignment=rio.CrossAxisAlignment.CENTER
            ),
            margin=rio.Margin.all(2.0)
        )
    
    def _build_indicator_selection_content(self) -> rio.Component:
        """
        构建指标选择界面
        
        Returns:
            rio.Component: 指标选择界面组件
        """
        # 这里暂时返回占位符，后续会创建专门的组件
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "步骤1: 指标选择",
                        style=rio.TextStyle(
                            font_size=1.5,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "请选择用于评价的指标项目。系统提供爆破质量、安全性和穿爆成本三大类指标。"
                    ),
                    rio.Spacer(height=1.0),
                    rio.Text("指标选择组件将在后续实现...")
                ],
                spacing=1.0
            ),
            margin=rio.Margin.all(1.0)
        )
    
    def _build_weight_setting_content(self) -> rio.Component:
        """
        构建权重设置界面
        
        Returns:
            rio.Component: 权重设置界面组件
        """
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "步骤2: 权重设置",
                        style=rio.TextStyle(
                            font_size=1.5,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "设置各指标的权重系数。支持专家打分法、层次分析法(AHP)、熵权法等多种方法。"
                    ),
                    rio.Spacer(height=1.0),
                    rio.Text("权重设置组件将在后续实现...")
                ],
                spacing=1.0
            ),
            margin=rio.Margin.all(1.0)
        )
    
    def _build_range_setting_content(self) -> rio.Component:
        """
        构建范围设置界面
        
        Returns:
            rio.Component: 范围设置界面组件
        """
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "步骤3: 范围设置",
                        style=rio.TextStyle(
                            font_size=1.5,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "设置各指标的评价范围。定义优秀、良好、一般、较差四个等级的数值范围。"
                    ),
                    rio.Spacer(height=1.0),
                    rio.Text("范围设置组件将在后续实现...")
                ],
                spacing=1.0
            ),
            margin=rio.Margin.all(1.0)
        )
    
    def _build_data_input_content(self) -> rio.Component:
        """
        构建数据输入界面
        
        Returns:
            rio.Component: 数据输入界面组件
        """
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "步骤4: 数据输入",
                        style=rio.TextStyle(
                            font_size=1.5,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "输入实际测量的指标数值。支持手动输入和文件导入两种方式。"
                    ),
                    rio.Spacer(height=1.0),
                    rio.Text("数据输入组件将在后续实现...")
                ],
                spacing=1.0
            ),
            margin=rio.Margin.all(1.0)
        )
    
    def _build_evaluation_result_content(self) -> rio.Component:
        """
        构建评价结果界面
        
        Returns:
            rio.Component: 评价结果界面组件
        """
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Text(
                        "步骤5: 评价结果",
                        style=rio.TextStyle(
                            font_size=1.5,
                            font_weight="bold"
                        )
                    ),
                    rio.Text(
                        "显示综合评价结果。包括总体评分、等级判定、各指标得分详情和改进建议。"
                    ),
                    rio.Spacer(height=1.0),
                    rio.Text("评价结果组件将在后续实现...")
                ],
                spacing=1.0
            ),
            margin=rio.Margin.all(1.0)
        )
    
    def _build_error_content(self, error_msg: str) -> rio.Component:
        """
        构建错误界面
        
        Args:
            error_msg: 错误信息
            
        Returns:
            rio.Component: 错误界面组件
        """
        return rio.Card(
            content=rio.Column(
                children=[
                    rio.Icon(
                        icon="material/error",
                        fill=rio.Color.DANGER
                    ),
                    rio.Text(
                        "系统错误",
                        style=rio.TextStyle(
                            font_size=1.5,
                            font_weight="bold",
                            fill=rio.Color.DANGER
                        )
                    ),
                    rio.Text(error_msg),
                    rio.Button(
                        text="重新加载",
                        icon="material/refresh",
                        on_press=self._reload_system
                    )
                ],
                spacing=1.0,
                cross_axis_alignment=rio.CrossAxisAlignment.CENTER
            ),
            margin=rio.Margin.all(2.0)
        )
    
    def _build_footer(self) -> rio.Component:
        """
        构建底部操作栏
        
        Returns:
            rio.Component: 底部操作栏组件
        """
        children = []
        
        # 上一步按钮
        if self.app_state.current_step > 1:
            children.append(
                rio.Button(
                    text="上一步",
                    icon="material/arrow_back",
                    style=rio.ButtonStyle.MINOR,
                    on_press=self._previous_step
                )
            )
        
        children.append(rio.Spacer())
        
        # 重置按钮
        children.append(
            rio.Button(
                text="重置",
                icon="material/refresh",
                style=rio.ButtonStyle.PLAIN_TEXT,
                on_press=self._reset_system
            )
        )
        
        # 下一步按钮
        if self.app_state.current_step < len(self.step_titles):
            children.append(
                rio.Button(
                    text="下一步",
                    icon="material/arrow_forward",
                    style=rio.ButtonStyle.MAJOR,
                    on_press=self._next_step
                )
            )
        
        return rio.Card(
            content=rio.Row(
                children=children,
                spacing=1.0
            ),
            margin=rio.Margin.all(0.5)
        )
    
    def _navigate_to_step(self, step: int) -> None:
        """
        导航到指定步骤
        
        Args:
            step: 目标步骤号
        """
        if 1 <= step <= len(self.step_titles):
            self.app_state.current_step = step
            self._clear_messages()
            self.logger.info(f"导航到步骤 {step}: {self.step_titles[step-1]}")
    
    def _previous_step(self) -> None:
        """
        返回上一步
        """
        if self.app_state.current_step > 1:
            self.app_state.current_step -= 1
            self._clear_messages()
    
    def _next_step(self) -> None:
        """
        进入下一步
        """
        if self.app_state.current_step < len(self.step_titles):
            self.app_state.current_step += 1
            self._clear_messages()
    
    def _show_help(self) -> None:
        """
        显示帮助信息
        """
        self.app_state.success_message = "帮助功能将在后续版本中实现"
    
    def _reload_system(self) -> None:
        """
        重新加载系统
        """
        self._clear_messages()
        self._initialize_controller()
    
    def _reset_system(self) -> None:
        """
        重置系统状态
        """
        if self.app_state.evaluation_controller:
            self.app_state.evaluation_controller.reset_evaluation_data()
        
        self.app_state.current_step = 1
        self._clear_messages()
        self.app_state.success_message = "系统已重置"
        
        self.logger.info("系统状态已重置")
    
    def _clear_messages(self) -> None:
        """
        清空消息提示
        """
        self.app_state.error_message = ""
        self.app_state.success_message = ""
    
    def get_evaluation_controller(self) -> Optional[EvaluationController]:
        """
        获取评价控制器实例
        
        Returns:
            Optional[EvaluationController]: 控制器实例
        """
        return self.app_state.evaluation_controller
    
    def set_error_message(self, message: str) -> None:
        """
        设置错误消息
        
        Args:
            message: 错误消息
        """
        self.app_state.error_message = message
        self.app_state.success_message = ""
    
    def set_success_message(self, message: str) -> None:
        """
        设置成功消息
        
        Args:
            message: 成功消息
        """
        self.app_state.success_message = message
        self.app_state.error_message = ""
    
    def set_loading(self, loading: bool) -> None:
        """
        设置加载状态
        
        Args:
            loading: 是否正在加载
        """
        self.app_state.is_loading = loading