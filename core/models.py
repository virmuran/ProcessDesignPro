#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field, asdict, fields
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import json

@dataclass
class MaterialParameter:
    """物料参数模型 - 基于硫酸标准扩展"""
    material_id: str
    name: str
    chemical_formula: Optional[str] = None
    cas_number: Optional[str] = None  # 新增：CAS号
    
    # 物性参数
    molar_mass: Optional[float] = None  # g/mol
    density: Optional[float] = None    # kg/m³
    viscosity: Optional[float] = None   # Pa·s
    specific_heat: Optional[float] = None  # J/(kg·K)
    thermal_conductivity: Optional[float] = None  # W/(m·K)
    
    # 质量指标（基于硫酸标准GB 29205-2012）
    sulfuric_acid_content_92: Optional[float] = None  # 92酸含量 %
    sulfuric_acid_content_98: Optional[float] = None  # 98酸含量 %
    nitrate_content: Optional[float] = None  # 硝酸盐含量 %
    chloride_content: Optional[float] = None  # 氯化物含量 %
    iron_content: Optional[float] = None  # 铁含量 %
    lead_content: Optional[float] = None  # 铅含量 mg/kg
    arsenic_content: Optional[float] = None  # 砷含量 mg/kg
    selenium_content: Optional[float] = None  # 硒含量 mg/kg
    reducing_substances: bool = True  # 还原性物质检测
    
    # 安全信息
    safety_class: Optional[str] = None
    storage_conditions: Optional[str] = None
    hazard_classification: Optional[str] = None  # 危险分类
    
    # 其他属性
    properties: Dict[str, Any] = field(default_factory=dict)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 计算属性
    @property
    def molecular_weight(self) -> Optional[float]:
        """获取分子量（kg/kmol）"""
        return self.molar_mass if self.molar_mass is None else self.molar_mass
    
    @property
    def heat_capacity(self) -> Optional[float]:
        """获取热容（J/(mol·K)）"""
        if self.molar_mass and self.specific_heat:
            return self.specific_heat * self.molar_mass / 1000  # J/(mol·K)
        return None
    
    def calculate_enthalpy(self, temperature: float, reference_temp: float = 25.0) -> Optional[float]:
        """计算焓值 (J/kg)"""
        if self.specific_heat is not None:
            return self.specific_heat * (temperature - reference_temp)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        
        # 处理properties字段为JSON字符串
        if 'properties' in data:
            data['properties_json'] = json.dumps(data.pop('properties', {}), ensure_ascii=False)
        
        # 处理其他需要JSON序列化的字段
        data['reducing_substances'] = 1 if self.reducing_substances else 0
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialParameter':
        """从字典创建实例"""
        # 处理properties_json字段
        if 'properties_json' in data:
            properties_json = data.pop('properties_json', None)
            if properties_json:
                data['properties'] = json.loads(properties_json) if properties_json else {}
        
        # 处理reducing_substances（SQLite可能存储为整数）
        if 'reducing_substances' in data:
            reducing = data['reducing_substances']
            if isinstance(reducing, int):
                data['reducing_substances'] = bool(reducing)
            elif isinstance(reducing, str):
                data['reducing_substances'] = reducing.lower() in ['true', '1', 'yes']
        
        # 过滤掉数据库中可能存在的额外字段（如id）
        valid_fields = [field.name for field in fields(cls)]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)

