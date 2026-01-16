"""
物料参数管理模块
用于管理工艺中使用的各种物料的基础物性参数
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
import json


class MaterialState(Enum):
    """物料状态枚举"""
    SOLID = "固体"
    LIQUID = "液体"
    GAS = "气体"
    SLURRY = "浆料"
    SUSPENSION = "悬浮液"


class MaterialCategory(Enum):
    """物料类别枚举"""
    RAW = "原料"
    INTERMEDIATE = "中间产物"
    PRODUCT = "产品"
    BYPRODUCT = "副产品"
    WASTE = "废物"
    AUXILIARY = "辅助物料"
    CATALYST = "催化剂"
    SOLVENT = "溶剂"


@dataclass
class MaterialProperty:
    """物料物性参数"""
    name: str
    value: float
    unit: str
    temperature: Optional[float] = None  # 测量温度，℃
    pressure: Optional[float] = None     # 测量压力，kPa
    source: str = "实测"                 # 数据来源


class MaterialParams:
    """物料参数管理类"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.materials = {}
        
    def add_material(self, material_data: Dict) -> bool:
        """添加新物料"""
        required_fields = ['name', 'cas_number', 'category', 'state']
        for field in required_fields:
            if field not in material_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        material_id = f"MAT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        material_data['id'] = material_id
        material_data['created_at'] = datetime.now()
        material_data['updated_at'] = datetime.now()
        
        # 保存到数据库
        if self.db:
            success = self.db.insert('materials', material_data)
            if success:
                self.materials[material_id] = material_data
                return True
        else:
            self.materials[material_id] = material_data
            return True
        
        return False
    
    def get_material(self, material_id: str) -> Optional[Dict]:
        """获取物料信息"""
        if self.db:
            return self.db.query_one('materials', {'id': material_id})
        return self.materials.get(material_id)
    
    def update_material(self, material_id: str, updates: Dict) -> bool:
        """更新物料信息"""
        updates['updated_at'] = datetime.now()
        
        if self.db:
            return self.db.update('materials', {'id': material_id}, updates)
        elif material_id in self.materials:
            self.materials[material_id].update(updates)
            return True
        
        return False
    
    def delete_material(self, material_id: str) -> bool:
        """删除物料"""
        if self.db:
            return self.db.delete('materials', {'id': material_id})
        elif material_id in self.materials:
            del self.materials[material_id]
            return True
        
        return False
    
    def search_materials(self, keyword: str = None, 
                        category: MaterialCategory = None,
                        state: MaterialState = None) -> List[Dict]:
        """搜索物料"""
        results = []
        
        if self.db:
            query = {}
            if keyword:
                query['name'] = f'%{keyword}%'
            if category:
                query['category'] = category.value
            if state:
                query['state'] = state.value
            results = self.db.query('materials', query)
        else:
            for mat in self.materials.values():
                match = True
                if keyword and keyword.lower() not in mat.get('name', '').lower():
                    match = False
                if category and mat.get('category') != category.value:
                    match = False
                if state and mat.get('state') != state.value:
                    match = False
                if match:
                    results.append(mat)
        
        return results
    
    def calculate_mixture_properties(self, components: List[Dict]) -> Dict:
        """计算混合物物性"""
        # 摩尔分数加权平均计算混合物物性
        total_moles = sum(comp.get('mole_fraction', 0) for comp in components)
        
        if total_moles == 0:
            return {}
        
        mixture_props = {
            'molecular_weight': 0,
            'density': 0,
            'heat_capacity': 0,
            'viscosity': 0,
            'surface_tension': 0,
            'boiling_point': 0
        }
        
        for comp in components:
            fraction = comp.get('mole_fraction', 0) / total_moles
            props = comp.get('properties', {})
            
            mixture_props['molecular_weight'] += props.get('molecular_weight', 0) * fraction
            mixture_props['density'] += props.get('density', 0) * fraction
            mixture_props['heat_capacity'] += props.get('heat_capacity', 0) * fraction
            mixture_props['viscosity'] += props.get('viscosity', 0) * fraction
            mixture_props['surface_tension'] += props.get('surface_tension', 0) * fraction
            mixture_props['boiling_point'] += props.get('boiling_point', 0) * fraction
        
        return mixture_props
    
    def export_to_json(self, material_ids: List[str] = None) -> str:
        """导出物料数据为JSON"""
        if material_ids:
            data = [self.get_material(mid) for mid in material_ids]
        else:
            data = list(self.materials.values())
        
        # 移除数据库连接对象
        for item in data:
            if 'db' in item:
                del item['db']
        
        return json.dumps(data, indent=2, default=str)
    
    def import_from_json(self, json_data: str) -> int:
        """从JSON导入物料数据"""
        data = json.loads(json_data)
        count = 0
        
        for item in data:
            if self.add_material(item):
                count += 1
        
        return count


# 常用物性计算方法
class PropertyCalculator:
    """物性计算器"""
    
    @staticmethod
    def calculate_density_at_temperature(base_density: float, 
                                        base_temp: float,
                                        target_temp: float,
                                        expansion_coefficient: float = 0.001) -> float:
        """根据温度计算密度"""
        # 简化计算，实际应用需考虑物料的膨胀系数
        delta_temp = target_temp - base_temp
        return base_density / (1 + expansion_coefficient * delta_temp)
    
    @staticmethod
    def calculate_viscosity_at_temperature(base_viscosity: float,
                                          base_temp: float,
                                          target_temp: float,
                                          activation_energy: float = 50000) -> float:
        """根据温度计算粘度（阿伦尼乌斯方程）"""
        R = 8.314  # 气体常数
        t1 = base_temp + 273.15  # 转换为开尔文
        t2 = target_temp + 273.15
        
        # 阿伦尼乌斯方程
        return base_viscosity * (t1 / t2) * (activation_energy / R * (1/t2 - 1/t1))
    
    @staticmethod
    def estimate_critical_properties(molecular_weight: float,
                                    boiling_point: float) -> Dict:
        """估算临界性质"""
        # 简单的经验关联式
        critical_temp = boiling_point * 1.5  # 简化的估算
        critical_pressure = 50.0  # bar, 简化估算
        critical_volume = 0.29 * molecular_weight  # L/mol
        
        return {
            'critical_temperature': critical_temp,
            'critical_pressure': critical_pressure,
            'critical_volume': critical_volume
        }