import sqlite3
from typing import Dict, Any, List
import json
from datetime import datetime

class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self.connect()
        
    def connect(self):
        """连接到数据库"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
    def initialize_database(self):
        """初始化数据库表结构"""
        with self.connection:
            # 项目信息表
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS project_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_date TEXT,
                    modified_date TEXT,
                    version TEXT DEFAULT '1.0'
                )
            ''')
            
            # 物料参数表
            self.connection.execute('''
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
            self.connection.execute('''
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
                    FOREIGN KEY (material_id) REFERENCES material_params (material_id)
                )
            ''')
            
            # 过程物料表
            self.connection.execute('''
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
            self.connection.execute('''
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
            self.connection.execute('''
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
            
            # 物料平衡表
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS material_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id TEXT NOT NULL,
                    input_streams_json TEXT,
                    output_streams_json,
                    conversion_rate REAL,
                    yield REAL,
                    losses_json TEXT,
                    balance_status TEXT,
                    created_date TEXT,
                    modified_date TEXT,
                    FOREIGN KEY (unit_id) REFERENCES process_flow (unit_id)
                )
            ''')
            
            # 热量平衡表
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS heat_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id TEXT NOT NULL,
                    heat_input_json TEXT,
                    heat_output_json TEXT,
                    heat_loss REAL,
                    efficiency REAL,
                    utility_requirements_json TEXT,
                    created_date TEXT,
                    modified_date TEXT,
                    FOREIGN KEY (unit_id) REFERENCES process_flow (unit_id)
                )
            ''')
            
            # 水平衡表
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS water_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id TEXT NOT NULL,
                    fresh_water_in REAL,
                    recycled_water_in REAL,
                    water_consumption REAL,
                    wastewater_out REAL,
                    reuse_possibilities TEXT,
                    created_date TEXT,
                    modified_date TEXT,
                    FOREIGN KEY (unit_id) REFERENCES process_flow (unit_id)
                )
            ''')
            
            # 数据版本控制表
            self.connection.execute('''
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
            
    def get_module_data(self, module_name: str) -> Dict[str, Any]:
        """获取指定模块的所有数据"""
        tables = {
            "material_params": "material_params",
            "msds_data": "msds_data",
            "process_materials": "process_materials",
            "process_flow": "process_flow",
            "equipment_list": "equipment_list",
            "material_balance": "material_balance",
            "heat_balance": "heat_balance",
            "water_balance": "water_balance"
        }
        
        if module_name not in tables:
            return {}
            
        table_name = tables[module_name]
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        # 解析JSON字段
        for item in data:
            for key, value in item.items():
                if isinstance(value, str) and (key.endswith('_json') or key in ['composition_json', 'specifications_json']):
                    try:
                        item[key] = json.loads(value) if value else {}
                    except:
                        item[key] = value
                        
        return {"data": data, "count": len(data)}
        
    def update_module_data(self, module_name: str, data: Dict[str, Any]):
        """更新模块数据"""
        # 这里实现具体的更新逻辑
        # 包括版本控制和数据验证
        pass