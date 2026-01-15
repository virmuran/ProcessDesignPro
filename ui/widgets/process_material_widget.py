#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过程物料组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from core.models import ProcessMaterial

class ProcessMaterialWidget(QWidget):
    """过程物料管理组件"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.streams = []
        self.materials = []  # 物料参数列表
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 流股列表标签页
        streams_tab = QWidget()
        streams_layout = QVBoxLayout(streams_tab)
        
        # 流股表格
        self.streams_table = QTableWidget()
        self.streams_table.setColumnCount(8)
        self.streams_table.setHorizontalHeaderLabels([
            "流股ID", "名称", "相态", "温度(°C)", "压力(bar)", 
            "流量(kg/h)", "来源", "去向"
        ])
        self.streams_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.streams_table.itemSelectionChanged.connect(self.on_stream_selected)
        
        streams_layout.addWidget(self.streams_table)
        
        # 流股操作按钮
        stream_buttons = QHBoxLayout()
        self.add_stream_btn = QPushButton("新增流股")
        self.add_stream_btn.clicked.connect(self.add_stream)
        self.delete_stream_btn = QPushButton("删除流股")
        self.duplicate_stream_btn = QPushButton("复制流股")
        self.calculate_stream_btn = QPushButton("计算性质")
        
        stream_buttons.addWidget(self.add_stream_btn)
        stream_buttons.addWidget(self.delete_stream_btn)
        stream_buttons.addWidget(self.duplicate_stream_btn)
        stream_buttons.addWidget(self.calculate_stream_btn)
        stream_buttons.addStretch()
        
        streams_layout.addLayout(stream_buttons)
        
        tab_widget.addTab(streams_tab, "流股列表")
        
        # 流股详情标签页
        detail_tab = QWidget()
        detail_layout = QVBoxLayout(detail_tab)
        
        # 基本参数
        basic_group = QGroupBox("基本参数")
        basic_layout = QFormLayout()
        
        self.stream_id_input = QLineEdit()
        self.stream_name_input = QLineEdit()
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(["液体", "气体", "固体", "气液混合", "液固混合"])
        
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(-273, 1000)
        self.temperature_input.setSuffix(" °C")
        self.temperature_input.setValue(25)
        
        self.pressure_input = QDoubleSpinBox()
        self.pressure_input.setRange(0, 1000)
        self.pressure_input.setSuffix(" bar")
        self.pressure_input.setValue(1)
        
        self.flow_rate_input = QDoubleSpinBox()
        self.flow_rate_input.setRange(0, 1000000)
        self.flow_rate_input.setSuffix(" kg/h")
        self.flow_rate_input.setValue(1000)
        
        basic_layout.addRow("流股ID:", self.stream_id_input)
        basic_layout.addRow("流股名称:", self.stream_name_input)
        basic_layout.addRow("相态:", self.phase_combo)
        basic_layout.addRow("温度:", self.temperature_input)
        basic_layout.addRow("压力:", self.pressure_input)
        basic_layout.addRow("流量:", self.flow_rate_input)
        
        basic_group.setLayout(basic_layout)
        detail_layout.addWidget(basic_group)
        
        # 组成和连接
        middle_layout = QHBoxLayout()
        
        # 组成
        composition_group = QGroupBox("物料组成")
        composition_layout = QVBoxLayout()
        
        self.composition_table = QTableWidget()
        self.composition_table.setColumnCount(3)
        self.composition_table.setHorizontalHeaderLabels(["物料", "质量分数", "摩尔分数"])
        composition_layout.addWidget(self.composition_table)
        
        composition_buttons = QHBoxLayout()
        self.add_component_btn = QPushButton("添加组分")
        self.remove_component_btn = QPushButton("移除组分")
        composition_buttons.addWidget(self.add_component_btn)
        composition_buttons.addWidget(self.remove_component_btn)
        composition_layout.addLayout(composition_buttons)
        
        composition_group.setLayout(composition_layout)
        middle_layout.addWidget(composition_group)
        
        # 连接信息
        connection_group = QGroupBox("连接信息")
        connection_layout = QFormLayout()
        
        self.source_unit_input = QLineEdit()
        self.source_unit_input.setPlaceholderText("如: R-001")
        self.destination_unit_input = QLineEdit()
        self.destination_unit_input.setPlaceholderText("如: C-001")
        
        connection_layout.addRow("来源设备:", self.source_unit_input)
        connection_layout.addRow("去向设备:", self.destination_unit_input)
        
        connection_group.setLayout(connection_layout)
        middle_layout.addWidget(connection_group)
        
        detail_layout.addLayout(middle_layout)
        
        # 物理性质
        properties_group = QGroupBox("物理性质")
        properties_layout = QFormLayout()
        
        self.density_calc = QLabel("密度: -- kg/m³")
        self.viscosity_calc = QLabel("粘度: -- Pa·s")
        self.specific_heat_calc = QLabel("比热: -- J/(kg·K)")
        self.enthalpy_calc = QLabel("焓值: -- kJ/kg")
        
        properties_layout.addRow(self.density_calc)
        properties_layout.addRow(self.viscosity_calc)
        properties_layout.addRow(self.specific_heat_calc)
        properties_layout.addRow(self.enthalpy_calc)
        
        properties_group.setLayout(properties_layout)
        detail_layout.addWidget(properties_group)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_stream_btn = QPushButton("保存流股")
        self.save_stream_btn.clicked.connect(self.save_stream)
        self.save_stream_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.calculate_all_btn = QPushButton("计算所有性质")
        self.reset_stream_btn = QPushButton("重置")
        
        save_layout.addWidget(self.save_stream_btn)
        save_layout.addWidget(self.calculate_all_btn)
        save_layout.addWidget(self.reset_stream_btn)
        save_layout.addStretch()
        
        detail_layout.addLayout(save_layout)
        
        tab_widget.addTab(detail_tab, "流股详情")
        
        # 物料平衡标签页
        balance_tab = QWidget()
        balance_layout = QVBoxLayout(balance_tab)
        
        balance_info = QLabel("物料平衡信息将在这里显示")
        balance_info.setAlignment(Qt.AlignCenter)
        balance_info.setStyleSheet("font-size: 16px; color: #666;")
        balance_layout.addWidget(balance_info)
        
        tab_widget.addTab(balance_tab, "物料平衡")
        
        main_layout.addWidget(tab_widget)
        
    def set_streams(self, streams):
        """设置流股数据"""
        self.streams = streams
        self.update_table()
        
    def set_materials(self, materials):
        """设置物料参数"""
        self.materials = materials
        
    def update_table(self):
        """更新表格"""
        self.streams_table.setRowCount(len(self.streams))
        
        for i, stream in enumerate(self.streams):
            if hasattr(stream, 'stream_id'):
                self.streams_table.setItem(i, 0, QTableWidgetItem(stream.stream_id))
                self.streams_table.setItem(i, 1, QTableWidgetItem(stream.name))
                self.streams_table.setItem(i, 2, QTableWidgetItem(stream.phase))
                self.streams_table.setItem(i, 3, QTableWidgetItem(str(stream.temperature or "")))
                self.streams_table.setItem(i, 4, QTableWidgetItem(str(stream.pressure or "")))
                self.streams_table.setItem(i, 5, QTableWidgetItem(str(stream.flow_rate or "")))
                self.streams_table.setItem(i, 6, QTableWidgetItem(stream.source_unit or ""))
                self.streams_table.setItem(i, 7, QTableWidgetItem(stream.destination_unit or ""))
                
    def on_stream_selected(self):
        """流股选择变化"""
        selected_items = self.streams_table.selectedItems()
        if not selected_items:
            return
            
        row = self.streams_table.currentRow()
        stream_id = self.streams_table.item(row, 0).text()
        
        # 查找流股
        stream = None
        for s in self.streams:
            if hasattr(s, 'stream_id') and s.stream_id == stream_id:
                stream = s
                break
                
        if stream:
            self.load_stream(stream)
            
    def load_stream(self, stream):
        """加载流股到表单"""
        self.stream_id_input.setText(stream.stream_id)
        self.stream_name_input.setText(stream.name)
        
        # 设置相态
        index = self.phase_combo.findText(stream.phase)
        if index >= 0:
            self.phase_combo.setCurrentIndex(index)
            
        self.temperature_input.setValue(stream.temperature or 25)
        self.pressure_input.setValue(stream.pressure or 1)
        self.flow_rate_input.setValue(stream.flow_rate or 1000)
        
        self.source_unit_input.setText(stream.source_unit or "")
        self.destination_unit_input.setText(stream.destination_unit or "")
        
        # 加载组成
        self.update_composition_table(stream.composition if hasattr(stream, 'composition') else {})
        
    def update_composition_table(self, composition):
        """更新组成表格"""
        self.composition_table.setRowCount(len(composition))
        
        row = 0
        for material_id, mass_fraction in composition.items():
            # 查找物料名称
            material_name = material_id
            for mat in self.materials:
                if hasattr(mat, 'material_id') and mat.material_id == material_id:
                    material_name = mat.name
                    break
                    
            self.composition_table.setItem(row, 0, QTableWidgetItem(material_name))
            self.composition_table.setItem(row, 1, QTableWidgetItem(f"{mass_fraction:.4f}"))
            # 计算摩尔分数（需要分子量）
            self.composition_table.setItem(row, 2, QTableWidgetItem("--"))
            row += 1
            
    def add_stream(self):
        """添加新流股"""
        import random
        new_id = f"STR-{random.randint(1000, 9999)}"
        self.stream_id_input.setText(new_id)
        self.stream_name_input.clear()
        self.stream_name_input.setFocus()
        
    def save_stream(self):
        """保存流股"""
        stream_id = self.stream_id_input.text().strip()
        if not stream_id:
            QMessageBox.warning(self, "警告", "流股ID不能为空")
            return
            
        # 获取组成数据
        composition = {}
        for i in range(self.composition_table.rowCount()):
            material_item = self.composition_table.item(i, 0)
            fraction_item = self.composition_table.item(i, 1)
            
            if material_item and fraction_item:
                try:
                    material_name = material_item.text()
                    fraction = float(fraction_item.text())
                    
                    # 查找物料ID
                    material_id = material_name
                    for mat in self.materials:
                        if hasattr(mat, 'name') and mat.name == material_name:
                            material_id = mat.material_id
                            break
                            
                    composition[material_id] = fraction
                except:
                    continue
                    
        # 创建流股对象
        stream = ProcessMaterial(
            stream_id=stream_id,
            name=self.stream_name_input.text().strip(),
            phase=self.phase_combo.currentText(),
            temperature=self.temperature_input.value(),
            pressure=self.pressure_input.value(),
            flow_rate=self.flow_rate_input.value(),
            composition=composition,
            source_unit=self.source_unit_input.text().strip(),
            destination_unit=self.destination_unit_input.text().strip()
        )
        
        # 发送数据变更信号
        self.data_changed.emit()
        QMessageBox.information(self, "成功", f"流股 {stream_id} 已保存")
        
    def calculate_properties(self):
        """计算流股性质"""
        # 这里可以实现物性计算逻辑
        QMessageBox.information(self, "提示", "物性计算功能待实现")