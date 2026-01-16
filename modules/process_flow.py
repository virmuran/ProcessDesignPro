"""
工艺路线管理模块
用于管理工艺流程图的绘制和工艺路线配置
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple, Any
from enum import Enum
import json
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import matplotlib.patches as mpatches


class UnitType(Enum):
    """单元操作类型"""
    REACTOR = "反应器"
    SEPARATOR = "分离器"
    HEAT_EXCHANGER = "换热器"
    PUMP = "泵"
    COMPRESSOR = "压缩机"
    VALVE = "阀门"
    TANK = "储罐"
    COLUMN = "塔器"
    FILTER = "过滤器"
    DRYER = "干燥器"
    MIXER = "混合器"
    SPLITTER = "分流器"


@dataclass
class UnitOperation:
    """单元操作"""
    unit_id: str
    name: str
    unit_type: UnitType
    position: Tuple[float, float]  # (x, y) 坐标
    parameters: Dict[str, Any]
    streams_in: List[str]  # 输入物流ID列表
    streams_out: List[str]  # 输出物流ID列表
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.description is None:
            self.description = f"{self.unit_type.value}: {self.name}"


@dataclass
class ProcessFlowConnection:
    """工艺流程图连接"""
    connection_id: str
    from_unit: str
    to_unit: str
    stream_id: str
    points: List[Tuple[float, float]]  # 连接点坐标列表，用于绘制折线


class ProcessFlowDiagram:
    """工艺流程图管理器"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.units = {}  # unit_id -> UnitOperation
        self.connections = {}  # connection_id -> ProcessFlowConnection
        self.graph = nx.DiGraph()
        
    def add_unit_operation(self, unit_data: Dict) -> str:
        """添加单元操作"""
        required_fields = ['name', 'unit_type', 'position']
        for field in required_fields:
            if field not in unit_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        unit_id = f"U{len(self.units) + 1:03d}"
        unit_data['unit_id'] = unit_id
        
        # 确保unit_type是UnitType枚举
        if isinstance(unit_data['unit_type'], str):
            unit_data['unit_type'] = UnitType(unit_data['unit_type'])
        
        unit = UnitOperation(**unit_data)
        self.units[unit_id] = unit
        
        # 添加到图中
        self.graph.add_node(unit_id, 
                           name=unit.name,
                           type=unit.unit_type.value,
                           position=unit.position)
        
        if self.db:
            self.db.insert('unit_operations', asdict(unit))
        
        return unit_id
    
    def add_connection(self, from_unit: str, to_unit: str, 
                      stream_id: str, points: List[Tuple[float, float]] = None) -> str:
        """添加单元操作间的连接"""
        # 验证单元是否存在
        if from_unit not in self.units or to_unit not in self.units:
            raise ValueError("单元操作不存在")
        
        connection_id = f"C{len(self.connections) + 1:03d}"
        
        # 如果没有提供点，生成默认连接路径
        if points is None:
            from_pos = self.units[from_unit].position
            to_pos = self.units[to_unit].position
            points = [from_pos, to_pos]
        
        connection = ProcessFlowConnection(
            connection_id=connection_id,
            from_unit=from_unit,
            to_unit=to_unit,
            stream_id=stream_id,
            points=points
        )
        
        self.connections[connection_id] = connection
        
        # 添加到图中
        self.graph.add_edge(from_unit, to_unit, 
                           stream_id=stream_id,
                           connection_id=connection_id)
        
        # 更新单元的物流连接
        self.units[from_unit].streams_out.append(stream_id)
        self.units[to_unit].streams_in.append(stream_id)
        
        if self.db:
            self.db.insert('flow_connections', asdict(connection))
        
        return connection_id
    
    def remove_unit(self, unit_id: str) -> bool:
        """删除单元操作及其连接"""
        if unit_id not in self.units:
            return False
        
        # 删除所有相关连接
        connections_to_remove = []
        for conn_id, conn in self.connections.items():
            if conn.from_unit == unit_id or conn.to_unit == unit_id:
                connections_to_remove.append(conn_id)
        
        for conn_id in connections_to_remove:
            del self.connections[conn_id]
        
        # 从图中删除
        self.graph.remove_node(unit_id)
        
        # 删除单元
        del self.units[unit_id]
        
        if self.db:
            self.db.delete('unit_operations', {'unit_id': unit_id})
            self.db.delete('flow_connections', {'from_unit': unit_id})
            self.db.delete('flow_connections', {'to_unit': unit_id})
        
        return True
    
    def get_process_sequence(self, start_unit: str = None) -> List[List[str]]:
        """获取工艺顺序（拓扑排序）"""
        try:
            if not self.graph.nodes:
                return []
            
            # 如果没有指定起始点，找到所有入度为0的节点（起始单元）
            if start_unit is None:
                start_nodes = [node for node, degree in self.graph.in_degree() if degree == 0]
            else:
                start_nodes = [start_unit]
            
            sequences = []
            for start in start_nodes:
                # 使用深度优先搜索获取路径
                for path in nx.all_simple_paths(self.graph, start, 
                                                [n for n in self.graph.nodes() 
                                                 if self.graph.out_degree(n) == 0]):
                    sequences.append(path)
            
            return sequences
        except nx.NetworkXError:
            return []
    
    def calculate_process_metrics(self) -> Dict:
        """计算工艺指标"""
        if not self.graph.nodes:
            return {}
        
        metrics = {
            'total_units': len(self.units),
            'total_connections': len(self.connections),
            'unit_type_distribution': {},
            'graph_density': nx.density(self.graph),
            'is_acyclic': nx.is_directed_acyclic_graph(self.graph),
            'longest_path': 0,
            'recycle_loops': []
        }
        
        # 统计单元类型分布
        for unit in self.units.values():
            unit_type = unit.unit_type.value
            metrics['unit_type_distribution'][unit_type] = \
                metrics['unit_type_distribution'].get(unit_type, 0) + 1
        
        # 计算最长路径（如果是有向无环图）
        if metrics['is_acyclic']:
            try:
                longest_path = nx.dag_longest_path_length(self.graph)
                metrics['longest_path'] = longest_path
            except:
                pass
        
        # 检测循环（如果图不是无环的）
        if not metrics['is_acyclic']:
            try:
                cycles = list(nx.simple_cycles(self.graph))
                metrics['recycle_loops'] = cycles
            except:
                pass
        
        # 计算连接复杂度
        total_possible_edges = len(self.units) * (len(self.units) - 1)
        if total_possible_edges > 0:
            metrics['connection_complexity'] = len(self.connections) / total_possible_edges
        else:
            metrics['connection_complexity'] = 0
        
        return metrics
    
    def export_to_json(self, include_layout: bool = True) -> str:
        """导出工艺路线为JSON"""
        data = {
            'units': {},
            'connections': {},
            'metadata': {
                'export_date': str(datetime.now()),
                'total_units': len(self.units),
                'total_connections': len(self.connections)
            }
        }
        
        # 导出单元操作
        for unit_id, unit in self.units.items():
            unit_dict = asdict(unit)
            # 转换枚举为字符串
            unit_dict['unit_type'] = unit.unit_type.value
            data['units'][unit_id] = unit_dict
        
        # 导出连接
        for conn_id, conn in self.connections.items():
            data['connections'][conn_id] = asdict(conn)
        
        if include_layout:
            data['layout'] = self._get_current_layout()
        
        return json.dumps(data, indent=2, default=str)
    
    def _get_current_layout(self) -> Dict:
        """获取当前布局信息"""
        layout = {}
        for unit_id, unit in self.units.items():
            layout[unit_id] = {
                'position': unit.position,
                'size': (100, 80),  # 默认大小
                'rotation': 0
            }
        return layout
    
    def import_from_json(self, json_data: str) -> int:
        """从JSON导入工艺路线"""
        data = json.loads(json_data)
        imported_count = 0
        
        # 导入单元操作
        if 'units' in data:
            for unit_id, unit_data in data['units'].items():
                try:
                    # 转换字符串为UnitType枚举
                    if 'unit_type' in unit_data and isinstance(unit_data['unit_type'], str):
                        unit_data['unit_type'] = UnitType(unit_data['unit_type'])
                    
                    self.units[unit_id] = UnitOperation(**unit_data)
                    imported_count += 1
                except Exception as e:
                    print(f"导入单元 {unit_id} 失败: {e}")
        
        # 导入连接
        if 'connections' in data:
            for conn_id, conn_data in data['connections'].items():
                try:
                    self.connections[conn_id] = ProcessFlowConnection(**conn_data)
                    
                    # 添加到图中
                    self.graph.add_edge(conn_data['from_unit'], 
                                       conn_data['to_unit'],
                                       stream_id=conn_data['stream_id'],
                                       connection_id=conn_id)
                except Exception as e:
                    print(f"导入连接 {conn_id} 失败: {e}")
        
        return imported_count
    
    def generate_pfd_diagram(self, output_file: str = None, 
                            show_labels: bool = True,
                            figsize: Tuple[float, float] = (12, 8)) -> plt.Figure:
        """生成工艺流程图"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # 设置背景
        ax.set_facecolor('#f0f0f0')
        ax.set_xlim(0, 1000)
        ax.set_ylim(0, 800)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 定义单元操作的图形
        unit_shapes = {
            UnitType.REACTOR: self._draw_reactor,
            UnitType.SEPARATOR: self._draw_separator,
            UnitType.HEAT_EXCHANGER: self._draw_heat_exchanger,
            UnitType.PUMP: self._draw_pump,
            UnitType.COMPRESSOR: self._draw_compressor,
            UnitType.TANK: self._draw_tank,
            UnitType.COLUMN: self._draw_column,
            UnitType.MIXER: self._draw_mixer,
            UnitType.SPLITTER: self._draw_splitter
        }
        
        # 绘制所有单元操作
        for unit in self.units.values():
            draw_func = unit_shapes.get(unit.unit_type, self._draw_default_unit)
            draw_func(ax, unit.position, unit.name, unit.unit_id)
        
        # 绘制所有连接
        for conn in self.connections.values():
            self._draw_connection(ax, conn.points, conn.stream_id)
        
        # 添加图例
        if show_labels:
            self._add_legend(ax)
        
        # 添加标题
        ax.set_title("工艺流程图", fontsize=16, fontweight='bold', pad=20)
        
        # 保存或显示
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _draw_reactor(self, ax, position, name, unit_id):
        """绘制反应器"""
        x, y = position
        width, height = 120, 80
        
        # 反应器主体
        reactor = Rectangle((x - width/2, y - height/2), width, height,
                           facecolor='#ffcccc', edgecolor='#cc0000', 
                           linewidth=2, zorder=2)
        ax.add_patch(reactor)
        
        # 搅拌器
        ax.plot([x, x], [y + height/2 - 10, y - height/2 + 10], 
                color='#666666', linewidth=3, zorder=3)
        
        # 标签
        ax.text(x, y, name, ha='center', va='center', 
                fontsize=9, fontweight='bold', zorder=4)
        ax.text(x, y - 20, unit_id, ha='center', va='center',
                fontsize=8, color='#666666', zorder=4)
    
    def _draw_separator(self, ax, position, name, unit_id):
        """绘制分离器"""
        x, y = position
        width, height = 100, 60
        
        # 分离器主体（椭圆形）
        separator = mpatches.Ellipse((x, y), width, height,
                                    facecolor='#ccffcc', edgecolor='#006600',
                                    linewidth=2, zorder=2)
        ax.add_patch(separator)
        
        # 标签
        ax.text(x, y, name, ha='center', va='center',
                fontsize=9, fontweight='bold', zorder=3)
        ax.text(x, y - 15, unit_id, ha='center', va='center',
                fontsize=8, color='#666666', zorder=3)
    
    def _draw_heat_exchanger(self, ax, position, name, unit_id):
        """绘制换热器"""
        x, y = position
        size = 60
        
        # 换热器主体（圆形）
        heat_ex = Circle((x, y), size/2,
                        facecolor='#ccccff', edgecolor='#0000cc',
                        linewidth=2, zorder=2)
        ax.add_patch(heat_ex)
        
        # 内部螺旋
        angles = np.linspace(0, 4 * np.pi, 100)
        spiral_x = x + (size/2 - 5) * np.cos(angles) * np.exp(-0.1 * angles)
        spiral_y = y + (size/2 - 5) * np.sin(angles) * np.exp(-0.1 * angles)
        ax.plot(spiral_x, spiral_y, color='#0000cc', linewidth=1.5, zorder=3)
        
        # 标签
        ax.text(x, y, name, ha='center', va='center',
                fontsize=8, fontweight='bold', zorder=4)
        ax.text(x, y - 12, unit_id, ha='center', va='center',
                fontsize=7, color='#666666', zorder=4)
    
    def _draw_pump(self, ax, position, name, unit_id):
        """绘制泵"""
        x, y = position
        width, height = 60, 40
        
        # 泵主体（圆形）
        pump = Circle((x, y), width/2,
                     facecolor='#ffffcc', edgecolor='#cc9900',
                     linewidth=2, zorder=2)
        ax.add_patch(pump)
        
        # 箭头
        ax.arrow(x, y - height/4, 0, height/2, 
                head_width=8, head_length=6, 
                fc='#cc9900', ec='#cc9900', zorder=3)
        
        # 标签
        ax.text(x, y, name, ha='center', va='center',
                fontsize=8, fontweight='bold', zorder=4)
        ax.text(x, y - 12, unit_id, ha='center', va='center',
                fontsize=7, color='#666666', zorder=4)
    
    def _draw_tank(self, ax, position, name, unit_id):
        """绘制储罐"""
        x, y = position
        width, height = 80, 100
        
        # 储罐主体（矩形加半圆顶）
        tank_bottom = Rectangle((x - width/2, y - height/2 + 20), 
                               width, height - 20,
                               facecolor='#e6e6ff', edgecolor='#6666cc',
                               linewidth=2, zorder=2)
        tank_top = mpatches.Arc((x, y - height/2 + 20), width, 40,
                               theta1=0, theta2=180,
                               edgecolor='#6666cc', linewidth=2, zorder=2)
        
        ax.add_patch(tank_bottom)
        ax.add_patch(tank_top)
        
        # 液位指示（假设50%液位）
        liquid_level = y - height/2 + 20 + (height - 20) * 0.5
        ax.plot([x - width/2 + 5, x + width/2 - 5], 
                [liquid_level, liquid_level],
                color='#0066cc', linewidth=3, zorder=3)
        
        # 标签
        ax.text(x, y + 10, name, ha='center', va='center',
                fontsize=9, fontweight='bold', zorder=4)
        ax.text(x, y - 10, unit_id, ha='center', va='center',
                fontsize=8, color='#666666', zorder=4)
    
    def _draw_default_unit(self, ax, position, name, unit_id):
        """绘制默认单元"""
        x, y = position
        width, height = 80, 60
        
        unit = Rectangle((x - width/2, y - height/2), width, height,
                        facecolor='#f0f0f0', edgecolor='#666666',
                        linewidth=2, zorder=2)
        ax.add_patch(unit)
        
        # 标签
        ax.text(x, y, name, ha='center', va='center',
                fontsize=9, fontweight='bold', zorder=3)
        ax.text(x, y - 15, unit_id, ha='center', va='center',
                fontsize=8, color='#666666', zorder=3)
    
    def _draw_connection(self, ax, points, stream_id):
        """绘制连接线"""
        if len(points) < 2:
            return
        
        # 绘制连接线
        xs, ys = zip(*points)
        ax.plot(xs, ys, color='#333333', linewidth=1.5, zorder=1)
        
        # 添加箭头
        if len(points) >= 2:
            x1, y1 = points[-2]
            x2, y2 = points[-1]
            dx, dy = x2 - x1, y2 - y1
            length = np.sqrt(dx*dx + dy*dy)
            if length > 0:
                ax.arrow(x1, y1, dx*0.9, dy*0.9,
                        head_width=5, head_length=8,
                        fc='#333333', ec='#333333', zorder=1)
        
        # 添加流股ID标签（在中间点）
        if len(points) >= 2:
            mid_idx = len(points) // 2
            x_mid, y_mid = points[mid_idx]
            ax.text(x_mid, y_mid + 5, stream_id,
                    ha='center', va='bottom',
                    fontsize=7, color='#0066cc',
                    bbox=dict(boxstyle="round,pad=0.2", 
                             facecolor='white', 
                             edgecolor='#cccccc', 
                             alpha=0.8),
                    zorder=5)
    
    def _add_legend(self, ax):
        """添加图例"""
        legend_elements = [
            mpatches.Patch(facecolor='#ffcccc', edgecolor='#cc0000', 
                          label='反应器'),
            mpatches.Patch(facecolor='#ccffcc', edgecolor='#006600', 
                          label='分离器'),
            mpatches.Patch(facecolor='#ccccff', edgecolor='#0000cc', 
                          label='换热器'),
            mpatches.Patch(facecolor='#ffffcc', edgecolor='#cc9900', 
                          label='泵'),
            mpatches.Patch(facecolor='#e6e6ff', edgecolor='#6666cc', 
                          label='储罐'),
            mpatches.Patch(facecolor='#f0f0f0', edgecolor='#666666', 
                          label='其他单元')
        ]
        
        ax.legend(handles=legend_elements, 
                 loc='upper left', 
                 bbox_to_anchor=(0.02, 0.98),
                 framealpha=0.9)
    
    def optimize_layout(self, algorithm: str = 'spring') -> Dict:
        """优化布局"""
        if not self.graph.nodes:
            return {}
        
        # 不同的布局算法
        if algorithm == 'spring':
            pos = nx.spring_layout(self.graph, k=2, iterations=50)
        elif algorithm == 'circular':
            pos = nx.circular_layout(self.graph)
        elif algorithm == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(self.graph)
        else:
            pos = nx.spring_layout(self.graph)
        
        # 更新单元位置
        for unit_id, position in pos.items():
            if unit_id in self.units:
                # 将坐标从[0,1]范围转换到[0,1000]范围
                scaled_x = position[0] * 800 + 100
                scaled_y = position[1] * 600 + 100
                self.units[unit_id].position = (scaled_x, scaled_y)
        
        # 更新连接点
        self._update_connection_points()
        
        return pos
    
    def _update_connection_points(self):
        """更新连接点坐标"""
        for conn in self.connections.values():
            from_unit = self.units.get(conn.from_unit)
            to_unit = self.units.get(conn.to_unit)
            
            if from_unit and to_unit:
                # 简化的连接路径：直接从起点到终点
                conn.points = [from_unit.position, to_unit.position]
    
    def validate_process_flow(self) -> Dict[str, List[str]]:
        """验证工艺流程图"""
        issues = {
            'unconnected_units': [],
            'units_without_input': [],
            'units_without_output': [],
            'duplicate_streams': [],
            'invalid_connections': []
        }
        
        # 检查未连接的单元
        for unit_id, unit in self.units.items():
            if not unit.streams_in and not unit.streams_out:
                issues['unconnected_units'].append(unit_id)
            
            if not unit.streams_in:
                issues['units_without_input'].append(unit_id)
            
            if not unit.streams_out:
                issues['units_without_output'].append(unit_id)
        
        # 检查重复的流股
        stream_ids = []
        for conn in self.connections.values():
            if conn.stream_id in stream_ids:
                issues['duplicate_streams'].append(conn.stream_id)
            else:
                stream_ids.append(conn.stream_id)
        
        # 检查无效连接
        for conn_id, conn in self.connections.items():
            if conn.from_unit not in self.units:
                issues['invalid_connections'].append(f"{conn_id}: 起点单元 {conn.from_unit} 不存在")
            if conn.to_unit not in self.units:
                issues['invalid_connections'].append(f"{conn_id}: 终点单元 {conn.to_unit} 不存在")
        
        return issues