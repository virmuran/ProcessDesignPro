#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工艺路线方块图组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsEllipseItem, QMenu,
    QDockWidget, QListWidget, QListWidgetItem, QToolBar,
    QToolButton, QStyle, QColorDialog, QInputDialog
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QAction

class ProcessFlowWidget(QWidget):
    """工艺路线方块图组件"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.units = []
        self.connections = []
        self._create_ui()
        self._setup_graphics()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # 添加工具按钮
        self.add_reactor_action = QAction("反应器", self)
        toolbar.addAction(self.add_reactor_action)
        
        self.add_separator_action = QAction("分离器", self)
        toolbar.addAction(self.add_separator_action)
        
        self.add_heatex_action = QAction("换热器", self)
        toolbar.addAction(self.add_heatex_action)
        
        self.add_pump_action = QAction("泵", self)
        toolbar.addAction(self.add_pump_action)
        
        self.add_tank_action = QAction("储罐", self)
        toolbar.addAction(self.add_tank_action)
        
        toolbar.addSeparator()
        
        self.select_action = QAction("选择", self)
        toolbar.addAction(self.select_action)
        
        self.connect_action = QAction("连接", self)
        toolbar.addAction(self.connect_action)
        
        self.delete_action = QAction("删除", self)
        toolbar.addAction(self.delete_action)
        
        toolbar.addSeparator()
        
        self.zoom_in_action = QAction("放大", self)
        toolbar.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction("缩小", self)
        toolbar.addAction(self.zoom_out_action)
        
        self.fit_view_action = QAction("适应视图", self)
        toolbar.addAction(self.fit_view_action)
        
        main_layout.addWidget(toolbar)
        
        # 主工作区
        workspace = QSplitter(Qt.Horizontal)
        
        # 左侧：设备库
        left_panel = QDockWidget("设备库")
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.unit_list = QListWidget()
        unit_types = [
            "反应器", "分离器", "换热器", "泵", "压缩机",
            "储罐", "塔器", "干燥器", "过滤器", "混合器"
        ]
        for unit_type in unit_types:
            self.unit_list.addItem(unit_type)
            
        left_layout.addWidget(self.unit_list)
        
        # 设备属性
        property_group = QGroupBox("设备属性")
        property_layout = QFormLayout()
        
        self.unit_id_input = QLineEdit()
        self.unit_name_input = QLineEdit()
        self.unit_type_input = QComboBox()
        self.unit_type_input.addItems(unit_types)
        self.unit_desc_input = QTextEdit()
        self.unit_desc_input.setMaximumHeight(60)
        
        property_layout.addRow("设备ID:", self.unit_id_input)
        property_layout.addRow("设备名称:", self.unit_name_input)
        property_layout.addRow("设备类型:", self.unit_type_input)
        property_layout.addRow("描述:", self.unit_desc_input)
        
        property_group.setLayout(property_layout)
        left_layout.addWidget(property_group)
        
        left_panel.setWidget(left_widget)
        
        # 中间：图形编辑器
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 图形视图
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        
        center_layout.addWidget(self.graphics_view)
        
        # 右侧：连接和属性
        right_panel = QDockWidget("连接和属性")
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 连接列表
        connection_group = QGroupBox("连接列表")
        connection_layout = QVBoxLayout()
        
        self.connection_table = QTableWidget()
        self.connection_table.setColumnCount(3)
        self.connection_table.setHorizontalHeaderLabels(["源设备", "目标设备", "物料流"])
        connection_layout.addWidget(self.connection_table)
        
        connection_group.setLayout(connection_layout)
        right_layout.addWidget(connection_group)
        
        # 流股属性
        stream_group = QGroupBox("流股属性")
        stream_layout = QFormLayout()
        
        self.stream_from_input = QLineEdit()
        self.stream_to_input = QLineEdit()
        self.stream_material_input = QComboBox()
        
        stream_layout.addRow("从:", self.stream_from_input)
        stream_layout.addRow("到:", self.stream_to_input)
        stream_layout.addRow("物料:", self.stream_material_input)
        
        stream_group.setLayout(stream_layout)
        right_layout.addWidget(stream_group)
        
        right_panel.setWidget(right_widget)
        
        # 添加面板到工作区
        workspace.addWidget(left_panel)
        workspace.addWidget(center_panel)
        workspace.addWidget(right_panel)
        
        main_layout.addWidget(workspace)
        
        # 连接信号
        self._connect_signals()
        
    def _setup_graphics(self):
        """设置图形场景"""
        # 设置场景背景
        self.graphics_scene.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # 创建示例设备
        self._create_example_units()
        
    def _create_example_units(self):
        """创建示例设备（用于演示）"""
        # 创建一些示例设备
        units_data = [
            {"id": "R-001", "name": "反应器", "type": "reactor", "x": 100, "y": 100},
            {"id": "S-001", "name": "分离器", "type": "separator", "x": 300, "y": 100},
            {"id": "H-001", "name": "换热器", "type": "heatex", "x": 500, "y": 100},
            {"id": "T-001", "name": "储罐", "type": "tank", "x": 200, "y": 300},
            {"id": "P-001", "name": "泵", "type": "pump", "x": 400, "y": 300}
        ]
        
        for unit_data in units_data:
            self._create_unit_graphics(unit_data)
            
    def _create_unit_graphics(self, unit_data):
        """创建设备图形"""
        # 根据设备类型选择颜色
        colors = {
            "reactor": QColor(255, 200, 200),
            "separator": QColor(200, 255, 200),
            "heatex": QColor(200, 200, 255),
            "pump": QColor(255, 255, 200),
            "tank": QColor(255, 200, 255)
        }
        
        color = colors.get(unit_data["type"], QColor(200, 200, 200))
        
        # 创建设备矩形
        rect = QGraphicsRectItem(0, 0, 80, 60)
        rect.setPos(unit_data["x"], unit_data["y"])
        rect.setBrush(QBrush(color))
        rect.setPen(QPen(Qt.black, 2))
        
        # 添加设备ID文本
        text = QGraphicsTextItem(unit_data["id"])
        text.setPos(unit_data["x"] + 10, unit_data["y"] + 20)
        
        # 添加设备名称文本
        name_text = QGraphicsTextItem(unit_data["name"])
        name_text.setPos(unit_data["x"] + 10, unit_data["y"] + 40)
        name_text.setFont(QFont("Arial", 8))
        
        # 添加到场景
        self.graphics_scene.addItem(rect)
        self.graphics_scene.addItem(text)
        self.graphics_scene.addItem(name_text)
        
    def _connect_signals(self):
        """连接信号"""
        self.unit_list.itemDoubleClicked.connect(self.add_unit_from_list)
        
    def add_unit_from_list(self, item):
        """从列表添加设备"""
        unit_type = item.text()
        
        # 生成设备ID
        import random
        unit_id = self._generate_unit_id(unit_type)
        
        # 在图形场景中添加设备
        unit_data = {
            "id": unit_id,
            "name": unit_type,
            "type": unit_type.lower(),
            "x": 100 + random.randint(0, 500),
            "y": 100 + random.randint(0, 300)
        }
        
        self._create_unit_graphics(unit_data)
        
    def _generate_unit_id(self, unit_type):
        """生成设备ID"""
        type_prefix = {
            "反应器": "R",
            "分离器": "S",
            "换热器": "H",
            "泵": "P",
            "储罐": "T",
            "塔器": "C",
            "压缩机": "K"
        }
        
        prefix = type_prefix.get(unit_type, "U")
        import random
        return f"{prefix}-{random.randint(100, 999)}"
        
    def set_units(self, units):
        """设置设备数据"""
        self.units = units
        self.update_graphics()
        
    def update_graphics(self):
        """更新图形显示"""
        # 清除场景
        self.graphics_scene.clear()
        
        # 重新绘制所有设备
        for unit in self.units:
            if hasattr(unit, 'unit_id'):
                unit_data = {
                    "id": unit.unit_id,
                    "name": unit.name,
                    "type": unit.type,
                    "x": unit.position_x or 0,
                    "y": unit.position_y or 0
                }
                self._create_unit_graphics(unit_data)