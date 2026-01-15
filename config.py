#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工艺设计程序配置文件
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.absolute()

# 数据库配置
DB_CONFIG = {
    'default_path': BASE_DIR / 'data' / 'projects',
    'template_path': BASE_DIR / 'data' / 'templates',
    'backup_path': BASE_DIR / 'data' / 'backups'
}

# 应用配置
APP_CONFIG = {
    'name': '工艺设计程序',
    'version': '1.0.0',
    'author': '工艺设计团队',
    'default_units': {
        'temperature': '°C',
        'pressure': 'bar',
        'flow_rate': 'kg/h',
        'density': 'kg/m³',
        'viscosity': 'Pa·s'
    }
}

# 创建必要的目录
def create_directories():
    """创建必要的项目目录"""
    directories = [
        DB_CONFIG['default_path'],
        DB_CONFIG['template_path'],
        DB_CONFIG['backup_path'],
        BASE_DIR / 'data' / 'reports',
        BASE_DIR / 'logs'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"确保目录存在: {directory}")

# 初始化时创建目录
create_directories()