"""
过程物料管理模块
用于管理工艺流程中的物料流和物料平衡
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum
from datetime import datetime
import numpy as np


class StreamType(Enum):
    """物流类型"""
    FEED = "进料"
    PRODUCT = "产品"
    RECYCLE = "循环"
    WASTE = "废物"
    VENT = "排放"
    INTERMEDIATE = "中间物流"


@dataclass
class StreamComponent:
    """物流组分"""
    material_id: str
    name: str
    mass_fraction: float  # 质量分数
    mole_fraction: float  # 摩尔分数
    flow_rate: float      # 流量 kg/h


@dataclass
class ProcessStream:
    """工艺物流"""
    stream_id: str
    name: str
    stream_type: StreamType
    temperature: float  # ℃
    pressure: float     # kPa
    total_flow: float   # kg/h
    components: List[StreamComponent]
    from_unit: Optional[str] = None
    to_unit: Optional[str] = None
    properties: Optional[Dict] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class ProcessMaterialManager:
    """过程物料管理器"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.streams = {}
        self.units = {}
        
    def create_stream(self, stream_data: Dict) -> str:
        """创建工艺物流"""
        required_fields = ['name', 'stream_type', 'temperature', 
                          'pressure', 'total_flow', 'components']
        for field in required_fields:
            if field not in stream_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        stream_id = f"STR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        stream_data['stream_id'] = stream_id
        stream_data['created_at'] = datetime.now()
        
        # 验证组分总和
        if not self._validate_component_sum(stream_data['components']):
            raise ValueError("组分分数总和不为1")
        
        if self.db:
            success = self.db.insert('process_streams', stream_data)
            if success:
                self.streams[stream_id] = ProcessStream(**stream_data)
                return stream_id
        else:
            self.streams[stream_id] = ProcessStream(**stream_data)
            return stream_id
        
        return None
    
    def _validate_component_sum(self, components: List[StreamComponent]) -> bool:
        """验证组分分数总和是否为1"""
        mass_sum = sum(comp.get('mass_fraction', 0) for comp in components)
        mole_sum = sum(comp.get('mole_fraction', 0) for comp in components)
        
        return abs(mass_sum - 1.0) < 0.01 and abs(mole_sum - 1.0) < 0.01
    
    def calculate_stream_properties(self, stream_id: str) -> Dict:
        """计算物流物性"""
        stream = self.get_stream(stream_id)
        if not stream:
            return {}
        
        properties = {
            'average_molecular_weight': 0,
            'density': 0,
            'viscosity': 0,
            'heat_capacity': 0,
            'enthalpy': 0,
            'entropy': 0
        }
        
        # 基于组分计算平均物性
        for comp in stream.components:
            fraction = comp.mole_fraction
            # 这里需要从物料数据库获取物性数据
            # 简化计算，使用理想混合规则
            material_props = self._get_material_properties(comp.material_id)
            
            if material_props:
                properties['average_molecular_weight'] += material_props.get('molecular_weight', 0) * comp.mass_fraction
                properties['density'] += material_props.get('density', 0) * comp.mass_fraction
                properties['viscosity'] += material_props.get('viscosity', 0) * comp.mole_fraction
                properties['heat_capacity'] += material_props.get('heat_capacity', 0) * comp.mass_fraction
                
                # 计算焓值（简化计算）
                cp = material_props.get('heat_capacity', 0)
                properties['enthalpy'] += cp * stream.temperature * comp.mass_fraction
        
        return properties
    
    def _get_material_properties(self, material_id: str) -> Optional[Dict]:
        """从数据库获取物料物性"""
        if self.db:
            return self.db.query_one('materials', {'id': material_id})
        return None
    
    def perform_mass_balance(self, unit_operation_id: str) -> Dict:
        """执行单元操作的物料平衡"""
        # 获取进出该单元的所有物流
        input_streams = self._get_streams_by_unit(unit_operation_id, is_input=True)
        output_streams = self._get_streams_by_unit(unit_operation_id, is_input=False)
        
        balance = {
            'unit_id': unit_operation_id,
            'input_total': 0,
            'output_total': 0,
            'closure_error': 0,
            'component_balance': {},
            'is_balanced': False
        }
        
        # 计算总质量平衡
        for stream in input_streams:
            balance['input_total'] += stream.total_flow
        
        for stream in output_streams:
            balance['output_total'] += stream.total_flow
        
        # 计算闭合误差
        if balance['input_total'] > 0:
            balance['closure_error'] = abs(balance['output_total'] - balance['input_total']) / balance['input_total'] * 100
        
        balance['is_balanced'] = balance['closure_error'] < 0.1  # 0.1%误差
        
        # 计算组分平衡
        self._calculate_component_balance(balance, input_streams, output_streams)
        
        return balance
    
    def _get_streams_by_unit(self, unit_id: str, is_input: bool = True) -> List[ProcessStream]:
        """获取进出单元操作的物流"""
        streams = []
        for stream in self.streams.values():
            if is_input and stream.to_unit == unit_id:
                streams.append(stream)
            elif not is_input and stream.from_unit == unit_id:
                streams.append(stream)
        return streams
    
    def _calculate_component_balance(self, balance: Dict, 
                                   inputs: List[ProcessStream],
                                   outputs: List[ProcessStream]):
        """计算组分物料平衡"""
        component_flows = {}
        
        # 统计所有组分
        all_components = set()
        for stream in inputs + outputs:
            for comp in stream.components:
                all_components.add(comp.material_id)
        
        # 计算各组分进出量
        for comp_id in all_components:
            component_flows[comp_id] = {
                'input': 0,
                'output': 0,
                'balance_error': 0
            }
            
            # 输入流中的组分
            for stream in inputs:
                for comp in stream.components:
                    if comp.material_id == comp_id:
                        component_flows[comp_id]['input'] += stream.total_flow * comp.mass_fraction
            
            # 输出流中的组分
            for stream in outputs:
                for comp in stream.components:
                    if comp.material_id == comp_id:
                        component_flows[comp_id]['output'] += stream.total_flow * comp.mass_fraction
            
            # 计算平衡误差
            if component_flows[comp_id]['input'] > 0:
                error = abs(component_flows[comp_id]['output'] - component_flows[comp_id]['input'])
                component_flows[comp_id]['balance_error'] = error / component_flows[comp_id]['input'] * 100
        
        balance['component_balance'] = component_flows
    
    def generate_stream_table(self, format_type: str = 'csv') -> str:
        """生成物流汇总表"""
        if format_type == 'csv':
            return self._generate_csv_stream_table()
        elif format_type == 'html':
            return self._generate_html_stream_table()
        else:
            return self._generate_text_stream_table()
    
    def _generate_csv_stream_table(self) -> str:
        """生成CSV格式物流表"""
        headers = ['Stream ID', 'Name', 'Type', 'From', 'To', 
                  'Temperature (℃)', 'Pressure (kPa)', 'Flow (kg/h)',
                  'Components']
        
        rows = []
        for stream in self.streams.values():
            components = ', '.join([f"{comp.name}:{comp.mass_fraction:.3f}" 
                                  for comp in stream.components])
            
            row = [
                stream.stream_id,
                stream.name,
                stream.stream_type.value,
                stream.from_unit or '',
                stream.to_unit or '',
                f"{stream.temperature:.1f}",
                f"{stream.pressure:.1f}",
                f"{stream.total_flow:.2f}",
                components
            ]
            rows.append(','.join(row))
        
        return '\n'.join([','.join(headers)] + rows)
    
    def _generate_html_stream_table(self) -> str:
        """生成HTML格式物流表"""
        html = """
        <html>
        <head>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h2>工艺物流汇总表</h2>
            <table>
                <tr>
                    <th>物流ID</th>
                    <th>名称</th>
                    <th>类型</th>
                    <th>来源</th>
                    <th>去向</th>
                    <th>温度(℃)</th>
                    <th>压力(kPa)</th>
                    <th>流量(kg/h)</th>
                    <th>组分</th>
                </tr>
        """
        
        for stream in self.streams.values():
            components = '<br>'.join([f"{comp.name}: {comp.mass_fraction:.3%}" 
                                    for comp in stream.components])
            
            html += f"""
                <tr>
                    <td>{stream.stream_id}</td>
                    <td>{stream.name}</td>
                    <td>{stream.stream_type.value}</td>
                    <td>{stream.from_unit or ''}</td>
                    <td>{stream.to_unit or ''}</td>
                    <td>{stream.temperature:.1f}</td>
                    <td>{stream.pressure:.1f}</td>
                    <td>{stream.total_flow:.2f}</td>
                    <td>{components}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_stream_table(self) -> str:
        """生成文本格式物流表"""
        lines = []
        lines.append("=" * 100)
        lines.append("工艺物流汇总表")
        lines.append("=" * 100)
        
        for stream in self.streams.values():
            lines.append(f"\n物流ID: {stream.stream_id}")
            lines.append(f"名称: {stream.name}")
            lines.append(f"类型: {stream.stream_type.value}")
            lines.append(f"来源: {stream.from_unit or 'N/A'}")
            lines.append(f"去向: {stream.to_unit or 'N/A'}")
            lines.append(f"温度: {stream.temperature:.1f} ℃")
            lines.append(f"压力: {stream.pressure:.1f} kPa")
            lines.append(f"总流量: {stream.total_flow:.2f} kg/h")
            lines.append("组分:")
            
            for comp in stream.components:
                lines.append(f"  - {comp.name}: {comp.mass_fraction:.3%} (质量), "
                           f"{comp.mole_fraction:.3%} (摩尔)")
        
        return '\n'.join(lines)
    
    def calculate_overall_material_balance(self) -> Dict:
        """计算全流程物料平衡"""
        total_input = 0
        total_output = 0
        total_waste = 0
        total_recycle = 0
        
        component_totals = {}
        
        for stream in self.streams.values():
            # 分类统计
            if stream.stream_type == StreamType.FEED:
                total_input += stream.total_flow
            elif stream.stream_type == StreamType.PRODUCT:
                total_output += stream.total_flow
            elif stream.stream_type == StreamType.WASTE:
                total_waste += stream.total_flow
            elif stream.stream_type == StreamType.RECYCLE:
                total_recycle += stream.total_flow
            
            # 组分统计
            for comp in stream.components:
                comp_id = comp.material_id
                if comp_id not in component_totals:
                    component_totals[comp_id] = {
                        'name': comp.name,
                        'input': 0,
                        'output': 0,
                        'consumption': 0,
                        'generation': 0
                    }
                
                flow = stream.total_flow * comp.mass_fraction
                
                if stream.stream_type in [StreamType.FEED, StreamType.RECYCLE]:
                    component_totals[comp_id]['input'] += flow
                elif stream.stream_type in [StreamType.PRODUCT, StreamType.WASTE, StreamType.VENT]:
                    component_totals[comp_id]['output'] += flow
        
        # 计算净生成/消耗
        for comp_data in component_totals.values():
            comp_data['consumption'] = max(0, comp_data['input'] - comp_data['output'])
            comp_data['generation'] = max(0, comp_data['output'] - comp_data['input'])
        
        overall_balance = {
            'total_input': total_input,
            'total_output': total_output,
            'total_waste': total_waste,
            'total_recycle': total_recycle,
            'material_efficiency': (total_output / total_input * 100) if total_input > 0 else 0,
            'waste_generation_rate': (total_waste / total_input * 100) if total_input > 0 else 0,
            'recycle_ratio': (total_recycle / total_input * 100) if total_input > 0 else 0,
            'component_balance': component_totals,
            'closure_error': abs(total_output + total_waste - total_input) / total_input * 100 if total_input > 0 else 0
        }
        
        return overall_balance