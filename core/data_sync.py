#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步引擎 - 完整实现
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import hashlib
import json
import math
from PySide6.QtCore import QObject, Signal

from .models import *
from .database import DatabaseManager

class DataSyncEngine(QObject):
    """数据同步引擎 - 完整实现"""
    
    # 信号定义
    data_updated = Signal(str, str)  # (模块名, 数据ID)
    sync_completed = Signal(str, bool, str)  # (同步类型, 成功状态, 消息)
    calculation_completed = Signal(str, Dict[str, Any])  # (计算类型, 结果)
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager
        self.sync_rules = self._initialize_sync_rules()
        self.calculation_cache = {}  # 计算缓存
        
    def _initialize_sync_rules(self) -> Dict[str, Dict[str, List[str]]]:
        """初始化同步规则"""
        return {
            'material_params': {
                'triggers': ['add', 'update', 'delete'],
                'targets': ['process_materials', 'material_balance', 'heat_balance'],
                'rules': {
                    'process_materials': self._sync_material_to_process,
                    'material_balance': self._sync_material_to_balance,
                    'heat_balance': self._sync_material_to_heat
                }
            },
            'process_materials': {
                'triggers': ['add', 'update', 'delete'],
                'targets': ['material_balance', 'heat_balance', 'water_balance', 'process_flow'],
                'rules': {
                    'material_balance': self._sync_process_to_balance,
                    'heat_balance': self._sync_process_to_heat,
                    'water_balance': self._sync_process_to_water,
                    'process_flow': self._sync_process_to_flow
                }
            },
            'process_flow': {
                'triggers': ['add', 'update', 'delete'],
                'targets': ['equipment_list', 'material_balance', 'heat_balance'],
                'rules': {
                    'equipment_list': self._sync_unit_to_equipment,
                    'material_balance': self._sync_unit_to_balance,
                    'heat_balance': self._sync_unit_to_heat
                }
            },
            'equipment_list': {
                'triggers': ['add', 'update', 'delete'],
                'targets': ['material_balance', 'heat_balance', 'water_balance'],
                'rules': {
                    'material_balance': self._sync_equipment_to_balance,
                    'heat_balance': self._sync_equipment_to_heat,
                    'water_balance': self._sync_equipment_to_water
                }
            }
        }
        
    def sync_data(self, source_module: str, operation: str, data_id: str, data: Optional[Dict[str, Any]] = None):
        """
        同步数据
        
        Args:
            source_module: 源模块名
            operation: 操作类型 (add, update, delete)
            data_id: 数据ID
            data: 数据内容 (删除操作时为None)
        """
        if source_module not in self.sync_rules:
            return
            
        rules = self.sync_rules[source_module]
        
        if operation not in rules['triggers']:
            return
            
        try:
            for target_module in rules['targets']:
                if target_module in rules['rules']:
                    sync_func = rules['rules'][target_module]
                    sync_func(source_module, operation, data_id, data)
                    
            self.sync_completed.emit(f"{source_module}->{','.join(rules['targets'])}", True, "同步成功")
            
        except Exception as e:
            error_msg = f"数据同步失败 {source_module} -> {target_module}: {str(e)}"
            print(error_msg)
            self.sync_completed.emit(source_module, False, error_msg)
            
    # ========== 物料参数同步 ==========
    
    def _sync_material_to_process(self, source_module: str, operation: str, material_id: str, data: Optional[Dict[str, Any]]):
        """同步物料参数到过程物料"""
        if operation == 'delete':
            # 物料被删除，需要从相关流股中移除
            self._remove_material_from_streams(material_id)
        elif operation in ['add', 'update']:
            # 物料被添加或更新，需要更新相关流股的物性计算
            self._update_streams_with_material(material_id, data)
            
    def _sync_material_to_balance(self, source_module: str, operation: str, material_id: str, data: Optional[Dict[str, Any]]):
        """同步物料参数到物料平衡"""
        if operation == 'delete':
            # 标记使用该物料的平衡需要重新计算
            self._mark_balance_for_recalculation(material_id)
        elif operation in ['add', 'update']:
            # 重新计算相关物料平衡
            self._recalculate_material_balances(material_id, data)
            
    def _sync_material_to_heat(self, source_module: str, operation: str, material_id: str, data: Optional[Dict[str, Any]]):
        """同步物料参数到热量平衡"""
        if operation in ['add', 'update'] and data:
            # 检查热力学参数是否变化
            old_material = self.db.get_material(material_id)
            new_specific_heat = data.get('specific_heat')
            
            if old_material and new_specific_heat:
                old_specific_heat = old_material.specific_heat or 0
                if abs(new_specific_heat - old_specific_heat) > 0.001:
                    # 热容变化，重新计算热量平衡
                    self._recalculate_heat_balances_for_material(material_id, data)
                    
    # ========== 过程物料同步 ==========
    
    def _sync_process_to_balance(self, source_module: str, operation: str, stream_id: str, data: Optional[Dict[str, Any]]):
        """同步过程物料到物料平衡"""
        # 获取流股信息
        stream = self.db.get_process_material(stream_id) if operation != 'delete' else None
        
        # 查找相关的工艺单元
        related_units = self._find_units_for_stream(stream_id, stream)
        
        for unit_id in related_units:
            # 获取或创建物料平衡记录
            balance = self._get_or_create_material_balance(unit_id)
            
            # 更新输入输出流列表
            self._update_balance_streams(balance, stream_id, operation, stream)
            
            # 重新计算物料平衡
            self._calculate_material_balance_for_unit(unit_id)
            
    def _sync_process_to_heat(self, source_module: str, operation: str, stream_id: str, data: Optional[Dict[str, Any]]):
        """同步过程物料到热量平衡"""
        if operation in ['add', 'update']:
            # 重新计算相关单元的热量平衡
            stream = self.db.get_process_material(stream_id)
            if stream:
                related_units = self._find_units_for_stream(stream_id, stream)
                for unit_id in related_units:
                    self._calculate_heat_balance_for_unit(unit_id)
                    
    def _sync_process_to_water(self, source_module: str, operation: str, stream_id: str, data: Optional[Dict[str, Any]]):
        """同步过程物料到水平衡"""
        if operation in ['add', 'update']:
            stream = self.db.get_process_material(stream_id)
            if stream and self._is_water_stream(stream):
                related_units = self._find_units_for_stream(stream_id, stream)
                for unit_id in related_units:
                    self._calculate_water_balance_for_unit(unit_id)
                    
    def _sync_process_to_flow(self, source_module: str, operation: str, stream_id: str, data: Optional[Dict[str, Any]]):
        """同步过程物料到工艺路线"""
        if operation in ['add', 'update']:
            stream = self.db.get_process_material(stream_id)
            if stream and (stream.source_unit or stream.destination_unit):
                # 更新工艺路线图中的连接
                self._update_flow_connections(stream_id, stream)
                
    # ========== 工艺单元同步 ==========
    
    def _sync_unit_to_equipment(self, source_module: str, operation: str, unit_id: str, data: Optional[Dict[str, Any]]):
        """同步工艺单元到设备清单"""
        if operation == 'add' and data:
            # 自动创建设备
            self._create_equipment_from_unit(unit_id, data)
        elif operation == 'update' and data:
            # 更新相关设备
            self._update_equipment_from_unit(unit_id, data)
        elif operation == 'delete':
            # 删除相关设备
            self._delete_equipment_for_unit(unit_id)
            
    def _sync_unit_to_balance(self, source_module: str, operation: str, unit_id: str, data: Optional[Dict[str, Any]]):
        """同步工艺单元到物料平衡"""
        if operation == 'add' and data:
            # 为新建单元创建物料平衡记录
            self._create_material_balance_for_unit(unit_id, data)
        elif operation in ['add', 'update', 'delete']:
            # 重新计算物料平衡
            self._calculate_material_balance_for_unit(unit_id)
            
    def _sync_unit_to_heat(self, source_module: str, operation: str, unit_id: str, data: Optional[Dict[str, Any]]):
        """同步工艺单元到热量平衡"""
        if operation in ['add', 'update', 'delete']:
            # 重新计算热量平衡
            self._calculate_heat_balance_for_unit(unit_id)
            
    # ========== 设备清单同步 ==========
    
    def _sync_equipment_to_balance(self, source_module: str, operation: str, equipment_id: str, data: Optional[Dict[str, Any]]):
        """同步设备清单到物料平衡"""
        if operation in ['add', 'update']:
            # 设备变化可能影响物料平衡（如设备效率变化）
            equipment = self.db.get_module_data('equipment_list')
            # 查找相关单元
            related_units = self._find_units_for_equipment(equipment_id)
            for unit_id in related_units:
                self._calculate_material_balance_for_unit(unit_id)
                
    def _sync_equipment_to_heat(self, source_module: str, operation: str, equipment_id: str, data: Optional[Dict[str, Any]]):
        """同步设备清单到热量平衡"""
        if operation in ['add', 'update']:
            # 设备变化可能影响热量平衡（如换热器效率变化）
            related_units = self._find_units_for_equipment(equipment_id)
            for unit_id in related_units:
                self._calculate_heat_balance_for_unit(unit_id)
                
    def _sync_equipment_to_water(self, source_module: str, operation: str, equipment_id: str, data: Optional[Dict[str, Any]]):
        """同步设备清单到水平衡"""
        if operation in ['add', 'update']:
            # 设备变化可能影响水平衡（如泵的耗水量变化）
            equipment = self.db.execute_query(
                "SELECT * FROM equipment_list WHERE equipment_id = ?", 
                (equipment_id,)
            )
            if equipment and equipment[0].get('type') in ['pump', 'cooling_tower', 'boiler']:
                related_units = self._find_units_for_equipment(equipment_id)
                for unit_id in related_units:
                    self._calculate_water_balance_for_unit(unit_id)
                    
    # ========== 核心计算方法 ==========
    
    def _calculate_material_balance_for_unit(self, unit_id: str):
        """计算单元的物料平衡"""
        try:
            # 获取物料平衡记录
            balance_data = self.db.execute_query(
                "SELECT * FROM material_balance WHERE unit_id = ?", 
                (unit_id,)
            )
            
            if not balance_data:
                # 如果没有物料平衡记录，创建新的
                balance = MaterialBalance(unit_id=unit_id)
                self.db.cursor.execute(
                    """INSERT INTO material_balance 
                    (unit_id, balance_status, created_date, modified_date) 
                    VALUES (?, ?, ?, ?)""",
                    (unit_id, 'calculated', datetime.now().isoformat(), datetime.now().isoformat())
                )
                self.db.connection.commit()
                balance_data = [{'unit_id': unit_id}]
                
            # 获取单元的输入输出流
            streams = self.db.execute_query(
                """SELECT * FROM process_materials 
                WHERE source_unit = ? OR destination_unit = ?""",
                (unit_id, unit_id)
            )
            
            input_streams = []
            output_streams = []
            process_streams = []
            
            for stream_data in streams:
                stream = ProcessMaterial.from_dict(stream_data)
                process_streams.append(stream)
                if stream.destination_unit == unit_id:
                    input_streams.append(stream)
                elif stream.source_unit == unit_id:
                    output_streams.append(stream)
                    
            if not input_streams and not output_streams:
                return
                
            # 创建物料平衡对象并计算
            balance = MaterialBalance(unit_id=unit_id)
            results = balance.calculate_balance(input_streams, output_streams)
            
            # 保存计算结果
            calculated_data_json = json.dumps(results, ensure_ascii=False)
            
            # 更新数据库
            self.db.cursor.execute(
                """UPDATE material_balance 
                SET balance_status = ?, calculated_data_json = ?, modified_date = ?
                WHERE unit_id = ?""",
                (balance.balance_status, calculated_data_json, datetime.now().isoformat(), unit_id)
            )
            self.db.connection.commit()
            
            # 发出计算完成信号
            self.calculation_completed.emit('material_balance', {
                'unit_id': unit_id,
                'results': results,
                'status': balance.balance_status
            })
            
            print(f"物料平衡计算完成: 单元 {unit_id}, 状态: {balance.balance_status}")
            
        except Exception as e:
            print(f"计算物料平衡失败 {unit_id}: {e}")
            
    def _calculate_heat_balance_for_unit(self, unit_id: str):
        """计算单元的热量平衡"""
        try:
            # 获取单元信息
            unit_data = self.db.execute_query(
                "SELECT * FROM process_flow WHERE unit_id = ?", 
                (unit_id,)
            )
            
            if not unit_data:
                return
                
            unit = ProcessUnit.from_dict(unit_data[0])
            
            # 获取单元的输入输出流
            streams = self.db.execute_query(
                """SELECT * FROM process_materials 
                WHERE source_unit = ? OR destination_unit = ?""",
                (unit_id, unit_id)
            )
            
            # 获取物料参数
            all_materials = self.db.get_all_materials()
            material_dict = {mat.material_id: mat for mat in all_materials}
            
            # 计算热量平衡
            total_input_heat = 0.0
            total_output_heat = 0.0
            
            input_heat_sources = {}
            output_heat_sources = {}
            
            # 计算流股的显热
            for stream_data in streams:
                stream = ProcessMaterial.from_dict(stream_data)
                
                if not stream.temperature or not stream.flow_rate or not stream.composition:
                    continue
                    
                # 计算流股的热量
                stream_heat = 0.0
                for material_id, fraction in stream.composition.items():
                    material = material_dict.get(material_id)
                    if material and material.specific_heat and stream.flow_rate:
                        # Q = m * Cp * ΔT (简化计算，假设参考温度25°C)
                        delta_temp = stream.temperature - 25.0
                        component_mass = stream.flow_rate * fraction / 3600  # kg/s
                        heat = component_mass * material.specific_heat * delta_temp  # kW
                        stream_heat += heat
                        
                if stream.destination_unit == unit_id:  # 输入流
                    input_heat_sources[f"stream_{stream.stream_id}"] = stream_heat
                    total_input_heat += stream_heat
                elif stream.source_unit == unit_id:  # 输出流
                    output_heat_sources[f"stream_{stream.stream_id}"] = stream_heat
                    total_output_heat += stream_heat
                    
            # 考虑反应热（如果有）
            reaction_heat = unit.parameters.get('reaction_heat', 0) if hasattr(unit, 'parameters') else 0
            if reaction_heat:
                input_heat_sources['reaction'] = reaction_heat
                total_input_heat += reaction_heat
                
            # 计算热损失（假设为输入热量的5%）
            heat_loss = total_input_heat * 0.05
            output_heat_sources['heat_loss'] = heat_loss
            total_output_heat += heat_loss
            
            # 计算热效率
            efficiency = None
            if total_input_heat > 0:
                useful_heat = total_output_heat - heat_loss
                efficiency = (useful_heat / total_input_heat) * 100 if total_input_heat > 0 else 0
                
            # 创建热量平衡对象
            heat_balance = HeatBalance(
                unit_id=unit_id,
                input_heat=input_heat_sources,
                output_heat=output_heat_sources,
                heat_loss=heat_loss,
                efficiency=efficiency,
                balance_status='calculated' if abs(total_output_heat - total_input_heat) < 0.01 else 'unbalanced'
            )
            
            # 保存计算结果
            calculated_data = {
                'total_input': total_input_heat,
                'total_output': total_output_heat,
                'difference': total_output_heat - total_input_heat,
                'efficiency': efficiency,
                'is_balanced': abs(total_output_heat - total_input_heat) < 0.01
            }
            
            heat_balance.calculated_data = calculated_data
            
            # 保存到数据库
            heat_dict = heat_balance.to_dict()
            
            # 检查是否已存在记录
            existing = self.db.execute_query(
                "SELECT id FROM heat_balance WHERE unit_id = ?", 
                (unit_id,)
            )
            
            if existing:
                # 更新现有记录
                self.db.cursor.execute(
                    """UPDATE heat_balance 
                    SET input_heat_json = ?, output_heat_json = ?, heat_loss = ?, 
                        efficiency = ?, utility_requirements_json = ?, 
                        calculated_data_json = ?, balance_status = ?, modified_date = ?
                    WHERE unit_id = ?""",
                    (
                        heat_dict['input_heat_json'],
                        heat_dict['output_heat_json'],
                        heat_dict['heat_loss'],
                        heat_dict['efficiency'],
                        heat_dict['utility_requirements_json'],
                        heat_dict['calculated_data_json'],
                        heat_dict['balance_status'],
                        datetime.now().isoformat(),
                        unit_id
                    )
                )
            else:
                # 插入新记录
                self.db.cursor.execute(
                    """INSERT INTO heat_balance 
                    (unit_id, input_heat_json, output_heat_json, heat_loss, 
                     efficiency, utility_requirements_json, calculated_data_json, 
                     balance_status, created_date, modified_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        unit_id,
                        heat_dict['input_heat_json'],
                        heat_dict['output_heat_json'],
                        heat_dict['heat_loss'],
                        heat_dict['efficiency'],
                        heat_dict['utility_requirements_json'],
                        heat_dict['calculated_data_json'],
                        heat_dict['balance_status'],
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                
            self.db.connection.commit()
            
            # 发出计算完成信号
            self.calculation_completed.emit('heat_balance', {
                'unit_id': unit_id,
                'results': calculated_data,
                'status': heat_balance.balance_status
            })
            
            print(f"热量平衡计算完成: 单元 {unit_id}, 状态: {heat_balance.balance_status}")
            
        except Exception as e:
            print(f"计算热量平衡失败 {unit_id}: {e}")
            
    def _calculate_water_balance_for_unit(self, unit_id: str):
        """计算单元的水平衡"""
        try:
            # 获取与水相关的流股
            streams = self.db.execute_query(
                """SELECT * FROM process_materials 
                WHERE (source_unit = ? OR destination_unit = ?) 
                AND (composition_json LIKE '%water%' OR name LIKE '%水%')""",
                (unit_id, unit_id)
            )
            
            water_input = 0.0
            water_output = 0.0
            water_consumption = 0.0
            
            for stream_data in streams:
                stream = ProcessMaterial.from_dict(stream_data)
                if stream.flow_rate:
                    # 计算水含量（简化：假设流股名称或组成中包含水）
                    water_content = 0.0
                    if 'water' in stream.composition:
                        water_content = stream.composition['water']
                    elif '水' in stream.name:
                        water_content = 1.0  # 假设纯水流股
                        
                    water_flow = stream.flow_rate * water_content
                    
                    if stream.destination_unit == unit_id:  # 输入
                        water_input += water_flow
                    elif stream.source_unit == unit_id:  # 输出
                        water_output += water_flow
                        
            # 计算水消耗
            water_consumption = water_input - water_output
            
            # 创建水平衡记录
            water_balance_data = {
                'unit_id': unit_id,
                'fresh_water_in': water_input,
                'recycled_water_in': 0.0,  # 可以根据实际情况计算
                'water_consumption': water_consumption if water_consumption > 0 else 0,
                'wastewater_out': water_output,
                'reuse_possibilities': '待分析'
            }
            
            # 保存到数据库
            existing = self.db.execute_query(
                "SELECT id FROM water_balance WHERE unit_id = ?", 
                (unit_id,)
            )
            
            if existing:
                self.db.cursor.execute(
                    """UPDATE water_balance 
                    SET fresh_water_in = ?, recycled_water_in = ?, water_consumption = ?, 
                        wastewater_out = ?, reuse_possibilities = ?, modified_date = ?
                    WHERE unit_id = ?""",
                    (
                        water_balance_data['fresh_water_in'],
                        water_balance_data['recycled_water_in'],
                        water_balance_data['water_consumption'],
                        water_balance_data['wastewater_out'],
                        water_balance_data['reuse_possibilities'],
                        datetime.now().isoformat(),
                        unit_id
                    )
                )
            else:
                self.db.cursor.execute(
                    """INSERT INTO water_balance 
                    (unit_id, fresh_water_in, recycled_water_in, water_consumption, 
                     wastewater_out, reuse_possibilities, created_date, modified_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        unit_id,
                        water_balance_data['fresh_water_in'],
                        water_balance_data['recycled_water_in'],
                        water_balance_data['water_consumption'],
                        water_balance_data['wastewater_out'],
                        water_balance_data['reuse_possibilities'],
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                
            self.db.connection.commit()
            
            # 发出计算完成信号
            self.calculation_completed.emit('water_balance', {
                'unit_id': unit_id,
                'results': water_balance_data,
                'status': 'calculated'
            })
            
            print(f"水平衡计算完成: 单元 {unit_id}")
            
        except Exception as e:
            print(f"计算水平衡失败 {unit_id}: {e}")
            
    # ========== 辅助方法 ==========
    
    def _remove_material_from_streams(self, material_id: str):
        """从流股中移除物料"""
        streams = self.db.execute_query(
            "SELECT * FROM process_materials WHERE composition_json LIKE ?",
            (f'%{material_id}%',)
        )
        
        for stream_data in streams:
            stream = ProcessMaterial.from_dict(stream_data)
            if material_id in stream.composition:
                del stream.composition[material_id]
                
                # 重新归一化组成
                total = sum(stream.composition.values())
                if total > 0:
                    for comp_id in stream.composition:
                        stream.composition[comp_id] /= total
                        
                # 更新数据库
                self.db.cursor.execute(
                    "UPDATE process_materials SET composition_json = ? WHERE stream_id = ?",
                    (json.dumps(stream.composition, ensure_ascii=False), stream.stream_id)
                )
                
        self.db.connection.commit()
        
    def _update_streams_with_material(self, material_id: str, material_data: Dict[str, Any]):
        """使用新物料数据更新流股"""
        # 这里可以更新流股的物性计算
        pass
        
    def _mark_balance_for_recalculation(self, material_id: str):
        """标记使用该物料的平衡需要重新计算"""
        # 查找使用该物料的物料平衡
        balances = self.db.execute_query(
            "SELECT unit_id FROM material_balance WHERE calculated_data_json LIKE ?",
            (f'%{material_id}%',)
        )
        
        for balance in balances:
            unit_id = balance['unit_id']
            self.db.cursor.execute(
                "UPDATE material_balance SET balance_status = 'needs_recalculation' WHERE unit_id = ?",
                (unit_id,)
            )
            
        self.db.connection.commit()
        
    def _recalculate_material_balances(self, material_id: str, material_data: Dict[str, Any]):
        """重新计算相关物料平衡"""
        # 查找使用该物料的流股
        streams = self.db.execute_query(
            "SELECT stream_id FROM process_materials WHERE composition_json LIKE ?",
            (f'%{material_id}%',)
        )
        
        processed_units = set()
        
        for stream_data in streams:
            stream_id = stream_data['stream_id']
            stream = self.db.get_process_material(stream_id)
            if stream:
                # 查找相关单元
                units = []
                if stream.source_unit:
                    units.append(stream.source_unit)
                if stream.destination_unit:
                    units.append(stream.destination_unit)
                    
                for unit_id in units:
                    if unit_id not in processed_units:
                        self._calculate_material_balance_for_unit(unit_id)
                        processed_units.add(unit_id)
                        
    def _recalculate_heat_balances_for_material(self, material_id: str, material_data: Dict[str, Any]):
        """重新计算相关热量平衡"""
        streams = self.db.execute_query(
            "SELECT stream_id FROM process_materials WHERE composition_json LIKE ?",
            (f'%{material_id}%',)
        )
        
        processed_units = set()
        
        for stream_data in streams:
            stream_id = stream_data['stream_id']
            stream = self.db.get_process_material(stream_id)
            if stream:
                units = []
                if stream.source_unit:
                    units.append(stream.source_unit)
                if stream.destination_unit:
                    units.append(stream.destination_unit)
                    
                for unit_id in units:
                    if unit_id not in processed_units:
                        self._calculate_heat_balance_for_unit(unit_id)
                        processed_units.add(unit_id)
                        
    def _find_units_for_stream(self, stream_id: str, stream: Optional[ProcessMaterial] = None) -> List[str]:
        """查找与流股相关的单元"""
        units = []
        
        if not stream:
            stream_data = self.db.execute_query(
                "SELECT * FROM process_materials WHERE stream_id = ?",
                (stream_id,)
            )
            if stream_data:
                stream = ProcessMaterial.from_dict(stream_data[0])
                
        if stream:
            if stream.source_unit:
                units.append(stream.source_unit)
            if stream.destination_unit:
                units.append(stream.destination_unit)
                
        return units
        
    def _get_or_create_material_balance(self, unit_id: str) -> Optional[MaterialBalance]:
        """获取或创建物料平衡记录"""
        balance_data = self.db.execute_query(
            "SELECT * FROM material_balance WHERE unit_id = ?",
            (unit_id,)
        )
        
        if balance_data:
            return MaterialBalance.from_dict(balance_data[0])
        else:
            # 创建新的物料平衡记录
            balance = MaterialBalance(unit_id=unit_id)
            self.db.cursor.execute(
                """INSERT INTO material_balance 
                (unit_id, balance_status, created_date, modified_date) 
                VALUES (?, ?, ?, ?)""",
                (unit_id, 'pending', datetime.now().isoformat(), datetime.now().isoformat())
            )
            self.db.connection.commit()
            return balance
            
    def _update_balance_streams(self, balance: MaterialBalance, stream_id: str, 
                               operation: str, stream: Optional[ProcessMaterial] = None):
        """更新物料平衡中的流股列表"""
        if operation == 'delete':
            if stream_id in balance.input_streams:
                balance.input_streams.remove(stream_id)
            if stream_id in balance.output_streams:
                balance.output_streams.remove(stream_id)
        elif operation in ['add', 'update'] and stream:
            if stream.destination_unit == balance.unit_id and stream_id not in balance.input_streams:
                balance.input_streams.append(stream_id)
            elif stream.source_unit == balance.unit_id and stream_id not in balance.output_streams:
                balance.output_streams.append(stream_id)
                
        # 更新数据库
        input_json = json.dumps(balance.input_streams, ensure_ascii=False)
        output_json = json.dumps(balance.output_streams, ensure_ascii=False)
        
        self.db.cursor.execute(
            """UPDATE material_balance 
            SET input_streams_json = ?, output_streams_json = ?, modified_date = ?
            WHERE unit_id = ?""",
            (input_json, output_json, datetime.now().isoformat(), balance.unit_id)
        )
        self.db.connection.commit()
        
    def _is_water_stream(self, stream: ProcessMaterial) -> bool:
        """检查是否是水流股"""
        if 'water' in stream.composition or '水' in stream.name.lower():
            return True
        return False
        
    def _update_flow_connections(self, stream_id: str, stream: ProcessMaterial):
        """更新工艺路线图中的连接"""
        if stream.source_unit and stream.destination_unit:
            # 查找源单元和目标单元
            source_unit = self.db.execute_query(
                "SELECT * FROM process_flow WHERE unit_id = ?",
                (stream.source_unit,)
            )
            dest_unit = self.db.execute_query(
                "SELECT * FROM process_flow WHERE unit_id = ?",
                (stream.destination_unit,)
            )
            
            if source_unit and dest_unit:
                # 这里可以更新工艺路线图中的连接关系
                # 实际实现可能需要图形界面更新
                pass
                
    def _create_equipment_from_unit(self, unit_id: str, unit_data: Dict[str, Any]):
        """从工艺单元创建设备"""
        unit_type = unit_data.get('type', '')
        equipment_type_map = {
            'reactor': '反应器',
            'separator': '分离器',
            'heatex': '换热器',
            'pump': '泵',
            'compressor': '压缩机',
            'tank': '储罐'
        }
        
        equipment_type = equipment_type_map.get(unit_type, '设备')
        
        equipment = EquipmentItem(
            equipment_id=f"EQ-{unit_id}",
            name=f"{unit_data.get('name', '')} - {equipment_type}",
            type=equipment_type,
            quantity=1,
            specifications={
                'source_unit': unit_id,
                'unit_type': unit_type,
                'description': unit_data.get('description', '')
            }
        )
        
        self.db.add_equipment(equipment)
        
    def _update_equipment_from_unit(self, unit_id: str, unit_data: Dict[str, Any]):
        """从工艺单元更新设备"""
        equipment_id = f"EQ-{unit_id}"
        equipment_data = self.db.execute_query(
            "SELECT * FROM equipment_list WHERE equipment_id = ?",
            (equipment_id,)
        )
        
        if equipment_data:
            # 更新现有设备
            equipment = EquipmentItem.from_dict(equipment_data[0])
            equipment.name = f"{unit_data.get('name', '')} - {equipment.type}"
            equipment.specifications['description'] = unit_data.get('description', '')
            
            self.db.cursor.execute(
                """UPDATE equipment_list 
                SET name = ?, specifications_json = ?, modified_date = ?
                WHERE equipment_id = ?""",
                (
                    equipment.name,
                    json.dumps(equipment.specifications, ensure_ascii=False),
                    datetime.now().isoformat(),
                    equipment_id
                )
            )
            self.db.connection.commit()
            
    def _delete_equipment_for_unit(self, unit_id: str):
        """删除与单元相关的设备"""
        equipment_id = f"EQ-{unit_id}"
        self.db.cursor.execute(
            "DELETE FROM equipment_list WHERE equipment_id = ?",
            (equipment_id,)
        )
        self.db.connection.commit()
        
    def _create_material_balance_for_unit(self, unit_id: str, unit_data: Dict[str, Any]):
        """为工艺单元创建物料平衡记录"""
        balance = MaterialBalance(unit_id=unit_id)
        self.db.add_material_balance(balance)
        
    def _find_units_for_equipment(self, equipment_id: str) -> List[str]:
        """查找与设备相关的单元"""
        # 从设备规格中提取源单元
        equipment_data = self.db.execute_query(
            "SELECT specifications_json FROM equipment_list WHERE equipment_id = ?",
            (equipment_id,)
        )
        
        units = []
        if equipment_data and equipment_data[0]['specifications_json']:
            try:
                specs = json.loads(equipment_data[0]['specifications_json'])
                source_unit = specs.get('source_unit')
                if source_unit:
                    units.append(source_unit)
            except:
                pass
                
        return units
        
    def calculate_all_balances(self):
        """计算所有单元的平衡"""
        # 获取所有工艺单元
        units = self.db.get_all_process_units()
        
        for unit in units:
            if hasattr(unit, 'unit_id'):
                print(f"计算单元 {unit.unit_id} 的平衡...")
                self._calculate_material_balance_for_unit(unit.unit_id)
                self._calculate_heat_balance_for_unit(unit.unit_id)
                self._calculate_water_balance_for_unit(unit.unit_id)
                
        print("所有平衡计算完成")
        
    def calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """计算数据哈希值"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
        
    def record_data_change(self, module_name: str, data_id: str, change_type: str, 
                          changed_by: str = 'system'):
        """记录数据变更"""
        try:
            query = """
                INSERT INTO data_versions 
                (module_name, version, data_hash, change_description, changed_by, changed_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            # 获取当前版本
            version_query = """
                SELECT MAX(version) as max_version 
                FROM data_versions 
                WHERE module_name = ? AND data_hash LIKE ?
            """
            hash_pattern = f"{data_id}%"
            result = self.db.execute_query(version_query, (module_name, hash_pattern))
            
            current_version = 1
            if result and result[0]['max_version']:
                current_version = result[0]['max_version'] + 1
                
            # 生成数据哈希
            data_hash = f"{data_id}_{self.calculate_data_hash({'id': data_id, 'type': change_type})}"
            
            self.db.cursor.execute(query, (
                module_name,
                current_version,
                data_hash,
                f"{change_type} operation",
                changed_by,
                datetime.now().isoformat()
            ))
            
            self.db.connection.commit()
            
        except Exception as e:
            print(f"记录数据变更失败: {e}")