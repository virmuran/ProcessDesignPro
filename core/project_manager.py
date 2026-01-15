#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理器 - 负责项目的创建、打开、保存和管理
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer

from config import DB_CONFIG, APP_CONFIG
from .database import DatabaseManager
from .data_sync import DataSyncEngine
from .models import ProjectInfo

class ProjectManager(QObject):
    """项目管理器"""
    
    # 信号定义
    project_created = Signal(str)      # 项目创建信号，参数：项目路径
    project_opened = Signal(str)       # 项目打开信号，参数：项目路径
    project_saved = Signal(str)        # 项目保存信号，参数：项目路径
    project_closed = Signal()          # 项目关闭信号
    data_changed = Signal(str, str, str)  # 数据变更信号 (模块名, 数据ID, 操作类型)
    sync_update = Signal(str, dict)    # 同步更新信号 (目标模块, 更新数据)
    
    def __init__(self):
        super().__init__()
        self.current_project_path = None
        self.current_project_name = None
        self.db_manager = None
        self.data_sync = None
        self.project_info = None
        self.auto_save_timer = None
        
        # 项目配置
        self.config = {
            'auto_save': True,
            'auto_save_interval': 300000,  # 5分钟，单位毫秒
            'max_backups': 10
        }
        
    # ========== 项目生命周期管理 ==========
    
    def create_project(self, name: str, path: str, description: str = "", 
                      author: str = "", company: str = "") -> Tuple[bool, str]:
        """
        创建新项目
        
        Args:
            name: 项目名称
            path: 项目保存路径
            description: 项目描述
            author: 作者
            company: 公司
            
        Returns:
            (成功状态, 消息)
        """
        try:
            # 验证项目名称
            if not name or not name.strip():
                return False, "项目名称不能为空"
                
            # 验证路径
            if not path or not os.path.exists(path):
                return False, "保存路径不存在"
                
            # 创建项目目录
            project_dir = os.path.join(path, name)
            if os.path.exists(project_dir):
                return False, "项目目录已存在"
                
            os.makedirs(project_dir)
            
            # 创建子目录
            subdirs = ['backups', 'exports', 'reports', 'attachments']
            for subdir in subdirs:
                os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)
                
            # 创建项目数据库
            db_path = os.path.join(project_dir, f"{name}.db")
            self.db_manager = DatabaseManager(db_path)
            
            # 初始化数据库
            if not self.db_manager.initialize_database():
                return False, "数据库初始化失败"
                
            # 保存项目信息
            self.project_info = ProjectInfo(
                name=name,
                description=description,
                author=author or APP_CONFIG.get('author', ''),
                company=company,
                version=APP_CONFIG.get('version', '1.0.0')
            )
            
            self.db_manager.save_project_info(self.project_info)
            
            # 保存项目配置文件
            config_data = {
                'name': name,
                'description': description,
                'author': author,
                'company': company,
                'created_date': datetime.now().isoformat(),
                'modified_date': datetime.now().isoformat(),
                'db_path': db_path,
                'app_version': APP_CONFIG.get('version', '1.0.0')
            }
            
            config_path = os.path.join(project_dir, 'project_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            # 设置当前项目
            self.current_project_path = project_dir
            self.current_project_name = name
            
            # 初始化数据同步引擎
            self.data_sync = DataSyncEngine(self.db_manager)
            
            # 连接信号
            self._connect_sync_signals()
            
            # 启动自动保存
            self._start_auto_save()
            
            print(f"项目创建成功: {project_dir}")
            self.project_created.emit(project_dir)
            return True, "项目创建成功"
            
        except Exception as e:
            error_msg = f"创建项目失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    def _connect_sync_signals(self):
        """连接数据同步信号"""
        if self.data_sync:
            self.data_sync.sync_completed.connect(self._on_sync_completed)
            self.data_sync.calculation_completed.connect(self._on_calculation_completed)
            
    def open_project(self, project_path: str) -> Tuple[bool, str]:
        """
        打开现有项目
        
        Args:
            project_path: 项目路径或项目配置文件路径
            
        Returns:
            (成功状态, 消息)
        """
        try:
            # 检查路径类型
            if project_path.endswith('.json'):
                # 项目配置文件
                config_path = project_path
                project_dir = os.path.dirname(project_path)
            else:
                # 项目目录
                project_dir = project_path
                config_path = os.path.join(project_dir, 'project_config.json')
                
            # 验证项目文件
            if not os.path.exists(config_path):
                return False, "项目配置文件不存在"
                
            # 读取项目配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # 验证数据库文件
            db_path = config_data.get('db_path')
            if not db_path or not os.path.exists(db_path):
                return False, "项目数据库文件不存在"
                
            # 连接到数据库
            self.db_manager = DatabaseManager(db_path)
            
            # 获取项目信息
            self.project_info = self.db_manager.get_project_info()
            if not self.project_info:
                return False, "项目信息读取失败"
                
            # 更新修改时间
            config_data['modified_date'] = datetime.now().isoformat()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            # 设置当前项目
            self.current_project_path = project_dir
            self.current_project_name = config_data.get('name')
            
            # 初始化数据同步引擎
            self.data_sync = DataSyncEngine(self.db_manager)
            
            # 连接信号
            self._connect_signals()
            
            # 启动自动保存
            self._start_auto_save()
            
            print(f"项目打开成功: {project_dir}")
            self.project_opened.emit(project_dir)
            return True, "项目打开成功"
            
        except Exception as e:
            error_msg = f"打开项目失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    def save_project(self, backup: bool = True) -> Tuple[bool, str]:
        """
        保存当前项目
        
        Args:
            backup: 是否创建备份
            
        Returns:
            (成功状态, 消息)
        """
        if not self.current_project_path or not self.db_manager:
            return False, "没有打开的项目"
            
        try:
            # 更新项目信息
            if self.project_info:
                self.project_info.modified_date = datetime.now().isoformat()
                self.db_manager.save_project_info(self.project_info)
                
            # 更新项目配置文件
            config_path = os.path.join(self.current_project_path, 'project_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                config_data['modified_date'] = datetime.now().isoformat()
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                    
            # 创建备份
            if backup:
                self._create_backup()
                
            print(f"项目保存成功: {self.current_project_path}")
            self.project_saved.emit(self.current_project_path)
            return True, "项目保存成功"
            
        except Exception as e:
            error_msg = f"保存项目失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    def close_project(self) -> bool:
        """关闭当前项目"""
        try:
            # 停止自动保存
            self._stop_auto_save()
            
            # 断开信号连接
            self._disconnect_signals()
            
            # 关闭数据库
            if self.db_manager:
                self.db_manager.close()
                
            # 重置状态
            self.current_project_path = None
            self.current_project_name = None
            self.db_manager = None
            self.data_sync = None
            self.project_info = None
            
            print("项目已关闭")
            self.project_closed.emit()
            return True
            
        except Exception as e:
            print(f"关闭项目失败: {e}")
            return False
            
    def delete_project(self, project_path: str) -> Tuple[bool, str]:
        """
        删除项目
        
        Args:
            project_path: 项目路径
            
        Returns:
            (成功状态, 消息)
        """
        try:
            # 安全检查
            if not os.path.exists(project_path):
                return False, "项目路径不存在"
                
            # 确认不是当前打开的项目
            if (self.current_project_path and 
                os.path.abspath(self.current_project_path) == os.path.abspath(project_path)):
                return False, "不能删除当前打开的项目"
                
            # 删除项目目录
            shutil.rmtree(project_path)
            return True, "项目删除成功"
            
        except Exception as e:
            error_msg = f"删除项目失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    # ========== 项目数据操作 ==========
    
    def add_data(self, module: str, data: Any) -> Tuple[bool, str]:
        """添加数据到指定模块"""
        if not self.db_manager:
            return False, "数据库未连接"
            
        try:
            success = False
            data_id = None
            
            if module == 'material_params' and hasattr(data, 'material_id'):
                data_id = data.material_id
                success = self.db_manager.add_material(data)
                
            elif module == 'process_materials' and hasattr(data, 'stream_id'):
                data_id = data.stream_id
                success = self.db_manager.add_process_material(data)
                
            elif module == 'process_flow' and hasattr(data, 'unit_id'):
                data_id = data.unit_id
                success = self.db_manager.add_process_unit(data)
                
            elif module == 'equipment_list' and hasattr(data, 'equipment_id'):
                data_id = data.equipment_id
                success = self.db_manager.add_equipment(data)
                
            if success and data_id and self.data_sync:
                # 触发数据同步
                data_dict = data.to_dict() if hasattr(data, 'to_dict') else data
                self.data_sync.sync_data(module, 'add', data_id, data_dict)
                self.data_changed.emit(module, data_id, 'add')
                return True, f"{module}添加成功"
                
            return False, "添加失败"
            
        except Exception as e:
            error_msg = f"添加数据失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    def calculate_all_balances(self) -> Tuple[bool, str]:
        """计算所有平衡"""
        if not self.data_sync:
            return False, "数据同步引擎未初始化"
            
        try:
            self.data_sync.calculate_all_balances()
            return True, "所有平衡计算完成"
        except Exception as e:
            return False, f"计算失败: {str(e)}"
            
    def get_data(self, module: str, data_id: str = None):
        """
        获取数据
        
        Args:
            module: 模块名
            data_id: 数据ID (为空时获取所有数据)
            
        Returns:
            数据对象或列表
        """
        if not self.db_manager:
            return None
            
        try:
            if data_id:
                # 获取单个数据
                if module == 'material_params':
                    return self.db_manager.get_material(data_id)
                elif module == 'process_materials':
                    return self.db_manager.get_process_material(data_id)
                # 其他模块...
            else:
                # 获取所有数据
                if module == 'material_params':
                    return self.db_manager.get_all_materials()
                elif module == 'process_materials':
                    return self.db_manager.get_all_process_materials()
                elif module == 'process_flow':
                    return self.db_manager.get_all_process_units()
                elif module == 'equipment_list':
                    return self.db_manager.get_all_equipment()
                elif module == 'msds_data':
                    return self.db_manager.get_module_data('msds_data')['data']
                    
            return None
            
        except Exception as e:
            print(f"获取数据失败 {module}: {e}")
            return None
            
    def update_data(self, module: str, data: Any) -> Tuple[bool, str]:
        """
        更新数据
        
        Args:
            module: 模块名
            data: 数据对象
            
        Returns:
            (成功状态, 消息)
        """
        if not self.db_manager:
            return False, "数据库未连接"
            
        try:
            data_id = None
            
            if module == 'material_params' and hasattr(data, 'material_id'):
                data_id = data.material_id
                success = self.db_manager.update_material(data)
                if success:
                    self.data_changed.emit(module, data_id, 'update')
                    # 触发数据同步
                    if self.data_sync:
                        data_dict = data.to_dict() if hasattr(data, 'to_dict') else data
                        self.data_sync.sync_data(module, 'update', data_id, data_dict)
                    return True, "物料更新成功"
                    
            # 其他模块的更新...
            
            return False, "不支持的模块或数据格式"
            
        except Exception as e:
            error_msg = f"更新数据失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    def delete_data(self, module: str, data_id: str) -> Tuple[bool, str]:
        """
        删除数据
        
        Args:
            module: 模块名
            data_id: 数据ID
            
        Returns:
            (成功状态, 消息)
        """
        if not self.db_manager:
            return False, "数据库未连接"
            
        try:
            success = False
            
            if module == 'material_params':
                success = self.db_manager.delete_material(data_id)
                if success:
                    self.data_changed.emit(module, data_id, 'delete')
                    # 触发数据同步
                    if self.data_sync:
                        self.data_sync.sync_data(module, 'delete', data_id)
                    return True, "物料删除成功"
                    
            # 其他模块的删除...
            
            return False, "删除失败"
            
        except Exception as e:
            error_msg = f"删除数据失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    # ========== 项目工具方法 ==========
    
    def export_project(self, export_path: str, format: str = 'json') -> Tuple[bool, str]:
        """
        导出项目
        
        Args:
            export_path: 导出路径
            format: 导出格式 (json, excel)
            
        Returns:
            (成功状态, 消息)
        """
        if not self.db_manager:
            return False, "数据库未连接"
            
        try:
            if format == 'json':
                success = self.db_manager.export_to_json(export_path)
                if success:
                    return True, "项目导出成功"
                else:
                    return False, "项目导出失败"
            else:
                return False, "不支持的导出格式"
                
        except Exception as e:
            error_msg = f"导出项目失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    def import_data(self, import_path: str, module: str = None) -> Tuple[bool, str]:
        """
        导入数据
        
        Args:
            import_path: 导入文件路径
            module: 目标模块 (为空时导入整个项目)
            
        Returns:
            (成功状态, 消息)
        """
        if not self.db_manager:
            return False, "数据库未连接"
            
        try:
            if module:
                # 导入指定模块数据
                # TODO: 实现模块数据导入
                return False, "模块数据导入功能暂未实现"
            else:
                # 导入整个项目
                success = self.db_manager.import_from_json(import_path)
                if success:
                    return True, "项目导入成功"
                else:
                    return False, "项目导入失败"
                    
        except Exception as e:
            error_msg = f"导入数据失败: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    def get_project_list(self, search_path: str = None) -> List[Dict[str, Any]]:
        """
        获取项目列表
        
        Args:
            search_path: 搜索路径 (为空时使用默认路径)
            
        Returns:
            项目信息列表
        """
        if not search_path:
            search_path = DB_CONFIG['default_path']
            
        projects = []
        
        try:
            if os.path.exists(search_path):
                for item in os.listdir(search_path):
                    item_path = os.path.join(search_path, item)
                    if os.path.isdir(item_path):
                        config_path = os.path.join(item_path, 'project_config.json')
                        if os.path.exists(config_path):
                            try:
                                with open(config_path, 'r', encoding='utf-8') as f:
                                    config_data = json.load(f)
                                    
                                projects.append({
                                    'name': config_data.get('name', item),
                                    'path': item_path,
                                    'description': config_data.get('description', ''),
                                    'author': config_data.get('author', ''),
                                    'created_date': config_data.get('created_date', ''),
                                    'modified_date': config_data.get('modified_date', ''),
                                    'config_path': config_path
                                })
                            except:
                                # 跳过无效的配置文件
                                pass
                                
            return sorted(projects, key=lambda x: x.get('modified_date', ''), reverse=True)
            
        except Exception as e:
            print(f"获取项目列表失败: {e}")
            return []
            
    def get_recent_projects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近打开的项目"""
        # TODO: 实现最近项目列表
        return self.get_project_list()[:limit]
        
    # ========== 内部方法 ==========
    
    def _connect_signals(self):
        """连接信号"""
        if self.data_sync:
            self.data_sync.sync_completed.connect(self._on_sync_completed)
            self.data_sync.data_updated.connect(self._on_data_updated)
            
    def _disconnect_signals(self):
        """断开信号连接"""
        if self.data_sync:
            try:
                self.data_sync.sync_completed.disconnect()
                self.data_sync.data_updated.disconnect()
            except:
                pass
                
    def _start_auto_save(self):
        """启动自动保存"""
        if self.config['auto_save'] and not self.auto_save_timer:
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self._auto_save)
            self.auto_save_timer.start(self.config['auto_save_interval'])
            
    def _stop_auto_save(self):
        """停止自动保存"""
        if self.auto_save_timer:
            self.auto_save_timer.stop()
            self.auto_save_timer = None
            
    def _auto_save(self):
        """自动保存"""
        if self.current_project_path and self.db_manager:
            print("自动保存项目...")
            self.save_project(backup=True)
            
    def _create_backup(self):
        """创建备份"""
        try:
            if not self.current_project_path:
                return
                
            backup_dir = os.path.join(self.current_project_path, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.current_project_name}_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # 备份数据库
            if self.db_manager:
                self.db_manager.backup_database(backup_path)
                
            # 清理旧的备份文件
            self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            print(f"创建备份失败: {e}")
            
    def _cleanup_old_backups(self, backup_dir: str):
        """清理旧的备份文件"""
        try:
            if not os.path.exists(backup_dir):
                return
                
            # 获取所有备份文件
            backup_files = []
            for file in os.listdir(backup_dir):
                if file.endswith('.db'):
                    file_path = os.path.join(backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
                    
            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超过最大备份数量的文件
            max_backups = self.config.get('max_backups', 10)
            for i in range(max_backups, len(backup_files)):
                file_path, _ = backup_files[i]
                try:
                    os.remove(file_path)
                    print(f"删除旧备份: {file_path}")
                except:
                    pass
                    
        except Exception as e:
            print(f"清理备份文件失败: {e}")
            
    def _on_sync_completed(self, sync_type: str, success: bool, message: str):
        """同步完成处理"""
        if success:
            self._log_message(f"数据同步完成: {sync_type}")
        else:
            self._log_message(f"数据同步失败: {sync_type} - {message}")
            
    def _on_calculation_completed(self, calc_type: str, results: Dict[str, Any]):
        """计算完成处理"""
        self._log_message(f"{calc_type}计算完成: {results.get('unit_id', 'unknown')}")
        # 发出数据变更信号，通知UI更新
        self.data_changed.emit(calc_type, results.get('unit_id', ''), 'calculated')
            
    def _on_data_updated(self, module: str, data_id: str):
        """数据更新处理"""
        print(f"数据已更新: {module} - {data_id}")
        
    # ========== 属性访问器 ==========
    
    @property
    def is_project_open(self) -> bool:
        """检查是否有项目打开"""
        return self.current_project_path is not None and self.db_manager is not None
        
    @property
    def project_directory(self) -> str:
        """获取项目目录"""
        return self.current_project_path
        
    @property
    def project_name(self) -> str:
        """获取项目名称"""
        return self.current_project_name
        
    @property
    def project_info_data(self) -> Optional[ProjectInfo]:
        """获取项目信息"""
        return self.project_info