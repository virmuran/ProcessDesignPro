"""
水平衡计算模块
用于计算工艺过程中的水平衡和用水优化
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum
import numpy as np


class WaterQualityParameter(Enum):
    """水质参数"""
    TDS = "总溶解固体"
    TSS = "总悬浮固体"
    COD = "化学需氧量"
    BOD = "生化需氧量"
    PH = "pH值"
    CONDUCTIVITY = "电导率"
    TURBIDITY = "浊度"
    HARDNESS = "硬度"
    CHLORIDE = "氯离子"
    SULFATE = "硫酸根"


class WaterSource(Enum):
    """水源类型"""
    FRESH_WATER = "新鲜水"
    RECYCLED_WATER = "回用水"
    RAIN_WATER = "雨水"
    GROUND_WATER = "地下水"
    SURFACE_WATER = "地表水"
    PROCESS_WATER = "工艺水"
    UTILITY_WATER = "公用工程水"


@dataclass
class WaterStream:
    """水流"""
    stream_id: str
    name: str
    source_type: WaterSource
    flow_rate: float  # 流量，m³/h
    temperature: float  # 温度，℃
    pressure: float  # 压力，kPa
    quality_parameters: Dict[str, float]  # 水质参数
    
    def get_parameter(self, param: WaterQualityParameter) -> float:
        """获取水质参数"""
        return self.quality_parameters.get(param.value, 0)
    
    def calculate_contaminant_load(self, contaminant: str) -> float:
        """计算污染物负荷"""
        concentration = self.quality_parameters.get(contaminant, 0)  # mg/L
        return self.flow_rate * concentration / 1000  # kg/h


@dataclass
class WaterTreatmentUnit:
    """水处理单元"""
    unit_id: str
    name: str
    unit_type: str
    inlet_streams: List[str]
    outlet_streams: List[str]
    removal_efficiencies: Dict[str, float]  # 污染物去除效率，%
    operation_cost: float  # 操作成本，元/h
    
    def calculate_treated_quality(self, inlet_quality: Dict[str, float]) -> Dict[str, float]:
        """计算处理后水质"""
        treated_quality = {}
        for param, concentration in inlet_quality.items():
            removal = self.removal_efficiencies.get(param, 0) / 100
            treated_quality[param] = concentration * (1 - removal)
        return treated_quality


class WaterBalanceCalculator:
    """水平衡计算器"""
    
    def __init__(self):
        self.water_streams = {}
        self.treatment_units = {}
        self.water_sinks = {}
        self.water_reuse_opportunities = []
        
    def add_water_stream(self, stream_data: Dict) -> str:
        """添加水流"""
        required_fields = ['name', 'source_type', 'flow_rate', 
                          'temperature', 'pressure', 'quality_parameters']
        for field in required_fields:
            if field not in stream_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        stream_id = f"WS{len(self.water_streams) + 1:03d}"
        stream = WaterStream(stream_id=stream_id, **stream_data)
        self.water_streams[stream_id] = stream
        
        return stream_id
    
    def add_treatment_unit(self, unit_data: Dict) -> str:
        """添加水处理单元"""
        required_fields = ['name', 'unit_type', 'inlet_streams', 
                          'outlet_streams', 'removal_efficiencies']
        for field in required_fields:
            if field not in unit_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        unit_id = f"WTU{len(self.treatment_units) + 1:03d}"
        unit = WaterTreatmentUnit(
            unit_id=unit_id,
            name=unit_data['name'],
            unit_type=unit_data['unit_type'],
            inlet_streams=unit_data['inlet_streams'],
            outlet_streams=unit_data['outlet_streams'],
            removal_efficiencies=unit_data['removal_efficiencies'],
            operation_cost=unit_data.get('operation_cost', 0)
        )
        
        self.treatment_units[unit_id] = unit
        
        return unit_id
    
    def calculate_overall_water_balance(self) -> Dict:
        """计算总体水平衡"""
        total_fresh_water = 0
        total_recycled_water = 0
        total_wastewater = 0
        total_consumption = 0
        
        for stream in self.water_streams.values():
            if stream.source_type == WaterSource.FRESH_WATER:
                total_fresh_water += stream.flow_rate
            elif stream.source_type == WaterSource.RECYCLED_WATER:
                total_recycled_water += stream.flow_rate
            elif stream.source_type in [WaterSource.PROCESS_WATER, WaterSource.UTILITY_WATER]:
                total_consumption += stream.flow_rate
        
        # 简化计算：假设所有不是新鲜水或回用水的水流都是废水
        total_wastewater = sum(stream.flow_rate for stream in self.water_streams.values()) - total_consumption
        
        water_balance = {
            'total_fresh_water': total_fresh_water,
            'total_recycled_water': total_recycled_water,
            'total_wastewater': total_wastewater,
            'total_consumption': total_consumption,
            'water_reuse_ratio': (total_recycled_water / total_fresh_water * 100) if total_fresh_water > 0 else 0,
            'specific_water_consumption': total_fresh_water / total_consumption if total_consumption > 0 else 0,
            'water_balance_error': abs(total_fresh_water + total_recycled_water - total_wastewater - total_consumption)
        }
        
        return water_balance
    
    def calculate_contaminant_balance(self, contaminant: str) -> Dict:
        """计算污染物平衡"""
        total_input_load = 0
        total_output_load = 0
        total_removed_load = 0
        
        # 计算输入负荷
        for stream in self.water_streams.values():
            if stream.source_type in [WaterSource.FRESH_WATER, WaterSource.RECYCLED_WATER]:
                load = stream.calculate_contaminant_load(contaminant)
                total_input_load += load
        
        # 计算处理单元去除
        for unit in self.treatment_units.values():
            # 计算进入单元的污染物负荷
            unit_inlet_load = 0
            for stream_id in unit.inlet_streams:
                if stream_id in self.water_streams:
                    stream = self.water_streams[stream_id]
                    unit_inlet_load += stream.calculate_contaminant_load(contaminant)
            
            # 计算去除量
            removal_efficiency = unit.removal_efficiencies.get(contaminant, 0) / 100
            removed_load = unit_inlet_load * removal_efficiency
            total_removed_load += removed_load
        
        # 计算输出负荷
        for stream in self.water_streams.values():
            if stream.source_type == WaterSource.WASTE:
                load = stream.calculate_contaminant_load(contaminant)
                total_output_load += load
        
        balance_error = total_input_load - total_output_load - total_removed_load
        removal_efficiency_total = (total_removed_load / total_input_load * 100) if total_input_load > 0 else 0
        
        return {
            'contaminant': contaminant,
            'total_input_load': total_input_load,
            'total_output_load': total_output_load,
            'total_removed_load': total_removed_load,
            'overall_removal_efficiency': removal_efficiency_total,
            'balance_error': balance_error,
            'is_balanced': abs(balance_error) < 0.01  # 0.01 kg/h误差
        }
    
    def identify_water_reuse_opportunities(self, 
                                          max_contaminant_levels: Dict[str, float]) -> List[Dict]:
        """识别水回用机会"""
        opportunities = []
        
        # 寻找废水水源
        wastewater_streams = [s for s in self.water_streams.values() 
                             if s.source_type == WaterSource.WASTE]
        
        # 寻找可接受较低水质的用水点
        fresh_water_streams = [s for s in self.water_streams.values() 
                              if s.source_type == WaterSource.FRESH_WATER]
        
        for wastewater in wastewater_streams:
            for fresh_water in fresh_water_streams:
                # 检查水质是否符合要求
                is_suitable = True
                reasons = []
                
                for param, max_level in max_contaminant_levels.items():
                    wastewater_level = wastewater.quality_parameters.get(param, 0)
                    if wastewater_level > max_level:
                        is_suitable = False
                        reasons.append(f"{param}: {wastewater_level} > {max_level}")
                
                if is_suitable:
                    opportunity = {
                        'wastewater_source': wastewater.stream_id,
                        'wastewater_flow': wastewater.flow_rate,
                        'fresh_water_replacement': fresh_water.stream_id,
                        'fresh_water_flow': fresh_water.flow_rate,
                        'potential_savings': min(wastewater.flow_rate, fresh_water.flow_rate),
                        'water_quality_analysis': {
                            param: {
                                'wastewater': wastewater.quality_parameters.get(param, 0),
                                'required': max_contaminant_levels.get(param, float('inf')),
                                'meets_requirement': wastewater.quality_parameters.get(param, 0) <= max_contaminant_levels.get(param, float('inf'))
                            }
                            for param in max_contaminant_levels.keys()
                        }
                    }
                    opportunities.append(opportunity)
        
        self.water_reuse_opportunities = opportunities
        return opportunities
    
    def calculate_water_reuse_potential(self) -> Dict:
        """计算水回用潜力"""
        if not self.water_reuse_opportunities:
            return {}
        
        total_potential = 0
        fresh_water_savings = 0
        wastewater_reduction = 0
        
        for opportunity in self.water_reuse_opportunities:
            total_potential += opportunity['potential_savings']
            fresh_water_savings += opportunity['potential_savings']
            wastewater_reduction += opportunity['potential_savings']
        
        current_balance = self.calculate_overall_water_balance()
        
        if current_balance['total_fresh_water'] > 0:
            potential_reduction_percent = (fresh_water_savings / current_balance['total_fresh_water'] * 100)
        else:
            potential_reduction_percent = 0
        
        return {
            'total_reuse_potential': total_potential,
            'fresh_water_savings': fresh_water_savings,
            'wastewater_reduction': wastewater_reduction,
            'potential_reduction_percent': potential_reduction_percent,
            'number_of_opportunities': len(self.water_reuse_opportunities),
            'estimated_cost_savings': fresh_water_savings * 24 * 365 * 5  # 假设水价5元/m³
        }
    
    def optimize_water_network(self, 
                              water_cost: float = 5,  # 元/m³
                              treatment_cost_factor: float = 10,  # 元/m³
                              max_iterations: int = 100) -> Dict:
        """优化水网络"""
        # 简化的水网络优化
        current_balance = self.calculate_overall_water_balance()
        
        # 识别回用机会
        reuse_opportunities = self.identify_water_reuse_opportunities({
            'TDS': 500,
            'COD': 100,
            'BOD': 30,
            'TSS': 50
        })
        
        reuse_potential = self.calculate_water_reuse_potential()
        
        # 计算当前成本
        current_fresh_water_cost = current_balance['total_fresh_water'] * water_cost * 24 * 365
        current_wastewater_cost = current_balance['total_wastewater'] * treatment_cost_factor * 24 * 365
        
        # 计算优化后成本
        optimized_fresh_water = max(0, current_balance['total_fresh_water'] - reuse_potential.get('fresh_water_savings', 0))
        optimized_wastewater = max(0, current_balance['total_wastewater'] - reuse_potential.get('wastewater_reduction', 0))
        
        optimized_fresh_water_cost = optimized_fresh_water * water_cost * 24 * 365
        optimized_wastewater_cost = optimized_wastewater * treatment_cost_factor * 24 * 365
        
        # 计算投资成本（简化）
        # 假设每个回用机会需要投资10万元
        investment_cost = len(reuse_opportunities) * 100000
        
        # 计算年节省
        annual_savings = (current_fresh_water_cost + current_wastewater_cost) - \
                        (optimized_fresh_water_cost + optimized_wastewater_cost)
        
        # 计算投资回收期
        if annual_savings > 0:
            payback_period = investment_cost / annual_savings
        else:
            payback_period = float('inf')
        
        return {
            'current_situation': {
                'fresh_water_consumption': current_balance['total_fresh_water'],
                'wastewater_generation': current_balance['total_wastewater'],
                'annual_fresh_water_cost': current_fresh_water_cost,
                'annual_wastewater_cost': current_wastewater_cost,
                'total_annual_cost': current_fresh_water_cost + current_wastewater_cost
            },
            'optimized_situation': {
                'fresh_water_consumption': optimized_fresh_water,
                'wastewater_generation': optimized_wastewater,
                'annual_fresh_water_cost': optimized_fresh_water_cost,
                'annual_wastewater_cost': optimized_wastewater_cost,
                'total_annual_cost': optimized_fresh_water_cost + optimized_wastewater_cost
            },
            'optimization_results': {
                'water_reuse_potential': reuse_potential.get('total_reuse_potential', 0),
                'fresh_water_reduction': reuse_potential.get('fresh_water_savings', 0),
                'wastewater_reduction': reuse_potential.get('wastewater_reduction', 0),
                'annual_cost_savings': annual_savings,
                'investment_required': investment_cost,
                'payback_period_years': payback_period,
                'number_of_reuse_opportunities': len(reuse_opportunities)
            }
        }
    
    def calculate_water_footprint(self) -> Dict:
        """计算水足迹"""
        water_balance = self.calculate_overall_water_balance()
        
        # 计算不同类型的水消耗
        water_types = {}
        for stream in self.water_streams.values():
            water_type = stream.source_type.value
            if water_type not in water_types:
                water_types[water_type] = 0
            water_types[water_type] += stream.flow_rate
        
        # 计算污染物排放当量
        contaminant_emissions = {}
        for contaminant in [p.value for p in WaterQualityParameter]:
            balance = self.calculate_contaminant_balance(contaminant)
            if balance['total_output_load'] > 0:
                contaminant_emissions[contaminant] = balance['total_output_load']
        
        # 计算水强度
        total_water_input = water_balance['total_fresh_water'] + water_balance['total_recycled_water']
        
        # 假设一个基准产量
        baseline_production = 1000  # 吨产品
        water_intensity = total_water_input / baseline_production if baseline_production > 0 else 0
        
        return {
            'total_water_footprint': total_water_input,
            'water_intensity': water_intensity,  # m³/吨产品
            'water_type_breakdown': water_types,
            'contaminant_emissions': contaminant_emissions,
            'water_reuse_ratio': water_balance['water_reuse_ratio'],
            'specific_water_consumption': water_balance['specific_water_consumption'],
            'water_efficiency_rating': self._calculate_efficiency_rating(water_balance['water_reuse_ratio'])
        }
    
    def _calculate_efficiency_rating(self, reuse_ratio: float) -> str:
        """计算水效率评级"""
        if reuse_ratio >= 80:
            return "优秀"
        elif reuse_ratio >= 60:
            return "良好"
        elif reuse_ratio >= 40:
            return "一般"
        elif reuse_ratio >= 20:
            return "需改进"
        else:
            return "较差"
    
    def generate_water_balance_report(self) -> str:
        """生成水平衡报告"""
        water_balance = self.calculate_overall_water_balance()
        water_footprint = self.calculate_water_footprint()
        reuse_potential = self.calculate_water_reuse_potential()
        
        report = f"""
        ===========================================
        水平衡报告
        ===========================================
        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        === 总体水平衡 ===
        新鲜水用量: {water_balance['total_fresh_water']:.2f} m³/h
        回用水用量: {water_balance['total_recycled_water']:.2f} m³/h
        废水产生量: {water_balance['total_wastewater']:.2f} m³/h
        水消耗量: {water_balance['total_consumption']:.2f} m³/h
        水回用率: {water_balance['water_reuse_ratio']:.1f} %
        单位水耗: {water_balance['specific_water_consumption']:.3f} m³/m³
        平衡误差: {water_balance['water_balance_error']:.4f} m³/h
        
        === 水足迹分析 ===
        总水足迹: {water_footprint['total_water_footprint']:.2f} m³/h
        水强度: {water_footprint['water_intensity']:.3f} m³/吨产品
        水效率评级: {water_footprint['water_efficiency_rating']}
        
        === 水回用潜力 ===
        总回用潜力: {reuse_potential.get('total_reuse_potential', 0):.2f} m³/h
        新鲜水节省: {reuse_potential.get('fresh_water_savings', 0):.2f} m³/h
        废水减排: {reuse_potential.get('wastewater_reduction', 0):.2f} m³/h
        潜在降低百分比: {reuse_potential.get('potential_reduction_percent', 0):.1f} %
        
        === 水处理单元 ===
        处理单元总数: {len(self.treatment_units)}
        """
        
        if self.treatment_units:
            report += "\n各处理单元性能:\n"
            for unit_id, unit in self.treatment_units.items():
                report += f"""
                单元: {unit.name} ({unit_id})
                类型: {unit.unit_type}
                去除效率: {', '.join([f'{k}: {v}%' for k, v in unit.removal_efficiencies.items()])}
                操作成本: {unit.operation_cost:.2f} 元/h
                """
        
        report += """
        ===========================================
        """
        
        return report