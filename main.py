#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
露天台阶爆破效果综合评价系统 - 主入口文件

本系统基于Rio框架开发，用于对露天台阶爆破效果进行综合评价。
系统采用多步骤向导式界面，引导用户完成从指标选择到最终评价的全过程。

作者: 开发团队
版本: 1.0.0
创建时间: 2025年1月
"""

import logging
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.app import BlastingEvaluationApp
from src.utils.logger import setup_logger
from src.utils.config import ConfigManager


def main():
    """
    应用程序主入口函数
    
    功能:
    1. 初始化日志系统
    2. 加载配置文件
    3. 创建并启动应用程序
    """
    try:
        # 设置日志
        setup_logger()
        logger = logging.getLogger(__name__)
        logger.info("启动露天台阶爆破效果综合评价系统")
        
        # 加载配置
        config = ConfigManager()
        logger.info(f"配置加载完成: {config.get('App', 'Title')} v{config.get('App', 'Version')}")
        
        # 创建应用实例
        app = BlastingEvaluationApp(config)
        
        # 启动应用
        host = config.get('Server', 'Host', fallback='localhost')
        port = config.getint('Server', 'Port', fallback=8080)
        debug = config.getboolean('App', 'Debug', fallback=False)
        
        logger.info(f"启动服务器: http://{host}:{port}")
        
        # 运行应用
        app.run_in_browser(
            host=host,
            port=port,
            quiet=not debug
        )
        
    except Exception as e:
        print(f"启动失败: {e}")
        logging.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()