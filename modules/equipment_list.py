"""
设备清单管理模块
用于管理工艺流程中所有设备的信息和规格
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum
from datetime import datetime
import json


class EquipmentStatus(Enum):
    """设备状态"""
    DESIGN = "设计"
    OPERATING = "运行"
    MAINTENANCE = "维修"
    STANDBY = "备用"
    DECOMMISSIONED = "停用"


class EquipmentMaterial(Enum):
    """设备材料"""
    CARBON_STEEL = "碳钢"
    STAINLESS_STEEL_304 = "不锈钢304"
    STAINLESS_STEEL_316 = "不锈钢316"
    HASTELLOY = "哈氏合金"
    TITANIUM = "钛"
    GLASS_LINED = "搪玻璃"
    FRP = "玻璃钢"
    PVC = "PVC"
    PP = "聚丙烯"


@dataclass
class EquipmentDimension:
    """设备尺寸"""
    diameter: Optional[float] = None  # 直径，mm
    height: Optional[float] = None    # 高度，mm
    length: Optional[float] = None    # 长度，mm
    width: Optional[float] = None     # 宽度，mm
    thickness: Optional[float] = None # 壁厚，mm
    volume: Optional[float] = None    # 容积，m³


@dataclass
class EquipmentSpecification:
    """设备规格"""
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    design_pressure: Optional[float] = None  # 设计压力，MPa
    design_temperature: Optional[float] = None  # 设计温度，℃
    operating_pressure: Optional[float] = None  # 操作压力，MPa
    operating_temperature: Optional[float] = None  # 操作温度，℃
    material_of_construction: Optional[str] = None  # 结构材料
    material_of_wetted_parts: Optional[str] = None  # 接触物料材料
    weight: Optional[float] = None  # 重量，kg
    power: Optional[float] = None  # 功率，kW
    efficiency: Optional[float] = None  # 效率，%


@dataclass
class MaintenanceRecord:
    """维护记录"""
    date: datetime
    type: str  # 维护类型
    description: str
    cost: float  # 费用
    performed_by: str  # 执行人
    next_maintenance_date: Optional[datetime] = None


class EquipmentItem:
    """设备项"""
    
    def __init__(self, equipment_id: str, name: str, equipment_type: str,
                 tag_number: str, unit_operation_id: str):
        self.equipment_id = equipment_id
        self.name = name
        self.equipment_type = equipment_type
        self.tag_number = tag_number
        self.unit_operation_id = unit_operation_id
        
        self.status = EquipmentStatus.DESIGN
        self.dimensions = EquipmentDimension()
        self.specifications = EquipmentSpecification()
        self.maintenance_history: List[MaintenanceRecord] = []
        
        self.created_date = datetime.now()
        self.updated_date = datetime.now()
        
        # 成本信息
        self.purchase_cost: Optional[float] = None
        self.installation_cost: Optional[float] = None
        self.estimated_lifetime: Optional[int] = None  # 年
        
        # 性能参数
        self.capacity: Optional[float] = None
        self.utilization: float = 0.0  # 利用率，%
        self.availability: float = 100.0  # 可用率，%
        
        # 附件
        self.attachments: List[str] = []  # 附件文件路径列表
        self.notes: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'equipment_id': self.equipment_id,
            'name': self.name,
            'equipment_type': self.equipment_type,
            'tag_number': self.tag_number,
            'unit_operation_id': self.unit_operation_id,
            'status': self.status.value,
            'dimensions': {
                'diameter': self.dimensions.diameter,
                'height': self.dimensions.height,
                'length': self.dimensions.length,
                'width': self.dimensions.width,
                'thickness': self.dimensions.thickness,
                'volume': self.dimensions.volume
            },
            'specifications': {
                'model': self.specifications.model,
                'manufacturer': self.specifications.manufacturer,
                'design_pressure': self.specifications.design_pressure,
                'design_temperature': self.specifications.design_temperature,
                'operating_pressure': self.specifications.operating_pressure,
                'operating_temperature': self.specifications.operating_temperature,
                'material_of_construction': self.specifications.material_of_construction,
                'material_of_wetted_parts': self.specifications.material_of_wetted_parts,
                'weight': self.specifications.weight,
                'power': self.specifications.power,
                'efficiency': self.specifications.efficiency
            },
            'cost': {
                'purchase': self.purchase_cost,
                'installation': self.installation_cost,
                'estimated_lifetime': self.estimated_lifetime
            },
            'performance': {
                'capacity': self.capacity,
                'utilization': self.utilization,
                'availability': self.availability
            },
            'maintenance_count': len(self.maintenance_history),
            'created_date': self.created_date,
            'updated_date': self.updated_date,
            'notes': self.notes
        }


class EquipmentListManager:
    """设备清单管理器"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.equipment_items = {}  # equipment_id -> EquipmentItem
        self.vendor_info = {}  # 供应商信息
        
    def add_equipment(self, equipment_data: Dict) -> str:
        """添加设备"""
        required_fields = ['name', 'equipment_type', 'tag_number', 'unit_operation_id']
        for field in required_fields:
            if field not in equipment_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        equipment_id = f"EQ{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建设备项
        equipment = EquipmentItem(
            equipment_id=equipment_id,
            name=equipment_data['name'],
            equipment_type=equipment_data['equipment_type'],
            tag_number=equipment_data['tag_number'],
            unit_operation_id=equipment_data['unit_operation_id']
        )
        
        # 设置可选字段
        if 'status' in equipment_data:
            equipment.status = EquipmentStatus(equipment_data['status'])
        
        # 设置尺寸
        if 'dimensions' in equipment_data:
            for key, value in equipment_data['dimensions'].items():
                if hasattr(equipment.dimensions, key):
                    setattr(equipment.dimensions, key, value)
        
        # 设置规格
        if 'specifications' in equipment_data:
            for key, value in equipment_data['specifications'].items():
                if hasattr(equipment.specifications, key):
                    setattr(equipment.specifications, key, value)
        
        # 设置成本
        if 'purchase_cost' in equipment_data:
            equipment.purchase_cost = equipment_data['purchase_cost']
        if 'installation_cost' in equipment_data:
            equipment.installation_cost = equipment_data['installation_cost']
        if 'estimated_lifetime' in equipment_data:
            equipment.estimated_lifetime = equipment_data['estimated_lifetime']
        
        # 设置性能
        if 'capacity' in equipment_data:
            equipment.capacity = equipment_data['capacity']
        if 'utilization' in equipment_data:
            equipment.utilization = equipment_data['utilization']
        if 'availability' in equipment_data:
            equipment.availability = equipment_data['availability']
        
        # 保存
        self.equipment_items[equipment_id] = equipment
        
        if self.db:
            self.db.insert('equipment', equipment.to_dict())
        
        return equipment_id
    
    def update_equipment(self, equipment_id: str, updates: Dict) -> bool:
        """更新设备信息"""
        if equipment_id not in self.equipment_items:
            return False
        
        equipment = self.equipment_items[equipment_id]
        
        # 更新基本信息
        for key in ['name', 'tag_number', 'unit_operation_id']:
            if key in updates:
                setattr(equipment, key, updates[key])
        
        # 更新状态
        if 'status' in updates:
            equipment.status = EquipmentStatus(updates['status'])
        
        # 更新尺寸
        if 'dimensions' in updates:
            for key, value in updates['dimensions'].items():
                if hasattr(equipment.dimensions, key):
                    setattr(equipment.dimensions, key, value)
        
        # 更新规格
        if 'specifications' in updates:
            for key, value in updates['specifications'].items():
                if hasattr(equipment.specifications, key):
                    setattr(equipment.specifications, key, value)
        
        # 更新成本
        for key in ['purchase_cost', 'installation_cost', 'estimated_lifetime']:
            if key in updates:
                setattr(equipment, key, updates[key])
        
        # 更新性能
        for key in ['capacity', 'utilization', 'availability']:
            if key in updates:
                setattr(equipment, key, updates[key])
        
        # 更新备注
        if 'notes' in updates:
            equipment.notes = updates['notes']
        
        equipment.updated_date = datetime.now()
        
        if self.db:
            self.db.update('equipment', {'equipment_id': equipment_id}, equipment.to_dict())
        
        return True
    
    def add_maintenance_record(self, equipment_id: str, 
                             record_data: Dict) -> bool:
        """添加维护记录"""
        if equipment_id not in self.equipment_items:
            return False
        
        required_fields = ['date', 'type', 'description', 'performed_by']
        for field in required_fields:
            if field not in record_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        record = MaintenanceRecord(
            date=record_data['date'],
            type=record_data['type'],
            description=record_data['description'],
            cost=record_data.get('cost', 0),
            performed_by=record_data['performed_by'],
            next_maintenance_date=record_data.get('next_maintenance_date')
        )
        
        equipment = self.equipment_items[equipment_id]
        equipment.maintenance_history.append(record)
        equipment.updated_date = datetime.now()
        
        # 更新可用率
        self._update_equipment_availability(equipment_id)
        
        if self.db:
            self.db.update('equipment', {'equipment_id': equipment_id}, 
                          {'maintenance_history': equipment.maintenance_history})
        
        return True
    
    def _update_equipment_availability(self, equipment_id: str):
        """更新设备可用率"""
        equipment = self.equipment_items.get(equipment_id)
        if not equipment:
            return
        
        # 简化的可用率计算
        # 在实际应用中，这里应该基于维护历史和运行时间计算
        total_records = len(equipment.maintenance_history)
        
        if total_records == 0:
            equipment.availability = 100.0
        else:
            # 假设每次维护降低1%的可用率
            equipment.availability = max(70.0, 100.0 - total_records * 1.0)
    
    def get_equipment_by_type(self, equipment_type: str) -> List[EquipmentItem]:
        """按类型获取设备"""
        return [eq for eq in self.equipment_items.values() 
                if eq.equipment_type == equipment_type]
    
    def get_equipment_by_unit(self, unit_operation_id: str) -> List[EquipmentItem]:
        """按单元操作获取设备"""
        return [eq for eq in self.equipment_items.values() 
                if eq.unit_operation_id == unit_operation_id]
    
    def get_equipment_by_status(self, status: EquipmentStatus) -> List[EquipmentItem]:
        """按状态获取设备"""
        return [eq for eq in self.equipment_items.values() 
                if eq.status == status]
    
    def calculate_equipment_costs(self) -> Dict:
        """计算设备成本汇总"""
        total_purchase = 0
        total_installation = 0
        equipment_count = len(self.equipment_items)
        
        type_costs = {}
        unit_costs = {}
        
        for equipment in self.equipment_items.values():
            # 总成本
            if equipment.purchase_cost:
                total_purchase += equipment.purchase_cost
            if equipment.installation_cost:
                total_installation += equipment.installation_cost
            
            # 按类型统计
            eq_type = equipment.equipment_type
            if eq_type not in type_costs:
                type_costs[eq_type] = {'purchase': 0, 'installation': 0, 'count': 0}
            
            if equipment.purchase_cost:
                type_costs[eq_type]['purchase'] += equipment.purchase_cost
            if equipment.installation_cost:
                type_costs[eq_type]['installation'] += equipment.installation_cost
            type_costs[eq_type]['count'] += 1
            
            # 按单元统计
            unit_id = equipment.unit_operation_id
            if unit_id not in unit_costs:
                unit_costs[unit_id] = {'purchase': 0, 'installation': 0, 'count': 0}
            
            if equipment.purchase_cost:
                unit_costs[unit_id]['purchase'] += equipment.purchase_cost
            if equipment.installation_cost:
                unit_costs[unit_id]['installation'] += equipment.installation_cost
            unit_costs[unit_id]['count'] += 1
        
        return {
            'total_purchase_cost': total_purchase,
            'total_installation_cost': total_installation,
            'total_equipment_cost': total_purchase + total_installation,
            'equipment_count': equipment_count,
            'average_cost_per_equipment': (total_purchase + total_installation) / equipment_count 
                                         if equipment_count > 0 else 0,
            'cost_by_type': type_costs,
            'cost_by_unit': unit_costs
        }
    
    def generate_equipment_list_report(self, report_format: str = 'text') -> str:
        """生成设备清单报告"""
        if report_format == 'text':
            return self._generate_text_report()
        elif report_format == 'html':
            return self._generate_html_report()
        elif report_format == 'csv':
            return self._generate_csv_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 100)
        lines.append("设备清单报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"设备总数: {len(self.equipment_items)}")
        lines.append("=" * 100)
        
        # 按单元操作分组
        units_dict = {}
        for equipment in self.equipment_items.values():
            unit_id = equipment.unit_operation_id
            if unit_id not in units_dict:
                units_dict[unit_id] = []
            units_dict[unit_id].append(equipment)
        
        for unit_id, equipment_list in units_dict.items():
            lines.append(f"\n单元操作: {unit_id}")
            lines.append("-" * 50)
            
            for equipment in equipment_list:
                lines.append(f"\n设备ID: {equipment.equipment_id}")
                lines.append(f"名称: {equipment.name}")
                lines.append(f"位号: {equipment.tag_number}")
                lines.append(f"类型: {equipment.equipment_type}")
                lines.append(f"状态: {equipment.status.value}")
                
                if equipment.capacity:
                    lines.append(f"能力: {equipment.capacity}")
                if equipment.utilization > 0:
                    lines.append(f"利用率: {equipment.utilization}%")
                lines.append(f"可用率: {equipment.availability}%")
                
                if equipment.purchase_cost:
                    lines.append(f"采购成本: ¥{equipment.purchase_cost:,.2f}")
                
                lines.append(f"维护记录: {len(equipment.maintenance_history)} 条")
        
        # 成本汇总
        cost_summary = self.calculate_equipment_costs()
        lines.append("\n" + "=" * 100)
        lines.append("成本汇总")
        lines.append("-" * 50)
        lines.append(f"总采购成本: ¥{cost_summary['total_purchase_cost']:,.2f}")
        lines.append(f"总安装成本: ¥{cost_summary['total_installation_cost']:,.2f}")
        lines.append(f"设备总成本: ¥{cost_summary['total_equipment_cost']:,.2f}")
        lines.append(f"平均设备成本: ¥{cost_summary['average_cost_per_equipment']:,.2f}")
        
        return '\n'.join(lines)
    
    def _generate_html_report(self) -> str:
        """生成HTML格式报告"""
        cost_summary = self.calculate_equipment_costs()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>设备清单报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #3498db; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .status-design {{ color: #3498db; }}
                .status-operating {{ color: #27ae60; }}
                .status-maintenance {{ color: #e67e22; }}
                .status-standby {{ color: #95a5a6; }}
                .status-decommissioned {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <h1>设备清单报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h3>总体统计</h3>
                <p>设备总数: {len(self.equipment_items)}</p>
                <p>总采购成本: ¥{cost_summary['total_purchase_cost']:,.2f}</p>
                <p>总安装成本: ¥{cost_summary['total_installation_cost']:,.2f}</p>
                <p>设备总成本: ¥{cost_summary['total_equipment_cost']:,.2f}</p>
            </div>
            
            <h2>设备清单</h2>
            <table>
                <tr>
                    <th>设备ID</th>
                    <th>名称</th>
                    <th>位号</th>
                    <th>类型</th>
                    <th>单元操作</th>
                    <th>状态</th>
                    <th>能力</th>
                    <th>可用率</th>
                    <th>采购成本</th>
                    <th>维护记录</th>
                </tr>
        """
        
        for equipment in self.equipment_items.values():
            status_class = f"status-{equipment.status.value.lower().replace(' ', '-')}"
            
            html += f"""
                <tr>
                    <td>{equipment.equipment_id}</td>
                    <td>{equipment.name}</td>
                    <td>{equipment.tag_number}</td>
                    <td>{equipment.equipment_type}</td>
                    <td>{equipment.unit_operation_id}</td>
                    <td class="{status_class}">{equipment.status.value}</td>
                    <td>{equipment.capacity if equipment.capacity else 'N/A'}</td>
                    <td>{equipment.availability:.1f}%</td>
                    <td>{"¥{:,}".format(equipment.purchase_cost) if equipment.purchase_cost else 'N/A'}</td>
                    <td>{len(equipment.maintenance_history)}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _generate_csv_report(self) -> str:
        """生成CSV格式报告"""
        headers = ['设备ID', '名称', '位号', '类型', '单元操作', '状态', 
                  '能力', '可用率(%)', '采购成本', '安装成本', '维护记录数']
        
        rows = []
        for equipment in self.equipment_items.values():
            row = [
                equipment.equipment_id,
                equipment.name,
                equipment.tag_number,
                equipment.equipment_type,
                equipment.unit_operation_id,
                equipment.status.value,
                equipment.capacity if equipment.capacity else '',
                f"{equipment.availability:.1f}",
                f"{equipment.purchase_cost}" if equipment.purchase_cost else '',
                f"{equipment.installation_cost}" if equipment.installation_cost else '',
                str(len(equipment.maintenance_history))
            ]
            rows.append(','.join(row))
        
        return '\n'.join([','.join(headers)] + rows)
    
    def get_maintenance_schedule(self, days_ahead: int = 30) -> List[Dict]:
        """获取即将到来的维护计划"""
        upcoming_maintenance = []
        today = datetime.now()
        
        for equipment in self.equipment_items.values():
            for record in equipment.maintenance_history:
                if record.next_maintenance_date:
                    days_until = (record.next_maintenance_date - today).days
                    if 0 <= days_until <= days_ahead:
                        upcoming_maintenance.append({
                            'equipment_id': equipment.equipment_id,
                            'equipment_name': equipment.name,
                            'tag_number': equipment.tag_number,
                            'last_maintenance_date': record.date,
                            'last_maintenance_type': record.type,
                            'next_maintenance_date': record.next_maintenance_date,
                            'days_until': days_until,
                            'unit_operation': equipment.unit_operation_id
                        })
        
        # 按时间排序
        upcoming_maintenance.sort(key=lambda x: x['next_maintenance_date'])
        
        return upcoming_maintenance
    
    def calculate_equipment_reliability(self) -> Dict:
        """计算设备可靠性指标"""
        if not self.equipment_items:
            return {}
        
        total_availability = 0
        total_maintenance_count = 0
        equipment_by_type = {}
        
        for equipment in self.equipment_items.values():
            total_availability += equipment.availability
            total_maintenance_count += len(equipment.maintenance_history)
            
            eq_type = equipment.equipment_type
            if eq_type not in equipment_by_type:
                equipment_by_type[eq_type] = {
                    'count': 0,
                    'total_availability': 0,
                    'total_maintenance': 0
                }
            
            equipment_by_type[eq_type]['count'] += 1
            equipment_by_type[eq_type]['total_availability'] += equipment.availability
            equipment_by_type[eq_type]['total_maintenance'] += len(equipment.maintenance_history)
        
        # 计算平均指标
        avg_availability = total_availability / len(self.equipment_items)
        avg_maintenance_frequency = total_maintenance_count / len(self.equipment_items)
        
        # 计算按类型统计
        type_reliability = {}
        for eq_type, data in equipment_by_type.items():
            type_reliability[eq_type] = {
                'average_availability': data['total_availability'] / data['count'],
                'average_maintenance_frequency': data['total_maintenance'] / data['count'],
                'equipment_count': data['count']
            }
        
        return {
            'total_equipment_count': len(self.equipment_items),
            'average_availability': avg_availability,
            'average_maintenance_frequency': avg_maintenance_frequency,
            'total_maintenance_records': total_maintenance_count,
            'reliability_by_type': type_reliability,
            'overall_reliability_rating': self._calculate_reliability_rating(avg_availability)
        }
    
    def _calculate_reliability_rating(self, availability: float) -> str:
        """计算可靠性评级"""
        if availability >= 95:
            return "优秀"
        elif availability >= 90:
            return "良好"
        elif availability >= 85:
            return "一般"
        elif availability >= 80:
            return "需要注意"
        else:
            return "需改进"