@dataclass
class MSDSData:
    """MSDS数据模型"""
    material_id: str
    msds_number: Optional[str] = None
    hazard_classification: Optional[str] = None
    precautionary_statements: Optional[str] = None
    first_aid_measures: Optional[str] = None
    fire_fighting_measures: Optional[str] = None
    accidental_release_measures: Optional[str] = None
    handling_and_storage: Optional[str] = None
    exposure_controls: Optional[str] = None
    stability_and_reactivity: Optional[str] = None
    toxicological_information: Optional[str] = None
    ecological_information: Optional[str] = None
    disposal_considerations: Optional[str] = None
    transport_information: Optional[str] = None
    regulatory_information: Optional[str] = None
    other_information: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class ProcessMaterial:
    """过程物料模型 - 添加计算属性"""
    stream_id: str
    name: str
    phase: str = "liquid"  # liquid, gas, solid
    temperature: Optional[float] = None  # °C
    pressure: Optional[float] = None     # bar
    flow_rate: Optional[float] = None    # kg/h
    composition: Dict[str, float] = field(default_factory=dict)  # 组分及质量分数
    source_unit: Optional[str] = None
    destination_unit: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 计算属性
    @property
    def molar_flow_rate(self) -> Optional[float]:
        """计算摩尔流率 (kmol/h)"""
        if not self.flow_rate or not self.composition:
            return None
        
        total_molar_flow = 0.0
        for material_id, mass_fraction in self.composition.items():
            # 注意：这里需要物料参数来计算，暂时返回None
            pass
        return None
    
    @property
    def total_mass_flow(self) -> Optional[float]:
        """获取总质量流率 (kg/h)"""
        return self.flow_rate
    
    def get_component_flow(self, material_id: str) -> Optional[float]:
        """获取组分的质量流率 (kg/h)"""
        if self.flow_rate and material_id in self.composition:
            return self.flow_rate * self.composition[material_id]
        return None

@dataclass
class ProcessUnit:
    """工艺单元模型"""
    unit_id: str
    name: str
    type: str  # reactor, separator, heat_exchanger, pump, etc.
    description: Optional[str] = None
    position_x: float = 0.0
    position_y: float = 0.0
    connections: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['connections_json'] = json.dumps(data.pop('connections', []), ensure_ascii=False)
        data['parameters_json'] = json.dumps(data.pop('parameters', {}), ensure_ascii=False)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessUnit':
        """从字典创建实例"""
        if 'connections_json' in data:
            data['connections'] = json.loads(data['connections_json']) if data['connections_json'] else []
        if 'parameters_json' in data:
            data['parameters'] = json.loads(data['parameters_json']) if data['parameters_json'] else {}
        return cls(**{k: v for k, v in data.items() if not k.endswith('_json')})

@dataclass
class EquipmentItem:
    """设备清单模型"""
    equipment_id: str
    name: str
    type: str
    model: Optional[str] = None
    specifications: Dict[str, Any] = field(default_factory=dict)
    quantity: int = 1
    material_of_construction: Optional[str] = None
    operating_conditions: Dict[str, Any] = field(default_factory=dict)
    utility_requirements: Dict[str, Any] = field(default_factory=dict)
    manufacturer: Optional[str] = None
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['specifications_json'] = json.dumps(data.pop('specifications', {}), ensure_ascii=False)
        data['operating_conditions_json'] = json.dumps(data.pop('operating_conditions', {}), ensure_ascii=False)
        data['utility_requirements_json'] = json.dumps(data.pop('utility_requirements', {}), ensure_ascii=False)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EquipmentItem':
        """从字典创建实例"""
        if 'specifications_json' in data:
            data['specifications'] = json.loads(data['specifications_json']) if data['specifications_json'] else {}
        if 'operating_conditions_json' in data:
            data['operating_conditions'] = json.loads(data['operating_conditions_json']) if data['operating_conditions_json'] else {}
        if 'utility_requirements_json' in data:
            data['utility_requirements'] = json.loads(data['utility_requirements_json']) if data['utility_requirements_json'] else {}
        return cls(**{k: v for k, v in data.items() if not k.endswith('_json')})

