import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

from core.database import DatabaseManager
from core.data_sync import DataSyncEngine

class ProjectManager(QObject):
    """项目管理器，负责项目的创建、打开、保存等操作"""
    
    project_loaded = Signal(str)  # 项目加载信号
    project_saved = Signal(str)   # 项目保存信号
    data_changed = Signal(str, str)  # 数据变更信号 (模块名, 变更类型)
    
    def __init__(self):
        super().__init__()
        self.current_project = None
        self.project_path = None
        self.db_manager = None
        self.data_sync = DataSyncEngine()
        
    def create_project(self, name: str, path: str, description: str = "") -> bool:
        """创建新项目"""
        # 创建项目目录
        project_dir = os.path.join(path, name)
        if os.path.exists(project_dir):
            return False
            
        os.makedirs(project_dir)
        
        # 创建项目数据库
        db_path = os.path.join(project_dir, f"{name}.db")
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize_database()
        
        # 保存项目信息
        project_info = {
            "name": name,
            "description": description,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "db_path": db_path
        }
        
        info_path = os.path.join(project_dir, "project_info.json")
        with open(info_path, "w") as f:
            json.dump(project_info, f, indent=2)
            
        self.current_project = name
        self.project_path = project_dir
        
        # 初始化数据同步
        self.data_sync.initialize(self.db_manager)
        
        self.project_loaded.emit(name)
        return True
        
    def open_project(self, project_file: str) -> bool:
        """打开现有项目"""
        try:
            with open(project_file, "r") as f:
                project_info = json.load(f)
                
            # 连接到项目数据库
            db_path = project_info.get("db_path")
            if not db_path or not os.path.exists(db_path):
                return False
                
            self.db_manager = DatabaseManager(db_path)
            self.current_project = project_info.get("name")
            self.project_path = os.path.dirname(project_file)
            
            # 初始化数据同步
            self.data_sync.initialize(self.db_manager)
            
            self.project_loaded.emit(self.current_project)
            return True
            
        except Exception as e:
            print(f"打开项目失败: {e}")
            return False
            
    def save_project(self):
        """保存项目"""
        if not self.current_project:
            return
            
        # 更新项目信息
        info_path = os.path.join(self.project_path, "project_info.json")
        if os.path.exists(info_path):
            with open(info_path, "r") as f:
                project_info = json.load(f)
                
            project_info["modified"] = datetime.now().isoformat()
            
            with open(info_path, "w") as f:
                json.dump(project_info, f, indent=2)
                
        self.project_saved.emit(self.current_project)
        
    def get_project_data(self, module: str) -> Dict[str, Any]:
        """获取指定模块的数据"""
        if not self.db_manager:
            return {}
        return self.db_manager.get_module_data(module)
        
    def update_project_data(self, module: str, data: Dict[str, Any]):
        """更新指定模块的数据"""
        if not self.db_manager:
            return
            
        self.db_manager.update_module_data(module, data)
        
        # 通知数据同步引擎
        self.data_changed.emit(module, "update")
        
        # 触发相关模块的同步更新
        self.data_sync.sync_data(module, data)