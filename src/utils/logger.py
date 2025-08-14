#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块

提供统一的日志记录功能，支持:
1. 控制台和文件双重输出
2. 日志级别控制
3. 日志文件轮转
4. 格式化输出

作者: 开发团队
版本: 1.0.0
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file: Optional[str] = None,
    max_file_size: str = "10MB",
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    创建并配置应用程序的日志记录器，支持同时输出到控制台和文件。
    
    Args:
        name: 日志记录器名称，默认为根记录器
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否输出到文件
        log_to_console: 是否输出到控制台
        log_file: 日志文件路径，默认为logs/blasting_evaluation.log
        max_file_size: 日志文件最大大小
        backup_count: 备份文件数量
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    
    # 获取日志记录器
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_to_file:
        # 设置日志文件路径
        if log_file is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "blasting_evaluation.log"
        else:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 解析文件大小
        max_bytes = _parse_file_size(max_file_size)
        
        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志向上传播
    logger.propagate = False
    
    logger.info(f"日志系统初始化完成 - 级别: {level}, 文件: {log_to_file}, 控制台: {log_to_console}")
    
    return logger


def _parse_file_size(size_str: str) -> int:
    """
    解析文件大小字符串
    
    支持的格式:
    - 数字 (字节)
    - 数字 + 单位 (KB, MB, GB)
    
    Args:
        size_str: 文件大小字符串
        
    Returns:
        int: 文件大小（字节）
    """
    size_str = size_str.upper().strip()
    
    # 单位映射
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024
    }
    
    # 提取数字和单位
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return int(number * multiplier)
            except ValueError:
                break
    
    # 如果没有单位，假设是字节
    try:
        return int(float(size_str))
    except ValueError:
        # 默认10MB
        return 10 * 1024 * 1024


class LoggerMixin:
    """
    日志记录器混入类
    
    为其他类提供日志记录功能的混入类。
    继承此类的类可以直接使用self.logger进行日志记录。
    """
    
    @property
    def logger(self) -> logging.Logger:
        """
        获取日志记录器
        
        Returns:
            logging.Logger: 日志记录器实例
        """
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        return self._logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    设置全局日志级别
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)
    
    # 更新所有处理器的级别
    for handler in logging.getLogger().handlers:
        handler.setLevel(log_level)


def log_function_call(func):
    """
    函数调用日志装饰器
    
    记录函数的调用和返回，用于调试。
    
    Args:
        func: 被装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"调用函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数返回: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"函数异常: {func.__name__} - {e}")
            raise
    return wrapper


def log_exception(logger: logging.Logger, message: str = "发生异常"):
    """
    异常日志装饰器
    
    捕获并记录函数执行过程中的异常。
    
    Args:
        logger: 日志记录器
        message: 异常消息
        
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{message}: {func.__name__} - {e}", exc_info=True)
                raise
        return wrapper
    return decorator


class ContextLogger:
    """
    上下文日志记录器
    
    提供带上下文信息的日志记录功能。
    """
    
    def __init__(self, logger: logging.Logger, context: str):
        """
        初始化上下文日志记录器
        
        Args:
            logger: 基础日志记录器
            context: 上下文信息
        """
        self.logger = logger
        self.context = context
    
    def _log(self, level: int, message: str, *args, **kwargs):
        """
        记录带上下文的日志
        
        Args:
            level: 日志级别
            message: 日志消息
        """
        full_message = f"[{self.context}] {message}"
        self.logger.log(level, full_message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """记录DEBUG级别日志"""
        self._log(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录INFO级别日志"""
        self._log(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录WARNING级别日志"""
        self._log(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录ERROR级别日志"""
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录CRITICAL级别日志"""
        self._log(logging.CRITICAL, message, *args, **kwargs)