@dataclass
class MaterialBalance:
    """物料平衡模型 - 增强"""
    unit_id: str
    input_streams: List[str] = field(default_factory=list)  # 输入流ID列表
    output_streams: List[str] = field(default_factory=list)  # 输出流ID列表
    conversion_rate: Optional[float] = None  # 转化率
    yield_value: Optional[float] = None      # 产率
    losses: Dict[str, float] = field(default_factory=dict)  # 损耗
    balance_status: str = "pending"  # pending, calculated, balanced, unbalanced
    calculated_data: Dict[str, Any] = field(default_factory=dict)  # 计算结果
    tolerance: float = 0.01  # 允许的平衡误差 (%)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def calculate_balance(self, input_streams_data: List[ProcessMaterial], 
                         output_streams_data: List[ProcessMaterial]) -> Dict[str, Any]:
        """计算物料平衡"""
        results = {
            "total_input": 0.0,
            "total_output": 0.0,
            "components": {},
            "is_balanced": False,
            "differences": {}
        }
        
        # 计算总输入输出
        for stream in input_streams_data:
            if stream.flow_rate:
                results["total_input"] += stream.flow_rate
                
        for stream in output_streams_data:
            if stream.flow_rate:
                results["total_output"] += stream.flow_rate
                
        # 计算组分平衡
        all_components = set()
        for stream in input_streams_data + output_streams_data:
            all_components.update(stream.composition.keys())
            
        for component in all_components:
            comp_input = 0.0
            comp_output = 0.0
            
            for stream in input_streams_data:
                if stream.flow_rate and component in stream.composition:
                    comp_input += stream.flow_rate * stream.composition[component]
                    
            for stream in output_streams_data:
                if stream.flow_rate and component in stream.composition:
                    comp_output += stream.flow_rate * stream.composition[component]
                    
            results["components"][component] = {
                "input": comp_input,
                "output": comp_output,
                "difference": comp_output - comp_input,
                "conversion": ((comp_input - comp_output) / comp_input * 100) if comp_input > 0 else 0
            }
            
        # 检查平衡状态
        total_diff = results["total_output"] - results["total_input"]
        diff_percent = (abs(total_diff) / results["total_input"] * 100) if results["total_input"] > 0 else 100
        
        results["total_difference"] = total_diff
        results["difference_percent"] = diff_percent
        results["is_balanced"] = diff_percent <= self.tolerance
        
        if results["is_balanced"]:
            self.balance_status = "balanced"
        else:
            self.balance_status = "unbalanced"
            
        self.calculated_data = results
        return results

@dataclass
class ProjectInfo:
    """项目信息模型"""
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: Optional[str] = None
    company: Optional[str] = None
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含id字段）"""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'company': self.company,
            'created_date': self.created_date,
            'modified_date': self.modified_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectInfo':
        """从字典创建实例，过滤掉不必要的字段"""
        # 过滤掉数据库中的id字段和其他不需要的字段
        valid_fields = [field.name for field in fields(cls)]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
@dataclass
class HeatBalance:
    """热量平衡模型"""
    unit_id: str
    input_heat: Dict[str, float] = field(default_factory=dict)  # 各项输入热量 (kW)
    output_heat: Dict[str, float] = field(default_factory=dict)  # 各项输出热量 (kW)
    heat_loss: float = 0.0  # 热损失 (kW)
    efficiency: Optional[float] = None  # 热效率 (%)
    utility_requirements: Dict[str, float] = field(default_factory=dict)  # 公用工程需求
    calculated_data: Dict[str, Any] = field(default_factory=dict)  # 计算结果
    balance_status: str = "pending"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['input_heat_json'] = json.dumps(data.pop('input_heat', {}), ensure_ascii=False)
        data['output_heat_json'] = json.dumps(data.pop('output_heat', {}), ensure_ascii=False)
        data['utility_requirements_json'] = json.dumps(data.pop('utility_requirements', {}), ensure_ascii=False)
        data['calculated_data_json'] = json.dumps(data.pop('calculated_data', {}), ensure_ascii=False)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeatBalance':
        """从字典创建实例"""
        if 'input_heat_json' in data:
            data['input_heat'] = json.loads(data['input_heat_json']) if data['input_heat_json'] else {}
        if 'output_heat_json' in data:
            data['output_heat'] = json.loads(data['output_heat_json']) if data['output_heat_json'] else {}
        if 'utility_requirements_json' in data:
            data['utility_requirements'] = json.loads(data['utility_requirements_json']) if data['utility_requirements_json'] else {}
        if 'calculated_data_json' in data:
            data['calculated_data'] = json.loads(data['calculated_data_json']) if data['calculated_data_json'] else {}
        return cls(**{k: v for k, v in data.items() if not k.endswith('_json')})