"""
热量平衡计算模块
用于计算工艺过程中的热量平衡和能量消耗
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum
import numpy as np
from scipy.optimize import fsolve


class HeatTransferType(Enum):
    """传热类型"""
    CONDUCTION = "传导"
    CONVECTION = "对流"
    RADIATION = "辐射"
    PHASE_CHANGE = "相变"
    CHEMICAL_REACTION = "化学反应"


class HeatExchangerType(Enum):
    """换热器类型"""
    SHELL_TUBE = "管壳式"
    PLATE = "板式"
    AIR_COOLED = "空冷器"
    SPIRAL = "螺旋板式"
    DOUBLE_PIPE = "双管式"


@dataclass
class HeatStream:
    """热流"""
    stream_id: str
    name: str
    temperature_in: float  # 入口温度，℃
    temperature_out: float  # 出口温度，℃
    flow_rate: float  # 流量，kg/h
    heat_capacity: float  # 比热容，kJ/(kg·℃)
    enthalpy_in: Optional[float] = None  # 入口焓，kJ/h
    enthalpy_out: Optional[float] = None  # 出口焓，kJ/h
    heat_duty: Optional[float] = None  # 热负荷，kJ/h
    
    def __post_init__(self):
        self._calculate_enthalpy()
    
    def _calculate_enthalpy(self):
        """计算焓值"""
        # 基于参考温度0℃计算
        reference_temp = 0
        self.enthalpy_in = self.flow_rate * self.heat_capacity * (self.temperature_in - reference_temp)
        self.enthalpy_out = self.flow_rate * self.heat_capacity * (self.temperature_out - reference_temp)
        self.heat_duty = self.enthalpy_out - self.enthalpy_in


@dataclass
class HeatExchanger:
    """换热器"""
    exchanger_id: str
    name: str
    exchanger_type: HeatExchangerType
    hot_stream: HeatStream
    cold_stream: HeatStream
    u_value: float  # 总传热系数，W/(m²·℃)
    area: float  # 传热面积，m²
    fouling_factor: float = 0.0001  # 污垢系数，m²·℃/W
    
    def calculate_heat_transfer(self) -> Dict:
        """计算传热"""
        q = self.hot_stream.heat_duty  # 热负荷
        
        # 计算对数平均温差
        delta_t1 = self.hot_stream.temperature_in - self.cold_stream.temperature_out
        delta_t2 = self.hot_stream.temperature_out - self.cold_stream.temperature_in
        
        if abs(delta_t1 - delta_t2) < 1e-6:
            lmtd = delta_t1
        else:
            lmtd = (delta_t1 - delta_t2) / np.log(delta_t1 / delta_t2)
        
        # 考虑污垢系数的总传热系数
        u_clean = self.u_value
        u_dirty = 1 / (1/u_clean + self.fouling_factor)
        
        # 计算需要的传热面积
        required_area = abs(q) * 1000 / (u_dirty * lmtd * 3600)  # 转换为W
        
        # 计算效率
        efficiency = (self.area / required_area) * 100 if required_area > 0 else 0
        
        return {
            'heat_duty': q,
            'lmtd': lmtd,
            'u_clean': u_clean,
            'u_dirty': u_dirty,
            'required_area': required_area,
            'actual_area': self.area,
            'area_efficiency': efficiency,
            'temperature_approach': min(delta_t1, delta_t2)
        }


class HeatBalanceCalculator:
    """热量平衡计算器"""
    
    def __init__(self):
        self.heat_streams = {}
        self.heat_exchangers = {}
        self.reactions = {}
        
        # 物性常数
        self.STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴)
        
    def add_heat_stream(self, stream_data: Dict) -> str:
        """添加热流"""
        required_fields = ['name', 'temperature_in', 'temperature_out', 
                          'flow_rate', 'heat_capacity']
        for field in required_fields:
            if field not in stream_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        stream_id = f"HS{len(self.heat_streams) + 1:03d}"
        stream = HeatStream(stream_id=stream_id, **stream_data)
        self.heat_streams[stream_id] = stream
        
        return stream_id
    
    def add_heat_exchanger(self, exchanger_data: Dict) -> str:
        """添加换热器"""
        required_fields = ['name', 'exchanger_type', 'hot_stream_id', 
                          'cold_stream_id', 'u_value', 'area']
        for field in required_fields:
            if field not in exchanger_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        hot_stream = self.heat_streams.get(exchanger_data['hot_stream_id'])
        cold_stream = self.heat_streams.get(exchanger_data['cold_stream_id'])
        
        if not hot_stream or not cold_stream:
            raise ValueError("热流或冷流不存在")
        
        exchanger_id = f"HX{len(self.heat_exchangers) + 1:03d}"
        
        exchanger = HeatExchanger(
            exchanger_id=exchanger_id,
            name=exchanger_data['name'],
            exchanger_type=HeatExchangerType(exchanger_data['exchanger_type']),
            hot_stream=hot_stream,
            cold_stream=cold_stream,
            u_value=exchanger_data['u_value'],
            area=exchanger_data['area'],
            fouling_factor=exchanger_data.get('fouling_factor', 0.0001)
        )
        
        self.heat_exchangers[exchanger_id] = exchanger
        
        return exchanger_id
    
    def calculate_overall_heat_balance(self, system_boundary: List[str] = None) -> Dict:
        """计算总体热量平衡"""
        total_heat_in = 0
        total_heat_out = 0
        heat_generated = 0
        heat_consumed = 0
        
        if system_boundary is None:
            # 计算所有热流
            streams = list(self.heat_streams.values())
        else:
            # 只计算边界内的热流
            streams = [self.heat_streams[sid] for sid in system_boundary 
                      if sid in self.heat_streams]
        
        for stream in streams:
            if stream.heat_duty > 0:
                # 吸热过程
                total_heat_in += abs(stream.heat_duty)
                heat_consumed += abs(stream.heat_duty)
            else:
                # 放热过程
                total_heat_out += abs(stream.heat_duty)
                heat_generated += abs(stream.heat_duty)
        
        # 添加反应热
        for reaction_heat in self.reactions.values():
            if reaction_heat > 0:
                heat_generated += reaction_heat
            else:
                heat_consumed += abs(reaction_heat)
        
        # 计算热损失
        heat_loss = total_heat_in + heat_generated - total_heat_out - heat_consumed
        
        # 计算平衡误差
        total_heat = total_heat_in + heat_generated
        if total_heat > 0:
            balance_error = abs(heat_loss) / total_heat * 100
        else:
            balance_error = 0
        
        return {
            'total_heat_input': total_heat_in,
            'total_heat_output': total_heat_out,
            'heat_generated': heat_generated,
            'heat_consumed': heat_consumed,
            'heat_loss': heat_loss,
            'balance_error_percent': balance_error,
            'is_balanced': balance_error < 1.0,  # 1%误差
            'thermal_efficiency': (total_heat_out / total_heat_in * 100) if total_heat_in > 0 else 0
        }
    
    def calculate_pinch_analysis(self, hot_streams: List[str] = None,
                                cold_streams: List[str] = None,
                                delta_t_min: float = 10.0) -> Dict:
        """进行夹点分析"""
        if hot_streams is None:
            hot_streams = [sid for sid, stream in self.heat_streams.items() 
                          if stream.temperature_in > stream.temperature_out]
        
        if cold_streams is None:
            cold_streams = [sid for sid, stream in self.heat_streams.items() 
                           if stream.temperature_in < stream.temperature_out]
        
        # 创建复合曲线
        hot_composite = self._create_composite_curve(hot_streams, is_hot=True)
        cold_composite = self._create_composite_curve(cold_streams, is_hot=False)
        
        # 计算夹点
        pinch_point = self._find_pinch_point(hot_composite, cold_composite, delta_t_min)
        
        # 计算理论最小公用工程用量
        min_utility = self._calculate_minimum_utility(hot_composite, cold_composite, delta_t_min)
        
        return {
            'pinch_temperature': pinch_point.get('temperature', 0),
            'hot_utility_min': min_utility['hot_utility'],
            'cold_utility_min': min_utility['cold_utility'],
            'heat_recovery_potential': min_utility['heat_recovery'],
            'hot_composite_curve': hot_composite,
            'cold_composite_curve': cold_composite
        }
    
    def _create_composite_curve(self, stream_ids: List[str], is_hot: bool) -> List[Dict]:
        """创建复合曲线"""
        streams = [self.heat_streams[sid] for sid in stream_ids]
        
        # 收集所有温度点
        temperatures = set()
        for stream in streams:
            temperatures.add(stream.temperature_in)
            temperatures.add(stream.temperature_out)
        
        # 排序温度点
        temp_list = sorted(list(temperatures), reverse=is_hot)
        
        composite_curve = []
        cumulative_heat = 0
        
        for i in range(len(temp_list) - 1):
            t1, t2 = temp_list[i], temp_list[i + 1]
            
            # 计算该温度区间内的总热容流率
            total_cp = 0
            for stream in streams:
                t_min = min(stream.temperature_in, stream.temperature_out)
                t_max = max(stream.temperature_in, stream.temperature_out)
                
                if t1 <= t_max and t2 >= t_min:
                    # 流股经过此温度区间
                    total_cp += stream.flow_rate * stream.heat_capacity
            
            # 计算该区间的热量
            delta_t = abs(t1 - t2)
            delta_q = total_cp * delta_t
            
            cumulative_heat += delta_q
            
            composite_curve.append({
                'temperature': t1,
                'cumulative_heat': cumulative_heat,
                'delta_q': delta_q,
                'cp': total_cp
            })
        
        return composite_curve
    
    def _find_pinch_point(self, hot_curve: List[Dict], 
                         cold_curve: List[Dict], 
                         delta_t_min: float) -> Dict:
        """寻找夹点"""
        # 将冷流曲线向上平移delta_t_min
        adjusted_cold_curve = []
        for point in cold_curve:
            adjusted_point = point.copy()
            adjusted_point['temperature'] += delta_t_min
            adjusted_cold_curve.append(adjusted_point)
        
        # 寻找最接近的点（夹点）
        pinch_point = None
        min_distance = float('inf')
        
        for h_point in hot_curve:
            for c_point in adjusted_cold_curve:
                distance = abs(h_point['temperature'] - c_point['temperature'])
                if distance < min_distance:
                    min_distance = distance
                    pinch_point = {
                        'hot_temperature': h_point['temperature'],
                        'cold_temperature': c_point['temperature'] - delta_t_min,
                        'temperature': h_point['temperature'],
                        'heat_flow': h_point['cumulative_heat']
                    }
        
        return pinch_point or {}
    
    def _calculate_minimum_utility(self, hot_curve: List[Dict],
                                  cold_curve: List[Dict],
                                  delta_t_min: float) -> Dict:
        """计算最小公用工程用量"""
        # 简化的计算，实际应用中应使用问题表格法
        hot_utility = 0
        cold_utility = 0
        
        # 计算总热量
        total_hot_heat = hot_curve[-1]['cumulative_heat'] if hot_curve else 0
        total_cold_heat = cold_curve[-1]['cumulative_heat'] if cold_curve else 0
        
        # 理论可回收热量
        heat_recovery = min(total_hot_heat, total_cold_heat)
        
        # 最小公用工程
        hot_utility = max(0, total_cold_heat - heat_recovery)
        cold_utility = max(0, total_hot_heat - heat_recovery)
        
        return {
            'hot_utility': hot_utility,
            'cold_utility': cold_utility,
            'heat_recovery': heat_recovery
        }
    
    def calculate_heat_exchanger_network(self, delta_t_min: float = 10.0) -> Dict:
        """计算换热网络"""
        hot_streams = [sid for sid, stream in self.heat_streams.items() 
                      if stream.temperature_in > stream.temperature_out]
        cold_streams = [sid for sid, stream in self.heat_streams.items() 
                       if stream.temperature_in < stream.temperature_out]
        
        # 进行夹点分析
        pinch_analysis = self.calculate_pinch_analysis(hot_streams, cold_streams, delta_t_min)
        
        # 简化的换热网络设计
        network = {
            'hot_streams': hot_streams,
            'cold_streams': cold_streams,
            'total_hot_streams': len(hot_streams),
            'total_cold_streams': len(cold_streams),
            'pinch_temperature': pinch_analysis['pinch_temperature'],
            'min_hot_utility': pinch_analysis['hot_utility_min'],
            'min_cold_utility': pinch_analysis['cold_utility_min'],
            'heat_exchangers': [],
            'utility_requirements': {}
        }
        
        # 匹配热流和冷流
        matches = []
        for hot_id in hot_streams:
            hot_stream = self.heat_streams[hot_id]
            for cold_id in cold_streams:
                cold_stream = self.heat_streams[cold_id]
                
                # 检查是否跨夹点（简化检查）
                if (hot_stream.temperature_out > cold_stream.temperature_in + delta_t_min and
                    hot_stream.temperature_in > cold_stream.temperature_out + delta_t_min):
                    
                    # 计算最大可交换热量
                    q_hot = abs(hot_stream.heat_duty)
                    q_cold = abs(cold_stream.heat_duty)
                    max_q = min(q_hot, q_cold)
                    
                    if max_q > 0:
                        matches.append({
                            'hot_stream': hot_id,
                            'cold_stream': cold_id,
                            'max_heat_exchange': max_q,
                            'temperature_approach': min(
                                hot_stream.temperature_out - cold_stream.temperature_in,
                                hot_stream.temperature_in - cold_stream.temperature_out
                            )
                        })
        
        network['possible_matches'] = matches
        
        return network
    
    def calculate_energy_efficiency(self) -> Dict:
        """计算能源效率指标"""
        overall_balance = self.calculate_overall_heat_balance()
        
        # 计算各单元的能量效率
        unit_efficiencies = {}
        for exchanger_id, exchanger in self.heat_exchangers.items():
            calc = exchanger.calculate_heat_transfer()
            unit_efficiencies[exchanger_id] = {
                'heat_exchanger': exchanger.name,
                'area_efficiency': calc['area_efficiency'],
                'temperature_approach': calc['temperature_approach'],
                'heat_duty': calc['heat_duty']
            }
        
        # 计算总的热回收率
        total_heat_exchanged = 0
        for exchanger in self.heat_exchangers.values():
            total_heat_exchanged += abs(exchanger.hot_stream.heat_duty)
        
        total_heat_input = overall_balance['total_heat_input']
        heat_recovery_rate = (total_heat_exchanged / total_heat_input * 100) if total_heat_input > 0 else 0
        
        return {
            'overall_thermal_efficiency': overall_balance['thermal_efficiency'],
            'heat_recovery_rate': heat_recovery_rate,
            'total_heat_exchanged': total_heat_exchanged,
            'unit_efficiencies': unit_efficiencies,
            'energy_intensity': total_heat_input / total_heat_exchanged if total_heat_exchanged > 0 else 0
        }
    
    def optimize_heat_exchanger_network(self, 
                                       hot_utility_cost: float = 100,  # 元/GJ
                                       cold_utility_cost: float = 50,  # 元/GJ
                                       capital_cost_factor: float = 1000  # 元/m²
                                       ) -> Dict:
        """优化换热网络"""
        # 进行夹点分析
        pinch_analysis = self.calculate_pinch_analysis()
        
        # 简化的经济优化
        base_case = {
            'hot_utility': pinch_analysis['hot_utility_min'],
            'cold_utility': pinch_analysis['cold_utility_min'],
            'heat_recovery': pinch_analysis['heat_recovery_potential']
        }
        
        # 计算年度运行成本
        annual_hours = 8000  # 年运行小时数
        gj_per_kj = 1e-6
        
        hot_utility_cost_annual = base_case['hot_utility'] * gj_per_kj * hot_utility_cost * annual_hours / 1000
        cold_utility_cost_annual = base_case['cold_utility'] * gj_per_kj * cold_utility_cost * annual_hours / 1000
        total_utility_cost = hot_utility_cost_annual + cold_utility_cost_annual
        
        # 估计投资成本（简化）
        total_area = sum(exchanger.area for exchanger in self.heat_exchangers.values())
        capital_cost = total_area * capital_cost_factor
        
        # 计算投资回收期
        utility_savings = total_utility_cost  # 假设优化后公用工程费用为0
        payback_period = capital_cost / utility_savings if utility_savings > 0 else float('inf')
        
        return {
            'base_case': base_case,
            'utility_costs': {
                'hot_utility_cost_annual': hot_utility_cost_annual,
                'cold_utility_cost_annual': cold_utility_cost_annual,
                'total_utility_cost_annual': total_utility_cost
            },
            'capital_cost': capital_cost,
            'payback_period_years': payback_period,
            'total_heat_exchanger_area': total_area,
            'number_of_exchangers': len(self.heat_exchangers),
            'optimization_potential': {
                'max_heat_recovery': base_case['heat_recovery'],
                'current_heat_recovery': sum(abs(exchanger.hot_stream.heat_duty) 
                                            for exchanger in self.heat_exchangers.values()),
                'improvement_opportunity': base_case['heat_recovery'] - 
                                          sum(abs(exchanger.hot_stream.heat_duty) 
                                              for exchanger in self.heat_exchangers.values())
            }
        }
    
    def generate_heat_balance_report(self) -> str:
        """生成热量平衡报告"""
        overall_balance = self.calculate_overall_heat_balance()
        energy_efficiency = self.calculate_energy_efficiency()
        
        report = f"""
        ===========================================
        热量平衡报告
        ===========================================
        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        === 总体热量平衡 ===
        总热输入: {overall_balance['total_heat_input']:,.0f} kJ/h
        总热输出: {overall_balance['total_heat_output']:,.0f} kJ/h
        反应生成热: {overall_balance['heat_generated']:,.0f} kJ/h
        反应消耗热: {overall_balance['heat_consumed']:,.0f} kJ/h
        热损失: {overall_balance['heat_loss']:,.0f} kJ/h
        平衡误差: {overall_balance['balance_error_percent']:.2f} %
        热效率: {overall_balance['thermal_efficiency']:.1f} %
        
        === 能源效率指标 ===
        总热回收率: {energy_efficiency['heat_recovery_rate']:.1f} %
        总换热负荷: {energy_efficiency['total_heat_exchanged']:,.0f} kJ/h
        能源强度: {energy_efficiency['energy_intensity']:.3f} kJ/kJ
        
        === 换热器统计 ===
        换热器总数: {len(self.heat_exchangers)}
        """
        
        if self.heat_exchangers:
            report += "\n=== 各换热器性能 ===\n"
            for exchanger_id, exchanger in self.heat_exchangers.items():
                calc = exchanger.calculate_heat_transfer()
                report += f"""
                换热器: {exchanger.name} ({exchanger_id})
                类型: {exchanger.exchanger_type.value}
                热负荷: {calc['heat_duty']:,.0f} kJ/h
                对数平均温差: {calc['lmtd']:.1f} ℃
                传热面积: {exchanger.area:.1f} m²
                面积效率: {calc['area_efficiency']:.1f} %
                温度接近点: {calc['temperature_approach']:.1f} ℃
                """
        
        report += """
        ===========================================
        """
        
        return report