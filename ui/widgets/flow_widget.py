#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程组件 - 统一接口
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox, QListWidget,
    QListWidgetItem, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal
from core.models import ProcessUnit

class FlowWidget(QWidget):
    """流程组件 - 统一接口"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.units = []
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QHBoxLayout(self)
        
        # 左侧：设备列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 设备列表
        list_group = QGroupBox("设备列表")
        list_layout = QVBoxLayout()
        
        self.unit_table = QTableWidget()
        self.unit_table.setColumnCount(5)
        self.unit_table.setHorizontalHeaderLabels(["设备ID", "名称", "类型", "X位置", "Y位置"])
        self.unit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.unit_table.itemSelectionChanged.connect(self.on_unit_selected)
        
        list_layout.addWidget(self.unit_table)
        
        # 设备操作按钮
        button_layout = QHBoxLayout()
        self.add_unit_btn = QPushButton("新增设备")
        self.add_unit_btn.clicked.connect(self.add_unit)
        self.delete_unit_btn = QPushButton("删除设备")
        self.delete_unit_btn.clicked.connect(self.delete_unit)
        
        button_layout.addWidget(self.add_unit_btn)
        button_layout.addWidget(self.delete_unit_btn)
        list_layout.addLayout(button_layout)
        
        list_group.setLayout(list_layout)
        left_layout.addWidget(list_group)
        
        # 右侧：设备详情
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        detail_group = QGroupBox("设备详情")
        detail_layout = QFormLayout()
        
        self.unit_id_input = QLineEdit()
        self.unit_id_input.setPlaceholderText("如: R-001")
        self.unit_name_input = QLineEdit()
        self.unit_name_input.setPlaceholderText("设备名称")
        
        self.unit_type_combo = QComboBox()
        self.unit_type_combo.addItems([
            "反应器", "分离器", "换热器", "泵", "压缩机",
            "储罐", "塔器", "干燥器", "过滤器", "混合器"
        ])
        
        self.unit_desc_input = QTextEdit()
        self.unit_desc_input.setMinimumHeight(60)
        self.unit_desc_input.setPlaceholderText("设备描述...")
        
        self.position_x_input = QDoubleSpinBox()
        self.position_x_input.setRange(0, 10000)
        self.position_x_input.setSuffix(" px")
        
        self.position_y_input = QDoubleSpinBox()
        self.position_y_input.setRange(0, 10000)
        self.position_y_input.setSuffix(" px")
        
        detail_layout.addRow("设备ID:", self.unit_id_input)
        detail_layout.addRow("设备名称:", self.unit_name_input)
        detail_layout.addRow("设备类型:", self.unit_type_combo)
        detail_layout.addRow("X位置:", self.position_x_input)
        detail_layout.addRow("Y位置:", self.position_y_input)
        detail_layout.addRow("描述:", self.unit_desc_input)
        
        detail_group.setLayout(detail_layout)
        right_layout.addWidget(detail_group)
        
        # 连接信息
        connection_group = QGroupBox("连接信息")
        connection_layout = QVBoxLayout()
        
        self.connections_input = QTextEdit()
        self.connections_input.setPlaceholderText("JSON格式的连接信息...")
        self.connections_input.setMinimumHeight(80)
        connection_layout.addWidget(self.connections_input)
        
        connection_group.setLayout(connection_layout)
        detail_layout.addRow(connection_group)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存设备")
        self.save_btn.clicked.connect(self.save_unit)
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_form)
        
        save_layout.addWidget(self.save_btn)
        save_layout.addWidget(self.reset_btn)
        save_layout.addStretch()
        
        right_layout.addLayout(save_layout)
        right_layout.addStretch()
        
        # 添加到主布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
    def set_units(self, units):
        """设置设备数据"""
        self.units = units
        self.update_table()
        
    def update_table(self):
        """更新表格"""
        self.unit_table.setRowCount(len(self.units))
        
        for i, unit in enumerate(self.units):
            if hasattr(unit, 'unit_id'):
                self.unit_table.setItem(i, 0, QTableWidgetItem(unit.unit_id))
                self.unit_table.setItem(i, 1, QTableWidgetItem(unit.name))
                self.unit_table.setItem(i, 2, QTableWidgetItem(unit.type))
                self.unit_table.setItem(i, 3, QTableWidgetItem(str(unit.position_x or 0)))
                self.unit_table.setItem(i, 4, QTableWidgetItem(str(unit.position_y or 0)))
                
    def on_unit_selected(self):
        """设备选择变化"""
        selected_items = self.unit_table.selectedItems()
        if not selected_items:
            return
            
        row = self.unit_table.currentRow()
        unit_id = self.unit_table.item(row, 0).text()
        
        # 查找设备
        unit = None
        for u in self.units:
            if hasattr(u, 'unit_id') and u.unit_id == unit_id:
                unit = u
                break
                
        if unit:
            self.load_unit(unit)
            
    def load_unit(self, unit):
        """加载设备到表单"""
        self.unit_id_input.setText(unit.unit_id)
        self.unit_name_input.setText(unit.name)
        
        # 设置设备类型
        index = self.unit_type_combo.findText(unit.type)
        if index >= 0:
            self.unit_type_combo.setCurrentIndex(index)
            
        self.position_x_input.setValue(unit.position_x or 0)
        self.position_y_input.setValue(unit.position_y or 0)
        self.unit_desc_input.setText(unit.description or "")
        
    def add_unit(self):
        """添加新设备"""
        self.reset_form()
        import random
        new_id = f"U-{random.randint(100, 999)}"
        self.unit_id_input.setText(new_id)
        self.unit_name_input.setFocus()
        
    def delete_unit(self):
        """删除设备"""
        selected_items = self.unit_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个设备")
            return
            
        row = self.unit_table.currentRow()
        unit_id = self.unit_table.item(row, 0).text()
        unit_name = self.unit_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除设备 '{unit_name}' ({unit_id}) 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_changed.emit()
            
    def save_unit(self):
        """保存设备"""
        unit_id = self.unit_id_input.text().strip()
        if not unit_id:
            QMessageBox.warning(self, "警告", "设备ID不能为空")
            return
            
        # 创建设备对象
        unit = ProcessUnit(
            unit_id=unit_id,
            name=self.unit_name_input.text().strip(),
            type=self.unit_type_combo.currentText(),
            description=self.unit_desc_input.toPlainText().strip(),
            position_x=self.position_x_input.value(),
            position_y=self.position_y_input.value()
        )
        
        self.data_changed.emit()
        QMessageBox.information(self, "成功", f"设备 {unit_id} 已保存")
        
    def reset_form(self):
        """重置表单"""
        self.unit_id_input.clear()
        self.unit_name_input.clear()
        self.unit_type_combo.setCurrentIndex(0)
        self.position_x_input.setValue(0)
        self.position_y_input.setValue(0)
        self.unit_desc_input.clear()
        self.connections_input.clear()