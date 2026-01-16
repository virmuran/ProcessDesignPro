"""
物料平衡计算模块
用于计算工艺流程中的物料平衡和收率
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum
import numpy as np
from scipy.optimize import least_squares


class ComponentType(Enum):
    """组分类型"""
    REACTANT = "反应物"
    PRODUCT = "产物"
    BYPRODUCT = "副产品"
    CATALYST = "催化剂"
    SOLVENT = "溶剂"
    IMPURITY = "杂质"


@dataclass
class Reaction:
    """化学反应"""
    reaction_id: str
    name: str
    stoichiometry: Dict[str, float]  # 组分ID -> 化学计量系数（反应物为负，产物为正）
    conversion: float  # 转化率，%
    selectivity: Dict[str, float]  # 组分ID -> 选择性，%
    heat_of_reaction: float  # 反应热，kJ/mol
    
    def calculate_extent(self, feed_compositions: Dict[str, float]) -> float:
        """计算反应程度"""
        # 找到限制反应物
        limiting_reactant = None
        min_ratio = float('inf')
        
        for component_id, coeff in self.stoichiometry.items():
            if coeff < 0:  # 反应物
                if component_id in feed_compositions:
                    ratio = feed_compositions[component_id] / abs(coeff)
                    if ratio < min_ratio:
                        min_ratio = ratio
                        limiting_reactant = component_id
        
        if limiting_reactant is None:
            return 0
        
        # 基于转化率计算反应程度
        feed_amount = feed_compositions.get(limiting_reactant, 0)
        extent = feed_amount * self.conversion / 100
        
        return extent
    
    def calculate_product_yields(self, feed_compositions: Dict[str, float]) -> Dict[str, float]:
        """计算产物收率"""
        extent = self.calculate_extent(feed_compositions)
        product_yields = {}
        
        for component_id, coeff in self.stoichiometry.items():
            if coeff > 0:  # 产物
                selectivity = self.selectivity.get(component_id, 100)
                yield_amount = extent * coeff * selectivity / 100
                product_yields[component_id] = yield_amount
        
        return product_yields


class MaterialBalanceCalculator:
    """物料平衡计算器"""
    
    def __init__(self):
        self.components = {}
        self.reactions = {}
        self.process_units = {}
        self.streams = {}
        
    def add_component(self, component_data: Dict) -> str:
        """添加组分"""
        required_fields = ['name', 'molecular_weight', 'density', 'component_type']
        for field in required_fields:
            if field not in component_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        component_id = f"C{len(self.components) + 1:03d}"
        self.components[component_id] = component_data
        
        return component_id
    
    def add_reaction(self, reaction_data: Dict) -> str:
        """添加反应"""
        required_fields = ['name', 'stoichiometry', 'conversion', 'selectivity']
        for field in required_fields:
            if field not in reaction_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        reaction_id = f"R{len(self.reactions) + 1:03d}"
        reaction = Reaction(
            reaction_id=reaction_id,
            name=reaction_data['name'],
            stoichiometry=reaction_data['stoichiometry'],
            conversion=reaction_data['conversion'],
            selectivity=reaction_data['selectivity'],
            heat_of_reaction=reaction_data.get('heat_of_reaction', 0)
        )
        
        self.reactions[reaction_id] = reaction
        
        return reaction_id
    
    def calculate_unit_material_balance(self, unit_id: str, 
                                       input_streams: List[Dict],
                                       output_streams: List[Dict]) -> Dict:
        """计算单元物料平衡"""
        # 汇总输入流组分
        total_input = {}
        for stream in input_streams:
            for component_id, amount in stream.get('components', {}).items():
                total_input[component_id] = total_input.get(component_id, 0) + amount
        
        # 汇总输出流组分
        total_output = {}
        for stream in output_streams:
            for component_id, amount in stream.get('components', {}).items():
                total_output[component_id] = total_output.get(component_id, 0) + amount
        
        # 计算平衡
        balance_result = {
            'unit_id': unit_id,
            'total_input': sum(total_input.values()),
            'total_output': sum(total_output.values()),
            'component_balance': {},
            'yields': {},
            'losses': {},
            'is_balanced': False
        }
        
        # 计算组分平衡
        all_components = set(total_input.keys()) | set(total_output.keys())
        
        for comp_id in all_components:
            input_amount = total_input.get(comp_id, 0)
            output_amount = total_output.get(comp_id, 0)
            
            if input_amount > 0:
                loss = input_amount - output_amount
                yield_pct = (output_amount / input_amount * 100) if input_amount > 0 else 0
                loss_pct = (loss / input_amount * 100) if input_amount > 0 else 0
                
                balance_result['component_balance'][comp_id] = {
                    'input': input_amount,
                    'output': output_amount,
                    'loss': loss,
                    'yield': yield_pct,
                    'loss_percent': loss_pct
                }
                
                balance_result['yields'][comp_id] = yield_pct
                balance_result['losses'][comp_id] = loss
            else:
                # 生成的组分
                balance_result['component_balance'][comp_id] = {
                    'input': 0,
                    'output': output_amount,
                    'loss': -output_amount,
                    'yield': 0,
                    'loss_percent': 0
                }
        
        # 检查总体平衡
        total_loss = sum(balance_result['losses'].values())
        if balance_result['total_input'] > 0:
            overall_loss_percent = (abs(total_loss) / balance_result['total_input'] * 100)
            balance_result['overall_loss_percent'] = overall_loss_percent
            balance_result['is_balanced'] = overall_loss_percent < 1.0  # 1%误差
        else:
            balance_result['overall_loss_percent'] = 0
            balance_result['is_balanced'] = True
        
        return balance_result
    
    def calculate_process_yield(self, main_product_id: str, 
                               total_feed_amount: float) -> Dict:
        """计算过程总收率"""
        # 查找所有包含主产物的反应
        product_yields = {}
        total_product = 0
        
        for reaction in self.reactions.values():
            if main_product_id in reaction.stoichiometry:
                # 假设使用标准进料量计算
                standard_feed = {comp_id: 100 for comp_id in reaction.stoichiometry.keys() 
                                if reaction.stoichiometry[comp_id] < 0}
                
                yields = reaction.calculate_product_yields(standard_feed)
                if main_product_id in yields:
                    product_yields[reaction.reaction_id] = yields[main_product_id]
                    total_product += yields[main_product_id]
        
        overall_yield = (total_product / total_feed_amount * 100) if total_feed_amount > 0 else 0
        
        return {
            'main_product': main_product_id,
            'total_feed': total_feed_amount,
            'total_product': total_product,
            'overall_yield': overall_yield,
            'reaction_yields': product_yields,
            'number_of_reactions': len(product_yields)
        }
    
    def optimize_material_balance(self, measured_data: Dict[str, float],
                                 tolerance: float = 0.01) -> Dict:
        """基于测量数据优化物料平衡"""
        # 使用最小二乘法调整物料平衡
        
        def balance_equations(params):
            """平衡方程"""
            residuals = []
            
            # 总质量守恒
            total_input = sum(params.get(f'input_{i}', 0) for i in range(len(measured_data)))
            total_output = sum(params.get(f'output_{i}', 0) for i in range(len(measured_data)))
            residuals.append(total_input - total_output)
            
            # 组分守恒
            for i, (comp_id, measured_value) in enumerate(measured_data.items()):
                input_key = f'input_{i}'
                output_key = f'output_{i}'
                
                if input_key in params and output_key in params:
                    residuals.append(params[input_key] - params[output_key] - measured_value)
            
            return residuals
        
        # 初始猜测
        initial_guess = []
        for i in range(len(measured_data) * 2):
            initial_guess.append(100.0)  # 初始猜测值
        
        # 优化
        result = least_squares(balance_equations, initial_guess, bounds=(0, np.inf))
        
        # 整理结果
        optimized_values = {}
        for i, (comp_id, _) in enumerate(measured_data.items()):
            optimized_values[f'{comp_id}_input'] = result.x[i * 2]
            optimized_values[f'{comp_id}_output'] = result.x[i * 2 + 1]
        
        return {
            'optimized_values': optimized_values,
            'success': result.success,
            'cost': result.cost,
            'message': result.message,
            'residuals': result.fun.tolist()
        }
    
    def calculate_material_efficiency(self) -> Dict:
        """计算物料效率指标"""
        if not self.streams:
            return {}
        
        # 计算总物料流
        total_input = 0
        total_output = 0
        total_byproduct = 0
        total_waste = 0
        
        component_flows = {}
        
        for stream_id, stream in self.streams.items():
            stream_type = stream.get('type', 'unknown')
            components = stream.get('components', {})
            
            total_flow = sum(components.values())
            
            if stream_type == 'feed':
                total_input += total_flow
                for comp_id, amount in components.items():
                    component_flows[comp_id] = component_flows.get(comp_id, 0) + amount
            elif stream_type == 'product':
                total_output += total_flow
            elif stream_type == 'byproduct':
                total_byproduct += total_flow
            elif stream_type == 'waste':
                total_waste += total_flow
        
        # 计算效率指标
        if total_input > 0:
            material_efficiency = (total_output / total_input * 100)
            atom_efficiency = self._calculate_atom_efficiency()
            e_factor = total_waste / total_output if total_output > 0 else 0
        else:
            material_efficiency = 0
            atom_efficiency = 0
            e_factor = 0
        
        return {
            'total_material_input': total_input,
            'total_product_output': total_output,
            'total_byproduct': total_byproduct,
            'total_waste': total_waste,
            'material_efficiency': material_efficiency,
            'atom_efficiency': atom_efficiency,
            'e_factor': e_factor,
            'product_yield': self._calculate_overall_yield(),
            'component_utilization': self._calculate_component_utilization(component_flows)
        }
    
    def _calculate_atom_efficiency(self) -> float:
        """计算原子效率"""
        # 简化的原子效率计算
        # 在实际应用中，需要基于分子结构和反应计量学
        total_atoms_in = 0
        total_atoms_out = 0
        
        # 这里使用简化的假设
        # 实际应用需要详细的分子结构数据
        for reaction in self.reactions.values():
            # 假设每个反应物分子贡献10个原子，每个产物分子贡献8个原子（简化）
            total_atoms_in += len([c for c in reaction.stoichiometry.values() if c < 0]) * 10
            total_atoms_out += len([c for c in reaction.stoichiometry.values() if c > 0]) * 8
        
        if total_atoms_in > 0:
            return (total_atoms_out / total_atoms_in * 100)
        return 0
    
    def _calculate_overall_yield(self) -> float:
        """计算总收率"""
        if not self.reactions:
            return 0
        
        total_yield = 1.0
        for reaction in self.reactions.values():
            # 基于转化率和选择性计算收率
            conversion = reaction.conversion / 100
            avg_selectivity = np.mean(list(reaction.selectivity.values())) / 100 if reaction.selectivity else 1.0
            reaction_yield = conversion * avg_selectivity
            total_yield *= reaction_yield
        
        return total_yield * 100
    
    def _calculate_component_utilization(self, component_flows: Dict[str, float]) -> Dict[str, float]:
        """计算组分利用率"""
        utilizations = {}
        
        # 查找主要反应物
        for reaction in self.reactions.values():
            for comp_id, coeff in reaction.stoichiometry.items():
                if coeff < 0:  # 反应物
                    if comp_id in component_flows:
                        # 简化的利用率计算
                        # 在实际应用中，需要基于实际反应程度计算
                        utilizations[comp_id] = min(100, reaction.conversion)
        
        return utilizations
    
    def generate_mass_balance_report(self) -> str:
        """生成物料平衡报告"""
        material_efficiency = self.calculate_material_efficiency()
        
        report = f"""
        ===========================================
        物料平衡报告
        ===========================================
        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        === 总体物料平衡 ===
        总物料输入: {material_efficiency.get('total_material_input', 0):,.2f} kg/h
        总产品输出: {material_efficiency.get('total_product_output', 0):,.2f} kg/h
        总副产品: {material_efficiency.get('total_byproduct', 0):,.2f} kg/h
        总废物: {material_efficiency.get('total_waste', 0):,.2f} kg/h
        
        === 效率指标 ===
        物料效率: {material_efficiency.get('material_efficiency', 0):.1f} %
        原子效率: {material_efficiency.get('atom_efficiency', 0):.1f} %
        E因子: {material_efficiency.get('e_factor', 0):.3f} kg废物/kg产品
        总收率: {material_efficiency.get('product_yield', 0):.1f} %
        
        === 反应统计 ===
        反应总数: {len(self.reactions)}
        """
        
        if self.reactions:
            report += "\n各反应性能:\n"
            for reaction_id, reaction in self.reactions.items():
                report += f"""
                反应: {reaction.name} ({reaction_id})
                转化率: {reaction.conversion:.1f} %
                选择性: {', '.join([f'{k}: {v}%' for k, v in reaction.selectivity.items()])}
                反应热: {reaction.heat_of_reaction:.1f} kJ/mol
                """
        
        report += f"""
        === 组分统计 ===
        总组分数: {len(self.components)}
        
        === 建议 ===
        """
        
        # 基于分析结果给出建议
        if material_efficiency.get('material_efficiency', 0) < 80:
            report += "1. 物料效率较低，建议优化反应条件以提高转化率和选择性\n"
        
        if material_efficiency.get('e_factor', 0) > 1.0:
            report += f"2. E因子较高({material_efficiency['e_factor']:.2f})，建议减少废物产生\n"
        
        if material_efficiency.get('atom_efficiency', 0) < 70:
            report += "3. 原子效率较低，建议优化反应路径或寻找更高效的催化剂\n"
        
        if not any(report.endswith(s) for s in ['\n', '\n\n']):
            report += "4. 当前工艺物料平衡表现良好，继续保持\n"
        
        report += """
        ===========================================
        """
        
        return report
    
    def perform_sensitivity_analysis(self, 
                                   parameter_ranges: Dict[str, Tuple[float, float]],
                                   num_points: int = 10) -> Dict:
        """进行敏感性分析"""
        results = {}
        
        for param_name, (min_val, max_val) in parameter_ranges.items():
            param_values = np.linspace(min_val, max_val, num_points)
            yields = []
            
            for val in param_values:
                # 更新参数值
                if param_name == 'conversion':
                    for reaction in self.reactions.values():
                        reaction.conversion = val
                
                # 计算收率
                efficiency = self.calculate_material_efficiency()
                yields.append(efficiency.get('product_yield', 0))
            
            results[param_name] = {
                'parameter_values': param_values.tolist(),
                'yield_values': yields,
                'sensitivity': np.std(yields) / np.mean(yields) if np.mean(yields) > 0 else 0
            }
        
        # 确定最敏感参数
        if results:
            sensitivities = {k: v['sensitivity'] for k, v in results.items()}
            most_sensitive = max(sensitivities.items(), key=lambda x: x[1])[0]
            least_sensitive = min(sensitivities.items(), key=lambda x: x[1])[0]
            
            results['_analysis'] = {
                'most_sensitive_parameter': most_sensitive,
                'least_sensitive_parameter': least_sensitive,
                'sensitivity_ranking': sorted(sensitivities.items(), key=lambda x: x[1], reverse=True)
            }
        
        return results