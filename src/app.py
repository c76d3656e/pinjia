#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
露天台阶爆破效果综合评价系统 - 主应用类

本模块包含系统的主应用类BlastingEvaluationApp，负责:
1. 应用程序生命周期管理
2. 视图与控制器的协调
3. 应用状态管理
4. Rio应用框架集成

作者: 开发团队
版本: 1.0.0
"""

import logging
from typing import Optional, Dict, Any

import rio

from controllers.evaluation_controller import EvaluationController
from views.main_view import MainView
from utils.config import ConfigManager


class BlastingEvaluationApp(rio.App):
    """
    露天台阶爆破效果综合评价系统主应用类
    
    继承自rio.App，负责整个应用程序的管理和协调。
    采用MVC架构模式，分离业务逻辑、数据模型和用户界面。
    
    Attributes:
        config: 配置管理器实例
        evaluation_controller: 评价控制器实例
        main_view: 主视图实例
        current_step: 当前步骤编号 (1-5)
        app_state: 应用状态字典
    """
    
    def __init__(self, config: ConfigManager):
        """
        初始化应用程序
        
        Args:
            config: 配置管理器实例
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # 初始化控制器
        self.evaluation_controller = EvaluationController()
        
        # 应用状态
        self.current_step = 1
        self.app_state: Dict[str, Any] = {
            'selected_indicators': [],
            'indicator_weights': {},
            'indicator_ranges': {},
            'measured_values': {},
            'evaluation_result': None
        }
        
        self.logger.info("应用程序初始化完成")
    
    def build(self) -> rio.Component:
        """
        构建应用程序主界面
        
        Rio框架要求的方法，返回应用程序的根组件。
        创建主视图并传入评价控制器实例。
        
        Returns:
            rio.Component: 应用程序的根组件
        """
        try:
            self.logger.info("构建应用程序界面")
            
            # 创建主视图
            self.main_view = MainView(
                controller=self.evaluation_controller,
                app_state=self.app_state
            )
            
            return self.main_view
            
        except Exception as e:
            self.logger.error(f"构建界面失败: {e}", exc_info=True)
            # 返回错误页面
            return self._build_error_page(str(e))
    
    def _build_error_page(self, error_message: str) -> rio.Component:
        """
        构建错误页面
        
        当应用程序初始化失败时显示的错误页面。
        
        Args:
            error_message: 错误信息
            
        Returns:
            rio.Component: 错误页面组件
        """
        return rio.Column(
            rio.Spacer(),
            rio.Card(
                content=rio.Column(
                    rio.Icon(
                        icon="material/error",
                        fill=rio.Color.RED,
                        width=4,
                        height=4
                    ),
                    rio.Text(
                        "应用程序启动失败",
                        style=rio.TextStyle(
                            font_size=1.5,
                            font_weight="bold"
                        ),
                        justify="center"
                    ),
                    rio.Text(
                        f"错误信息: {error_message}",
                        style=rio.TextStyle(font_size=1.0),
                        justify="center"
                    ),
                    rio.Text(
                        "请检查配置文件和依赖包是否正确安装",
                        style=rio.TextStyle(
                            font_size=0.9,
                            fill=rio.Color.GREY
                        ),
                        justify="center"
                    ),
                    spacing=1,
                    align_x=0.5
                ),
                margin=2
            ),
            rio.Spacer(),
            align_x=0.5,
            align_y=0.5
        )
    
    def get_current_step(self) -> int:
        """
        获取当前步骤编号
        
        Returns:
            int: 当前步骤编号 (1-5)
        """
        return self.current_step
    
    def set_current_step(self, step: int) -> None:
        """
        设置当前步骤编号
        
        Args:
            step: 步骤编号 (1-5)
        """
        if 1 <= step <= 5:
            self.current_step = step
            self.logger.info(f"切换到步骤 {step}")
        else:
            self.logger.warning(f"无效的步骤编号: {step}")
    
    def update_app_state(self, key: str, value: Any) -> None:
        """
        更新应用状态
        
        Args:
            key: 状态键名
            value: 状态值
        """
        self.app_state[key] = value
        self.logger.debug(f"更新应用状态: {key} = {value}")
    
    def get_app_state(self, key: str, default: Any = None) -> Any:
        """
        获取应用状态
        
        Args:
            key: 状态键名
            default: 默认值
            
        Returns:
            Any: 状态值
        """
        return self.app_state.get(key, default)
    
    def reset_app_state(self) -> None:
        """
        重置应用状态
        
        清空所有状态数据，回到初始状态。
        """
        self.app_state = {
            'selected_indicators': [],
            'indicator_weights': {},
            'indicator_ranges': {},
            'measured_values': {},
            'evaluation_result': None
        }
        self.current_step = 1
        self.logger.info("应用状态已重置")
    
    def on_app_start(self) -> None:
        """
        应用启动时的回调函数
        
        Rio框架在应用启动时调用此方法。
        可以在这里执行一些初始化操作。
        """
        self.logger.info("应用程序启动")
        
        # 加载指标体系
        try:
            self.evaluation_controller.load_indicators()
            self.logger.info("指标体系加载完成")
        except Exception as e:
            self.logger.error(f"指标体系加载失败: {e}", exc_info=True)
    
    def on_app_close(self) -> None:
        """
        应用关闭时的回调函数
        
        Rio框架在应用关闭时调用此方法。
        可以在这里执行一些清理操作。
        """
        self.logger.info("应用程序关闭")
        
        # 保存配置
        try:
            self.config.save()
            self.logger.info("配置保存完成")
        except Exception as e:
            self.logger.error(f"配置保存失败: {e}", exc_info=True)