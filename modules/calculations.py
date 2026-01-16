"""
通用计算工具模块
包含化工计算中常用的通用计算方法
"""

import numpy as np
from typing import Optional, List, Dict, Tuple, Union
from enum import Enum
from scipy import integrate
from scipy.optimize import fsolve, minimize


class UnitSystem(Enum):
    """单位制"""
    SI = "国际单位制"
    METRIC = "公制"
    IMPERIAL = "英制"
    US = "美制"


class PropertyPackage:
    """物性包基类"""
    
    @staticmethod
    def ideal_gas_law(pressure: float, volume: float, 
                     temperature: float, n: float) -> float:
        """理想气体定律"""
        R = 8.314462618  # J/(mol·K)
        return n * R * temperature / volume
    
    @staticmethod
    def van_der_waals(pressure: float, volume: float,
                     temperature: float, n: float,
                     a: float, b: float) -> float:
        """范德华方程"""
        R = 8.314462618
        return (n * R * temperature) / (volume - n * b) - (n**2 * a) / (volume**2)
    
    @staticmethod
    def raoults_law(x: List[float], vapor_pressures: List[float]) -> List[float]:
        """拉乌尔定律"""
        return [x_i * p_i for x_i, p_i in zip(x, vapor_pressures)]
    
    @staticmethod
    def henrys_law(concentration: float, henry_constant: float) -> float:
        """亨利定律"""
        return henry_constant * concentration


class ThermodynamicsCalculator:
    """热力学计算器"""
    
    @staticmethod
    def calculate_enthalpy(temperature: float, 
                          heat_capacity_coeffs: List[float],
                          reference_temperature: float = 298.15) -> float:
        """计算焓值"""
        # Cp = A + B*T + C*T² + D*T³
        T = temperature + 273.15  # 转换为K
        T_ref = reference_temperature
        
        if len(heat_capacity_coeffs) >= 4:
            A, B, C, D = heat_capacity_coeffs[:4]
            delta_H = (A * (T - T_ref) +
                      B/2 * (T**2 - T_ref**2) +
                      C/3 * (T**3 - T_ref**3) +
                      D/4 * (T**4 - T_ref**4))
        else:
            # 常数比热容
            Cp = heat_capacity_coeffs[0] if heat_capacity_coeffs else 0
            delta_H = Cp * (T - T_ref)
        
        return delta_H
    
    @staticmethod
    def calculate_entropy(temperature: float,
                         heat_capacity_coeffs: List[float],
                         reference_temperature: float = 298.15) -> float:
        """计算熵值"""
        T = temperature + 273.15
        T_ref = reference_temperature
        
        if len(heat_capacity_coeffs) >= 4:
            A, B, C, D = heat_capacity_coeffs[:4]
            delta_S = (A * np.log(T/T_ref) +
                      B * (T - T_ref) +
                      C/2 * (T**2 - T_ref**2) +
                      D/3 * (T**3 - T_ref**3))
        else:
            Cp = heat_capacity_coeffs[0] if heat_capacity_coeffs else 0
            delta_S = Cp * np.log(T/T_ref)
        
        return delta_S
    
    @staticmethod
    def calculate_gibbs_free_energy(delta_H: float, 
                                   delta_S: float,
                                   temperature: float) -> float:
        """计算吉布斯自由能"""
        T = temperature + 273.15
        return delta_H - T * delta_S
    
    @staticmethod
    def calculate_vapor_pressure(temperature: float,
                                antoine_coeffs: Dict[str, float]) -> float:
        """使用安托万方程计算蒸气压"""
        # log10(P) = A - B/(T + C)
        A = antoine_coeffs.get('A', 0)
        B = antoine_coeffs.get('B', 0)
        C = antoine_coeffs.get('C', 0)
        
        if temperature + C == 0:
            return 0
        
        log10_p = A - B/(temperature + C)
        return 10**log10_p  # 返回kPa


