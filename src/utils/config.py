#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

提供应用程序配置文件的读取、写入和管理功能。
支持INI格式的配置文件，提供默认配置创建功能。

作者: 开发团队
版本: 1.0.0
"""

import configparser
import logging
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """
    配置管理器
    
    负责应用程序配置文件的管理，包括:
    1. 配置文件的读取和写入
    2. 默认配置的创建
    3. 配置项的获取和设置
    4. 配置文件的验证
    
    Attributes:
        config_file: 配置文件路径
        config: ConfigParser实例
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为config/settings.ini
        """
        self.logger = logging.getLogger(__name__)
        
        # 设置配置文件路径
        if config_file is None:
            self.config_file = Path(__file__).parent.parent.parent / "config" / "settings.ini"
        else:
            self.config_file = Path(config_file)
        
        # 确保配置目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化ConfigParser
        self.config = configparser.ConfigParser()
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """
        加载配置文件
        
        如果配置文件不存在，则创建默认配置文件。
        """
        try:
            if self.config_file.exists():
                self.config.read(self.config_file, encoding='utf-8')
                self.logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                self.logger.info("配置文件不存在，创建默认配置")
                self._create_default_config()
                self.save()
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """
        创建默认配置
        
        定义应用程序的默认配置项，包括:
        - App: 应用基本信息
        - Server: 服务器配置
        - Evaluation: 评价相关配置
        - UI: 界面配置
        """
        # 应用基本信息
        self.config['App'] = {
            'Title': '露天台阶爆破效果综合评价系统',
            'Version': '1.0.0',
            'Author': '开发团队',
            'Description': '基于Rio框架的爆破效果评价系统',
            'Theme': 'default',
            'Language': 'zh_CN',
            'Debug': 'False'
        }
        
        # 服务器配置
        self.config['Server'] = {
            'Host': 'localhost',
            'Port': '8080',
            'StartBrowser': 'True',
            'HotReload': 'True'
        }
        
        # 评价相关配置
        self.config['Evaluation'] = {
            'DefaultMethod': 'AHP',
            'Precision': '4',
            'MinIndicators': '1',
            'MaxIndicators': '20',
            'AutoSave': 'True'
        }
        
        # 界面配置
        self.config['UI'] = {
            'WindowWidth': '1200',
            'WindowHeight': '800',
            'ShowStepNumbers': 'True',
            'ShowProgress': 'True',
            'AnimationEnabled': 'True'
        }
        
        # 日志配置
        self.config['Logging'] = {
            'Level': 'INFO',
            'LogToFile': 'True',
            'LogToConsole': 'True',
            'MaxFileSize': '10MB',
            'BackupCount': '5'
        }
        
        self.logger.info("默认配置创建完成")
    
    def get(self, section: str, option: str, fallback: Any = None) -> str:
        """
        获取配置项值
        
        Args:
            section: 配置节名
            option: 配置项名
            fallback: 默认值
            
        Returns:
            str: 配置项值
        """
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.logger.warning(f"配置项不存在: [{section}] {option}，使用默认值: {fallback}")
            return fallback
    
    def getint(self, section: str, option: str, fallback: int = 0) -> int:
        """
        获取整数类型配置项值
        
        Args:
            section: 配置节名
            option: 配置项名
            fallback: 默认值
            
        Returns:
            int: 配置项值
        """
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            self.logger.warning(f"配置项不存在或格式错误: [{section}] {option}，使用默认值: {fallback}")
            return fallback
    
    def getfloat(self, section: str, option: str, fallback: float = 0.0) -> float:
        """
        获取浮点数类型配置项值
        
        Args:
            section: 配置节名
            option: 配置项名
            fallback: 默认值
            
        Returns:
            float: 配置项值
        """
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            self.logger.warning(f"配置项不存在或格式错误: [{section}] {option}，使用默认值: {fallback}")
            return fallback
    
    def getboolean(self, section: str, option: str, fallback: bool = False) -> bool:
        """
        获取布尔类型配置项值
        
        Args:
            section: 配置节名
            option: 配置项名
            fallback: 默认值
            
        Returns:
            bool: 配置项值
        """
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            self.logger.warning(f"配置项不存在或格式错误: [{section}] {option}，使用默认值: {fallback}")
            return fallback
    
    def set(self, section: str, option: str, value: Any) -> None:
        """
        设置配置项值
        
        Args:
            section: 配置节名
            option: 配置项名
            value: 配置项值
        """
        try:
            # 确保节存在
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            # 设置值
            self.config.set(section, option, str(value))
            self.logger.debug(f"配置项设置: [{section}] {option} = {value}")
            
        except Exception as e:
            self.logger.error(f"配置项设置失败: [{section}] {option} = {value}, 错误: {e}")
    
    def save(self) -> None:
        """
        保存配置到文件
        
        将当前配置写入配置文件。
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self.logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
    
    def reload(self) -> None:
        """
        重新加载配置文件
        
        从文件重新读取配置，丢弃内存中的修改。
        """
        self.config.clear()
        self._load_config()
        self.logger.info("配置文件重新加载完成")
    
    def has_section(self, section: str) -> bool:
        """
        检查配置节是否存在
        
        Args:
            section: 配置节名
            
        Returns:
            bool: 是否存在
        """
        return self.config.has_section(section)
    
    def has_option(self, section: str, option: str) -> bool:
        """
        检查配置项是否存在
        
        Args:
            section: 配置节名
            option: 配置项名
            
        Returns:
            bool: 是否存在
        """
        return self.config.has_option(section, option)
    
    def get_sections(self) -> list:
        """
        获取所有配置节名
        
        Returns:
            list: 配置节名列表
        """
        return self.config.sections()
    
    def get_options(self, section: str) -> list:
        """
        获取指定节的所有配置项名
        
        Args:
            section: 配置节名
            
        Returns:
            list: 配置项名列表
        """
        try:
            return self.config.options(section)
        except configparser.NoSectionError:
            self.logger.warning(f"配置节不存在: {section}")
            return []
    
    def validate_config(self) -> bool:
        """
        验证配置文件的完整性
        
        检查必要的配置节和配置项是否存在。
        
        Returns:
            bool: 配置是否有效
        """
        required_sections = ['App', 'Server', 'Evaluation', 'UI']
        required_options = {
            'App': ['Title', 'Version'],
            'Server': ['Host', 'Port'],
            'Evaluation': ['DefaultMethod', 'Precision'],
            'UI': ['WindowWidth', 'WindowHeight']
        }
        
        try:
            # 检查必要的节
            for section in required_sections:
                if not self.has_section(section):
                    self.logger.error(f"缺少必要的配置节: {section}")
                    return False
            
            # 检查必要的配置项
            for section, options in required_options.items():
                for option in options:
                    if not self.has_option(section, option):
                        self.logger.error(f"缺少必要的配置项: [{section}] {option}")
                        return False
            
            self.logger.info("配置文件验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"配置文件验证失败: {e}")
            return False