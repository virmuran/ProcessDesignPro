#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器 - SQLite数据库操作核心
"""

import sqlite3
import json
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

from config import DB_CONFIG
from .models import *

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """连接到数据库"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # 返回字典格式的结果
        self.cursor = self.connection.cursor()
        
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            
    def initialize_database(self):
        """初始化数据库表结构"""
        try:
            # 启用外键约束
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            # 项目信息表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT DEFAULT '1.0.0',
                    author TEXT,
                    company TEXT,
                    created_date TEXT,
                    modified_date TEXT
                )
            ''')
            
            # 物料参数表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_params (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    chemical_formula TEXT,
                    molar_mass REAL,
                    density REAL,
                    viscosity REAL,
                    specific_heat REAL,
                    thermal_conductivity REAL,
                    safety_class TEXT,
                    storage_conditions TEXT,
                    properties_json TEXT,
                    created_date TEXT,
                    modified_date TEXT
                )
            ''')
            
            # MSDS数据表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS msds_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_id TEXT NOT NULL,
                    msds_number TEXT,
                    hazard_classification TEXT,
                    precautionary_statements TEXT,
                    first_aid_measures TEXT,
                    fire_fighting_measures TEXT,
                    accidental_release_measures TEXT,
                    handling_and_storage TEXT,
                    exposure_controls TEXT,
                    stability_and_reactivity TEXT,
                    toxicological_information TEXT,
                    ecological_information TEXT,
                    disposal_considerations TEXT,
                    transport_information TEXT,
                    regulatory_information TEXT,
                    other_information TEXT,
                    FOREIGN KEY (material_id) REFERENCES material_params (material_id) ON DELETE CASCADE
                )
            ''')
            
            # 过程物料表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    phase TEXT,
                    temperature REAL,
                    pressure REAL,
                    flow_rate REAL,
                    composition_json TEXT,
                    source_unit TEXT,
                    destination_unit TEXT,
                    properties_json TEXT,
                    created_date TEXT,
                    modified_date TEXT
                )
            ''')
            
            # 工艺路线表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_flow (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT,
                    description TEXT,
                    position_x REAL,
                    position_y REAL,
                    connections_json TEXT,
                    parameters_json TEXT,
                    created_date TEXT,
                    modified_date TEXT
                )
            ''')
            
            # 设备清单表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT,
                    model TEXT,
                    specifications_json TEXT,
                    quantity INTEGER,
                    material_of_construction TEXT,
                    operating_conditions_json TEXT,
                    utility_requirements_json TEXT,
                    manufacturer TEXT,
                    created_date TEXT,
                    modified_date TEXT
                )
            ''')
            
            # 物料平衡表（更新）
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id TEXT NOT NULL,
                    input_streams_json TEXT,
                    output_streams_json TEXT,
                    conversion_rate REAL,
                    yield REAL,
                    losses_json TEXT,
                    calculated_data_json TEXT,
                    balance_status TEXT DEFAULT 'pending',
                    tolerance REAL DEFAULT 0.01,
                    created_date TEXT,
                    modified_date TEXT,
                    FOREIGN KEY (unit_id) REFERENCES process_flow (unit_id) ON DELETE CASCADE
                )
            ''')
            
            # 热量平衡表（更新）
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS heat_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id TEXT NOT NULL,
                    input_heat_json TEXT,
                    output_heat_json TEXT,
                    heat_loss REAL,
                    efficiency REAL,
                    utility_requirements_json TEXT,
                    calculated_data_json TEXT,
                    balance_status TEXT DEFAULT 'pending',
                    created_date TEXT,
                    modified_date TEXT,
                    FOREIGN KEY (unit_id) REFERENCES process_flow (unit_id) ON DELETE CASCADE
                )
            ''')
            
            # 水平衡表（更新）
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS water_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id TEXT NOT NULL,
                    fresh_water_in REAL,
                    recycled_water_in REAL,
                    water_consumption REAL,
                    wastewater_out REAL,
                    reuse_possibilities TEXT,
                    calculated_data_json TEXT,
                    created_date TEXT,
                    modified_date TEXT,
                    FOREIGN KEY (unit_id) REFERENCES process_flow (unit_id) ON DELETE CASCADE
                )
            ''')
            
            # 数据版本控制表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_name TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    data_hash TEXT,
                    change_description TEXT,
                    changed_by TEXT,
                    changed_date TEXT
                )
            ''')
            
            # 数据关系表（用于跟踪数据间的依赖关系）
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_module TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_module TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT,
                    created_date TEXT
                )
            ''')
            
            self.connection.commit()
            print(f"数据库初始化成功: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            self.connection.rollback()
            return False
            
    # ========== 项目信息操作 ==========
    
    def save_project_info(self, project_info: ProjectInfo) -> bool:
        """保存项目信息"""
        try:
            # 首先删除旧的项目信息（只保留一条）
            self.cursor.execute("DELETE FROM project_info")
            
            # 插入新的项目信息
            data = project_info.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            query = f"INSERT INTO project_info ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"保存项目信息失败: {e}")
            self.connection.rollback()
            return False
            
    def get_project_info(self) -> Optional[ProjectInfo]:
        """获取项目信息"""
        try:
            self.cursor.execute("SELECT * FROM project_info LIMIT 1")
            row = self.cursor.fetchone()
            
            if row:
                return ProjectInfo(**dict(row))
            return None
            
        except Exception as e:
            print(f"获取项目信息失败: {e}")
            return None
            
    # ========== 物料参数操作 ==========
    
    def add_material(self, material: MaterialParameter) -> bool:
        """添加物料参数"""
        try:
            data = material.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            query = f"INSERT INTO material_params ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"添加物料参数失败: {e}")
            self.connection.rollback()
            return False
            
    def update_material(self, material: MaterialParameter) -> bool:
        """更新物料参数"""
        try:
            data = material.to_dict()
            data['modified_date'] = datetime.now().isoformat()
            
            # 构建SET子句
            set_clause = ', '.join([f"{k}=?" for k in data.keys() if k != 'material_id'])
            values = [v for k, v in data.items() if k != 'material_id']
            values.append(material.material_id)  # WHERE子句的参数
            
            query = f"UPDATE material_params SET {set_clause} WHERE material_id=?"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"更新物料参数失败: {e}")
            self.connection.rollback()
            return False
            
    def delete_material(self, material_id: str) -> bool:
        """删除物料参数"""
        try:
            query = "DELETE FROM material_params WHERE material_id=?"
            self.cursor.execute(query, (material_id,))
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"删除物料参数失败: {e}")
            self.connection.rollback()
            return False
            
    def get_material(self, material_id: str) -> Optional[MaterialParameter]:
        """获取单个物料参数"""
        try:
            query = "SELECT * FROM material_params WHERE material_id=?"
            self.cursor.execute(query, (material_id,))
            row = self.cursor.fetchone()
            
            if row:
                return MaterialParameter.from_dict(dict(row))
            return None
            
        except Exception as e:
            print(f"获取物料参数失败: {e}")
            return None
            
    def get_all_materials(self) -> List[MaterialParameter]:
        """获取所有物料参数"""
        try:
            query = "SELECT * FROM material_params ORDER BY name"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            materials = []
            for row in rows:
                materials.append(MaterialParameter.from_dict(dict(row)))
            return materials
            
        except Exception as e:
            print(f"获取所有物料参数失败: {e}")
            return []
            
    # ========== MSDS数据操作 ==========
    
    def add_msds(self, msds: MSDSData) -> bool:
        """添加MSDS数据"""
        try:
            data = msds.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            query = f"INSERT INTO msds_data ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"添加MSDS数据失败: {e}")
            self.connection.rollback()
            return False
            
    def get_msds(self, material_id: str) -> Optional[MSDSData]:
        """获取MSDS数据"""
        try:
            query = "SELECT * FROM msds_data WHERE material_id=?"
            self.cursor.execute(query, (material_id,))
            row = self.cursor.fetchone()
            
            if row:
                return MSDSData(**dict(row))
            return None
            
        except Exception as e:
            print(f"获取MSDS数据失败: {e}")
            return None
            
    # ========== 过程物料操作 ==========
    
    def add_process_material(self, material: ProcessMaterial) -> bool:
        """添加过程物料"""
        try:
            data = material.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            query = f"INSERT INTO process_materials ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"添加过程物料失败: {e}")
            self.connection.rollback()
            return False
            
    def get_process_material(self, stream_id: str) -> Optional[ProcessMaterial]:
        """获取单个过程物料"""
        try:
            query = "SELECT * FROM process_materials WHERE stream_id=?"
            self.cursor.execute(query, (stream_id,))
            row = self.cursor.fetchone()
            
            if row:
                return ProcessMaterial.from_dict(dict(row))
            return None
            
        except Exception as e:
            print(f"获取过程物料失败: {e}")
            return None
            
    def get_all_process_materials(self) -> List[ProcessMaterial]:
        """获取所有过程物料"""
        try:
            query = "SELECT * FROM process_materials ORDER BY name"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            materials = []
            for row in rows:
                materials.append(ProcessMaterial.from_dict(dict(row)))
            return materials
            
        except Exception as e:
            print(f"获取所有过程物料失败: {e}")
            return []
            
    # ========== 工艺路线操作 ==========
    
    def add_process_unit(self, unit: ProcessUnit) -> bool:
        """添加工艺单元"""
        try:
            data = unit.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            query = f"INSERT INTO process_flow ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"添加工艺单元失败: {e}")
            self.connection.rollback()
            return False
            
    def get_all_process_units(self) -> List[ProcessUnit]:
        """获取所有工艺单元"""
        try:
            query = "SELECT * FROM process_flow ORDER BY name"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            units = []
            for row in rows:
                units.append(ProcessUnit.from_dict(dict(row)))
            return units
            
        except Exception as e:
            print(f"获取所有工艺单元失败: {e}")
            return []
            
    # ========== 设备清单操作 ==========
    
    def add_equipment(self, equipment: EquipmentItem) -> bool:
        """添加设备"""
        try:
            data = equipment.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            query = f"INSERT INTO equipment_list ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"添加设备失败: {e}")
            self.connection.rollback()
            return False
            
    def get_all_equipment(self) -> List[EquipmentItem]:
        """获取所有设备"""
        try:
            query = "SELECT * FROM equipment_list ORDER BY name"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            equipment_list = []
            for row in rows:
                equipment_list.append(EquipmentItem.from_dict(dict(row)))
            return equipment_list
            
        except Exception as e:
            print(f"获取所有设备失败: {e}")
            return []
            
    # ========== 物料平衡操作 ==========
    
    def add_material_balance(self, balance: MaterialBalance) -> bool:
        """添加物料平衡"""
        try:
            data = balance.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            query = f"INSERT INTO material_balance ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"添加物料平衡失败: {e}")
            self.connection.rollback()
            return False
            
    # ========== 通用查询方法 ==========
    
    def get_module_data(self, module_name: str) -> Dict[str, Any]:
        """获取指定模块的所有数据"""
        table_map = {
            "material_params": ("material_params", MaterialParameter),
            "msds_data": ("msds_data", MSDSData),
            "process_materials": ("process_materials", ProcessMaterial),
            "process_flow": ("process_flow", ProcessUnit),
            "equipment_list": ("equipment_list", EquipmentItem),
            "material_balance": ("material_balance", MaterialBalance),
        }
        
        if module_name not in table_map:
            return {"data": [], "count": 0}
            
        table_name, model_class = table_map[module_name]
        
        try:
            query = f"SELECT * FROM {table_name}"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            data = []
            for row in rows:
                if hasattr(model_class, 'from_dict'):
                    data.append(model_class.from_dict(dict(row)))
                else:
                    data.append(dict(row))
                    
            return {"data": data, "count": len(data)}
            
        except Exception as e:
            print(f"获取模块数据失败 {module_name}: {e}")
            return {"data": [], "count": 0}
            
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行自定义查询"""
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"执行查询失败: {e}")
            return []
            
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"数据库备份成功: {backup_path}")
            return True
        except Exception as e:
            print(f"数据库备份失败: {e}")
            return False
            
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库"""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            print(f"数据库恢复成功: {self.db_path}")
            return True
        except Exception as e:
            print(f"数据库恢复失败: {e}")
            return False
            
    def export_to_json(self, export_path: str) -> bool:
        """导出数据库到JSON文件"""
        try:
            data = {}
            
            # 获取所有表名
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in self.cursor.fetchall()]
            
            for table in tables:
                self.cursor.execute(f"SELECT * FROM {table}")
                rows = self.cursor.fetchall()
                data[table] = [dict(row) for row in rows]
                
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"数据库导出成功: {export_path}")
            return True
            
        except Exception as e:
            print(f"数据库导出失败: {e}")
            return False
            
    def import_from_json(self, import_path: str) -> bool:
        """从JSON文件导入数据库"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for table, rows in data.items():
                if rows:
                    # 获取列名
                    columns = list(rows[0].keys())
                    columns_str = ', '.join(columns)
                    placeholders = ', '.join(['?' for _ in columns])
                    
                    # 清空表
                    self.cursor.execute(f"DELETE FROM {table}")
                    
                    # 插入数据
                    for row in rows:
                        values = [row[col] for col in columns]
                        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                        self.cursor.execute(query, values)
                        
            self.connection.commit()
            print(f"数据库导入成功: {import_path}")
            return True
            
        except Exception as e:
            print(f"数据库导入失败: {e}")
            self.connection.rollback()
            return False