class FluidMechanicsCalculator:
    """流体力学计算器"""
    
    @staticmethod
    def calculate_pressure_drop(flow_rate: float,
                               pipe_diameter: float,
                               pipe_length: float,
                               fluid_density: float,
                               fluid_viscosity: float,
                               pipe_roughness: float = 0.046e-3) -> float:
        """计算管道压降（Darcy-Weisbach方程）"""
        # 计算流速
        area = np.pi * (pipe_diameter/2)**2
        velocity = flow_rate / area
        
        # 计算雷诺数
        Re = (fluid_density * velocity * pipe_diameter) / fluid_viscosity
        
        # 计算摩擦因子（Churchill方程）
        if Re < 2300:
            # 层流
            f = 64 / Re
        else:
            # 湍流，使用Churchill方程
            A = (2.457 * np.log(1/((7/Re)**0.9 + 0.27*pipe_roughness/pipe_diameter)))**16
            B = (37530/Re)**16
            f = 8 * ((8/Re)**12 + 1/(A + B)**1.5)**(1/12)
        
        # 计算压降
        delta_p = f * (pipe_length/pipe_diameter) * (fluid_density * velocity**2) / 2
        
        return delta_p  # Pa
    
    @staticmethod
    def calculate_pump_power(flow_rate: float,
                            pressure_drop: float,
                            pump_efficiency: float = 0.75) -> float:
        """计算泵功率"""
        # P = (Q * ΔP) / η
        power = (flow_rate * pressure_drop) / pump_efficiency  # W
        return power / 1000  # kW
    
    @staticmethod
    def calculate_orifice_flow(diameter: float,
                             pressure_drop: float,
                             fluid_density: float,
                             discharge_coefficient: float = 0.61) -> float:
        """计算孔板流量"""
        # Q = Cd * A * √(2*ΔP/ρ)
        area = np.pi * (diameter/2)**2
        flow_rate = discharge_coefficient * area * np.sqrt(2 * pressure_drop / fluid_density)
        return flow_rate


class HeatTransferCalculator:
    """传热计算器"""
    
    @staticmethod
    def calculate_overall_heat_transfer_coefficient(h_inside: float,
                                                   h_outside: float,
                                                   fouling_inside: float = 0.0002,
                                                   fouling_outside: float = 0.0002,
                                                   wall_conductivity: float = 50,
                                                   wall_thickness: float = 0.003) -> float:
        """计算总传热系数"""
        # 1/U = 1/h_i + R_fi + t_w/k_w + R_fo + 1/h_o
        R_total = (1/h_inside + fouling_inside + 
                  wall_thickness/wall_conductivity + 
                  fouling_outside + 1/h_outside)
        
        return 1 / R_total  # W/(m²·K)
    
    @staticmethod
    def calculate_log_mean_temperature_difference(t_hot_in: float,
                                                 t_hot_out: float,
                                                 t_cold_in: float,
                                                 t_cold_out: float) -> float:
        """计算对数平均温差"""
        delta_t1 = t_hot_in - t_cold_out
        delta_t2 = t_hot_out - t_cold_in
        
        if abs(delta_t1 - delta_t2) < 1e-6:
            return delta_t1
        
        if delta_t1 <= 0 or delta_t2 <= 0:
            raise ValueError("温度交叉，无法计算LMTD")
        
        return (delta_t1 - delta_t2) / np.log(delta_t1 / delta_t2)
    
    @staticmethod
    def calculate_ntu_effectiveness(m_hot: float, cp_hot: float,
                                  m_cold: float, cp_cold: float,
                                  ua: float) -> Tuple[float, float]:
        """计算NTU和效能"""
        C_hot = m_hot * cp_hot
        C_cold = m_cold * cp_cold
        
        C_min = min(C_hot, C_cold)
        C_max = max(C_hot, C_cold)
        C_ratio = C_min / C_max
        
        NTU = ua / C_min
        
        # 计算效能（逆流换热器）
        if C_ratio < 1:
            effectiveness = (1 - np.exp(-NTU * (1 - C_ratio))) / (1 - C_ratio * np.exp(-NTU * (1 - C_ratio)))
        else:
            effectiveness = NTU / (1 + NTU)
        
        return NTU, effectiveness


class ReactionEngineeringCalculator:
    """反应工程计算器"""
    
    @staticmethod
    def calculate_equilibrium_constant(delta_G: float,
                                      temperature: float) -> float:
        """计算平衡常数"""
        R = 8.314462618  # J/(mol·K)
        T = temperature + 273.15  # K
        return np.exp(-delta_G / (R * T))
    
    @staticmethod
    def calculate_reaction_rate(concentrations: List[float],
                               rate_constant: float,
                               reaction_order: List[float]) -> float:
        """计算反应速率"""
        rate = rate_constant
        for conc, order in zip(concentrations, reaction_order):
            rate *= conc**order
        return rate
    
    @staticmethod
    def calculate_space_time_yield(production_rate: float,
                                  reactor_volume: float) -> float:
        """计算空时收率"""
        return production_rate / reactor_volume  # kg/(m³·h)
    
    @staticmethod
    def calculate_damkohler_number(reaction_rate: float,
                                  characteristic_time: float,
                                  characteristic_concentration: float) -> float:
        """计算达姆科勒数"""
        return reaction_rate * characteristic_time / characteristic_concentration


class SeparationCalculator:
    """分离计算器"""
    
    @staticmethod
    def calculate_mccabe_thiele(num_stages: int,
                               reflux_ratio: float,
                               feed_quality: float = 1.0) -> Dict:
        """计算McCabe-Thiele理论塔板数"""
        # 简化计算，返回理论塔板数和进料板位置
        # 在实际应用中，需要完整的McCabe-Thiele图计算
        
        # 简化的经验公式
        if reflux_ratio <= 1.2:
            n_theoretical = 20
        elif reflux_ratio <= 2.0:
            n_theoretical = 15
        else:
            n_theoretical = 10
        
        # 估算进料板位置
        if feed_quality == 1.0:  # 饱和液体
            feed_stage = int(n_theoretical / 2)
        elif feed_quality == 0:  # 饱和蒸汽
            feed_stage = int(n_theoretical / 3)
        else:
            feed_stage = int(n_theoretical / 2.5)
        
        return {
            'theoretical_stages': n_theoretical,
            'feed_stage': feed_stage,
            'reflux_ratio': reflux_ratio,
            'minimum_reflux_ratio': reflux_ratio * 0.6  # 估算最小回流比
        }
    
    @staticmethod
    def calculate_kremser_equation(num_stages: int,
                                  absorption_factor: float,
                                  inlet_conc: float,
                                  equilibrium_conc: float) -> float:
        """计算Kremser方程（吸收塔）"""
        if abs(absorption_factor - 1) < 1e-6:
            # A = 1的特殊情况
            removal = num_stages / (num_stages + 1)
        else:
            removal = (absorption_factor**num_stages - absorption_factor) / (absorption_factor**num_stages - 1)
        
        outlet_conc = inlet_conc * (1 - removal) + equilibrium_conc * removal
        return outlet_conc
    
    @staticmethod
    def calculate_specific_sedimentation_area(flow_rate: float,
                                            solid_loading: float,
                                            settling_velocity: float) -> float:
        """计算比沉降面积"""
        # A = Q / (C * v)
        return flow_rate / (solid_loading * settling_velocity)


class EconomicCalculator:
    """经济计算器"""
    
    @staticmethod
    def calculate_capital_cost(equipment_cost: float,
                              installation_factor: float = 3.0) -> float:
        """计算投资成本"""
        # 兰氏因子法
        return equipment_cost * installation_factor
    
    @staticmethod
    def calculate_operating_cost(raw_material_cost: float,
                                utility_cost: float,
                                labor_cost: float,
                                maintenance_cost: float,
                                depreciation: float) -> float:
        """计算操作成本"""
        return (raw_material_cost + utility_cost + labor_cost + 
                maintenance_cost + depreciation)
    
    @staticmethod
    def calculate_break_even_point(fixed_costs: float,
                                  variable_cost_per_unit: float,
                                  selling_price_per_unit: float) -> float:
        """计算盈亏平衡点"""
        if selling_price_per_unit <= variable_cost_per_unit:
            return float('inf')
        
        return fixed_costs / (selling_price_per_unit - variable_cost_per_unit)
    
    @staticmethod
    def calculate_net_present_value(cash_flows: List[float],
                                   discount_rate: float) -> float:
        """计算净现值"""
        npv = 0
        for t, cash_flow in enumerate(cash_flows):
            npv += cash_flow / (1 + discount_rate)**t
        return npv
    
    @staticmethod
    def calculate_internal_rate_of_return(cash_flows: List[float]) -> float:
        """计算内部收益率"""
        def npv_function(rate):
            return sum(cf / (1 + rate)**i for i, cf in enumerate(cash_flows))
        
        try:
            # 使用数值方法求解IRR
            result = fsolve(npv_function, 0.1)
            return result[0]
        except:
            return 0


class SafetyCalculator:
    """安全计算器"""
    
    @staticmethod
    def calculate_flash_point(temperature: float,
                             vapor_pressure: float,
                             lower_flammable_limit: float) -> float:
        """计算闪点"""
        # 简化的闪点估算
        # 在实际应用中，需要详细的物性数据
        if vapor_pressure <= 0:
            return float('inf')
        
        # 基于蒸气压和爆炸下限估算
        pressure_at_flash = lower_flammable_limit * 101.325  # kPa
        flash_point = temperature * (pressure_at_flash / vapor_pressure)**0.5
        
        return flash_point
    
    @staticmethod
    def calculate_explosion_limits(concentrations: List[float],
                                  lower_limits: List[float],
                                  upper_limits: List[float]) -> Tuple[float, float]:
        """计算混合气体的爆炸极限"""
        # 使用Le Chatelier法则
        sum_lower = 0
        sum_upper = 0
        
        for conc, lel, uel in zip(concentrations, lower_limits, upper_limits):
            if conc > 0:
                sum_lower += conc / lel
                sum_upper += conc / uel
        
        mixture_lel = 1 / sum_lower if sum_lower > 0 else 0
        mixture_uel = 1 / sum_upper if sum_upper > 0 else float('inf')
        
        return mixture_lel, mixture_uel
    
    @staticmethod
    def calculate_relief_valve_size(flow_rate: float,
                                   pressure: float,
                                   temperature: float,
                                   fluid_properties: Dict) -> float:
        """计算安全阀尺寸"""
        # 基于API 520标准简化计算
        # 实际应用需要详细的计算
        
        # 简化的面积计算
        if fluid_properties.get('phase') == 'gas':
            # 气体
            k = fluid_properties.get('specific_heat_ratio', 1.4)
            Z = fluid_properties.get('compressibility', 1.0)
            MW = fluid_properties.get('molecular_weight', 29)
            
            area = flow_rate / (0.9 * pressure * np.sqrt(k * Z * temperature / MW))
        else:
            # 液体
            density = fluid_properties.get('density', 1000)
            area = flow_rate / (0.65 * np.sqrt(2 * density * pressure))
        
        # 转换为直径
        diameter = 2 * np.sqrt(area / np.pi)
        return diameter


class UnitConverter:
    """单位转换器"""
    
    @staticmethod
    def convert_temperature(value: float, 
                           from_unit: str, 
                           to_unit: str) -> float:
        """温度转换"""
        conversions = {
            ('C', 'K'): lambda x: x + 273.15,
            ('K', 'C'): lambda x: x - 273.15,
            ('C', 'F'): lambda x: x * 9/5 + 32,
            ('F', 'C'): lambda x: (x - 32) * 5/9,
            ('F', 'K'): lambda x: (x - 32) * 5/9 + 273.15,
            ('K', 'F'): lambda x: (x - 273.15) * 9/5 + 32
        }
        
        key = (from_unit.upper(), to_unit.upper())
        if key in conversions:
            return conversions[key](value)
        else:
            raise ValueError(f"不支持的温度转换: {from_unit} -> {to_unit}")
    
    @staticmethod
    def convert_pressure(value: float,
                        from_unit: str,
                        to_unit: str) -> float:
        """压力转换"""
        # 定义基本单位：Pa
        to_pa = {
            'PA': 1,
            'KPA': 1000,
            'MPA': 1e6,
            'BAR': 1e5,
            'ATM': 101325,
            'PSI': 6894.76,
            'MMHG': 133.322,
            'INHG': 3386.39
        }
        
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        
        if from_unit not in to_pa or to_unit not in to_pa:
            raise ValueError(f"不支持的压力单位: {from_unit} 或 {to_unit}")
        
        value_pa = value * to_pa[from_unit]
        return value_pa / to_pa[to_unit]
    
    @staticmethod
    def convert_flow_rate(value: float,
                         from_unit: str,
                         to_unit: str,
                         fluid_density: float = 1000) -> float:
        """流量转换"""
        # 定义基本单位：kg/h
        to_kgh = {
            'KG/H': 1,
            'KG/S': 3600,
            'G/S': 3.6,
            'L/H': lambda x, rho: x * rho,
            'L/MIN': lambda x, rho: x * 60 * rho,
            'L/S': lambda x, rho: x * 3600 * rho,
            'M3/H': lambda x, rho: x * 1000 * rho,
            'M3/S': lambda x, rho: x * 3600000 * rho,
            'GPM': lambda x, rho: x * 227.1 * rho / 1000,  # 美制加仑/分钟
            'CFM': lambda x, rho: x * 1699 * rho / 1000   # 立方英尺/分钟
        }
        
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        
        # 先转换为kg/h
        if callable(to_kgh.get(from_unit, 1)):
            value_kgh = to_kgh[from_unit](value, fluid_density)
        else:
            value_kgh = value * to_kgh.get(from_unit, 1)
        
        # 再转换为目标单位
        if to_unit in ['L/H', 'L/MIN', 'L/S', 'M3/H', 'M3/S', 'GPM', 'CFM']:
            # 需要反函数
            # 简化处理：对于体积流量，假设密度不变
            if to_unit == 'L/H':
                return value_kgh / fluid_density
            elif to_unit == 'L/MIN':
                return value_kgh / fluid_density / 60
            elif to_unit == 'L/S':
                return value_kgh / fluid_density / 3600
            elif to_unit == 'M3/H':
                return value_kgh / fluid_density / 1000
            elif to_unit == 'M3/S':
                return value_kgh / fluid_density / 1000 / 3600
            elif to_unit == 'GPM':
                return value_kgh / fluid_density * 1000 / 227.1
            elif to_unit == 'CFM':
                return value_kgh / fluid_density * 1000 / 1699
        else:
            return value_kgh / to_kgh.get(to_unit, 1)


class NumericalMethods:
    """数值方法"""
    
    @staticmethod
    def solve_ode_system(equations, initial_conditions, 
                        t_span, method='RK45'):
        """求解常微分方程组"""
        from scipy.integrate import solve_ivp
        
        solution = solve_ivp(equations, t_span, initial_conditions, 
                            method=method, dense_output=True)
        return solution
    
    @staticmethod
    def solve_algebraic_system(equations, initial_guess):
        """求解代数方程组"""
        from scipy.optimize import fsolve
        
        solution = fsolve(equations, initial_guess, full_output=True)
        return solution
    
    @staticmethod
    def perform_regression(x_data, y_data, degree=1):
        """多项式回归"""
        coefficients = np.polyfit(x_data, y_data, degree)
        polynomial = np.poly1d(coefficients)
        
        # 计算R²
        y_pred = polynomial(x_data)
        ss_res = np.sum((y_data - y_pred)**2)
        ss_tot = np.sum((y_data - np.mean(y_data))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        return {
            'coefficients': coefficients,
            'polynomial': polynomial,
            'r_squared': r_squared,
            'predictions': y_pred
        }
    
    @staticmethod
    def interpolate_data(x_data, y_data, x_new, method='cubic'):
        """数据插值"""
        from scipy.interpolate import interp1d
        
        if method == 'linear':
            f = interp1d(x_data, y_data, kind='linear', fill_value='extrapolate')
        elif method == 'cubic':
            f = interp1d(x_data, y_data, kind='cubic', fill_value='extrapolate')
        elif method == 'spline':
            from scipy.interpolate import UnivariateSpline
            f = UnivariateSpline(x_data, y_data, s=0)
        else:
            raise ValueError(f"不支持的插值方法: {method}")
        
        y_new = f(x_new)
        return y_new


# 使用示例
if __name__ == "__main__":
    # 示例用法
    thermo = ThermodynamicsCalculator()
    enthalpy = thermo.calculate_enthalpy(100, [30, 0.1, 0.001, 0.00001])
    print(f"焓值: {enthalpy:.2f} J/mol")
    
    fluid = FluidMechanicsCalculator()
    pressure_drop = fluid.calculate_pressure_drop(10, 0.1, 100, 1000, 0.001)
    print(f"压降: {pressure_drop:.2f} Pa")
    
    converter = UnitConverter()
    temp_c = converter.convert_temperature(100, 'C', 'F')
    print(f"100°C = {temp_c:.2f}°F")