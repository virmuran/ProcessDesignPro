#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料参数组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from core.models import MaterialParameter

class MaterialWidget(QWidget):
    """物料参数管理组件"""
    
    # 信号定义
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.materials = []
        self.current_material_id = None
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QHBoxLayout(self)
        
        # 左侧：物料列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 搜索框
        search_group = QGroupBox("搜索")
        search_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入物料名称或ID搜索...")
        self.search_input.textChanged.connect(self.filter_materials)
        search_layout.addWidget(self.search_input)
        search_group.setLayout(search_layout)
        left_layout.addWidget(search_group)
        
        # 物料列表
        list_group = QGroupBox("物料列表")
        list_layout = QVBoxLayout()
        
        self.material_table = QTableWidget()
        self.material_table.setColumnCount(6)
        self.material_table.setHorizontalHeaderLabels([
            "ID", "名称", "化学式", "分子量", "密度", "安全等级"
        ])
        self.material_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.material_table.itemSelectionChanged.connect(self.on_material_selected)
        
        list_layout.addWidget(self.material_table)
        list_group.setLayout(list_layout)
        left_layout.addWidget(list_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("新增")
        self.add_btn.clicked.connect(self.add_material)
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_material)
        self.import_btn = QPushButton("导入")
        self.export_btn = QPushButton("导出")
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
        left_layout.addLayout(button_layout)
        
        # 右侧：物料详情
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        detail_group = QGroupBox("物料详情")
        detail_layout = QFormLayout()
        
        # 基本属性
        self.material_id_input = QLineEdit()
        self.material_id_input.setPlaceholderText("如: MAT-001")
        self.material_name_input = QLineEdit()
        self.material_name_input.setPlaceholderText("物料名称")
        self.chemical_formula_input = QLineEdit()
        self.chemical_formula_input.setPlaceholderText("如: H2O")
        
        detail_layout.addRow("物料ID:", self.material_id_input)
        detail_layout.addRow("物料名称:", self.material_name_input)
        detail_layout.addRow("化学式:", self.chemical_formula_input)
        
        # 物性参数
        self.molar_mass_input = QDoubleSpinBox()
        self.molar_mass_input.setRange(0, 10000)
        self.molar_mass_input.setSuffix(" g/mol")
        self.molar_mass_input.setDecimals(3)
        
        self.density_input = QDoubleSpinBox()
        self.density_input.setRange(0, 10000)
        self.density_input.setSuffix(" kg/m³")
        self.density_input.setDecimals(2)
        
        self.viscosity_input = QDoubleSpinBox()
        self.viscosity_input.setRange(0, 1000)
        self.viscosity_input.setSuffix(" Pa·s")
        self.viscosity_input.setDecimals(6)
        self.viscosity_input.setSpecialValueText("0 (默认)")
        
        self.specific_heat_input = QDoubleSpinBox()
        self.specific_heat_input.setRange(0, 10000)
        self.specific_heat_input.setSuffix(" J/(kg·K)")
        self.specific_heat_input.setDecimals(2)
        
        self.thermal_conductivity_input = QDoubleSpinBox()
        self.thermal_conductivity_input.setRange(0, 1000)
        self.thermal_conductivity_input.setSuffix(" W/(m·K)")
        self.thermal_conductivity_input.setDecimals(3)
        
        detail_layout.addRow("分子量:", self.molar_mass_input)
        detail_layout.addRow("密度:", self.density_input)
        detail_layout.addRow("粘度:", self.viscosity_input)
        detail_layout.addRow("比热:", self.specific_heat_input)
        detail_layout.addRow("热导率:", self.thermal_conductivity_input)
        
        # 安全信息
        self.safety_class_combo = QComboBox()
        self.safety_class_combo.addItems([
            "非危险品", "易燃液体", "腐蚀品", "毒性物质", 
            "氧化剂", "爆炸品", "放射性物质", "其他"
        ])
        
        self.storage_input = QLineEdit()
        self.storage_input.setPlaceholderText("如: 阴凉通风处")
        
        detail_layout.addRow("安全等级:", self.safety_class_combo)
        detail_layout.addRow("储存条件:", self.storage_input)
        
        # 其他属性
        properties_group = QGroupBox("其他属性")
        properties_layout = QVBoxLayout()
        self.properties_input = QTextEdit()
        self.properties_input.setPlaceholderText("JSON格式的其他属性...")
        self.properties_input.setMinimumHeight(80)
        properties_layout.addWidget(self.properties_input)
        properties_group.setLayout(properties_layout)
        
        detail_layout.addRow(properties_group)
        
        detail_group.setLayout(detail_layout)
        right_layout.addWidget(detail_group)
        
        # 保存按钮
        button_group = QGroupBox()
        button_group_layout = QHBoxLayout(button_group)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_material)
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_form)
        
        self.calculate_btn = QPushButton("计算性质")
        self.calculate_btn.clicked.connect(self.calculate_properties)
        
        button_group_layout.addWidget(self.save_btn)
        button_group_layout.addWidget(self.reset_btn)
        button_group_layout.addWidget(self.calculate_btn)
        
        right_layout.addWidget(button_group)
        right_layout.addStretch()
        
        # 添加到主布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
    def set_materials(self, materials):
        """设置物料数据"""
        self.materials = materials
        self.update_table()
        
    def update_table(self):
        """更新表格数据"""
        self.material_table.setRowCount(len(self.materials))
        
        for i, material in enumerate(self.materials):
            if hasattr(material, 'material_id'):
                self.material_table.setItem(i, 0, QTableWidgetItem(material.material_id))
                self.material_table.setItem(i, 1, QTableWidgetItem(material.name))
                self.material_table.setItem(i, 2, QTableWidgetItem(material.chemical_formula or ""))
                self.material_table.setItem(i, 3, QTableWidgetItem(str(material.molar_mass or "")))
                self.material_table.setItem(i, 4, QTableWidgetItem(str(material.density or "")))
                self.material_table.setItem(i, 5, QTableWidgetItem(material.safety_class or ""))
                
    def on_material_selected(self):
        """物料选择变化"""
        selected_items = self.material_table.selectedItems()
        if not selected_items:
            return
            
        row = self.material_table.currentRow()
        material_id = self.material_table.item(row, 0).text()
        
        # 查找物料
        material = None
        for mat in self.materials:
            if hasattr(mat, 'material_id') and mat.material_id == material_id:
                material = mat
                break
                
        if material:
            self.load_material(material)
            
    def load_material(self, material):
        """加载物料到表单"""
        self.current_material_id = material.material_id
        
        self.material_id_input.setText(material.material_id)
        self.material_name_input.setText(material.name)
        self.chemical_formula_input.setText(material.chemical_formula or "")
        
        self.molar_mass_input.setValue(material.molar_mass or 0)
        self.density_input.setValue(material.density or 0)
        self.viscosity_input.setValue(material.viscosity or 0)
        self.specific_heat_input.setValue(material.specific_heat or 0)
        self.thermal_conductivity_input.setValue(material.thermal_conductivity or 0)
        
        # 设置安全等级
        index = self.safety_class_combo.findText(material.safety_class or "非危险品")
        if index >= 0:
            self.safety_class_combo.setCurrentIndex(index)
            
        self.storage_input.setText(material.storage_conditions or "")
        
    def add_material(self):
        """添加新物料"""
        self.reset_form()
        # 生成新的物料ID
        import random
        new_id = f"MAT-{random.randint(1000, 9999)}"
        self.material_id_input.setText(new_id)
        self.material_name_input.setFocus()
        
    def delete_material(self):
        """删除物料"""
        selected_items = self.material_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个物料")
            return
            
        row = self.material_table.currentRow()
        material_id = self.material_table.item(row, 0).text()
        material_name = self.material_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除物料 '{material_name}' ({material_id}) 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 发送删除信号
            self.data_changed.emit()
            
    def save_material(self):
        """保存物料"""
        material_id = self.material_id_input.text().strip()
        if not material_id:
            QMessageBox.warning(self, "警告", "物料ID不能为空")
            return
            
        # 创建物料对象
        material = MaterialParameter(
            material_id=material_id,
            name=self.material_name_input.text().strip(),
            chemical_formula=self.chemical_formula_input.text().strip(),
            molar_mass=self.molar_mass_input.value(),
            density=self.density_input.value(),
            viscosity=self.viscosity_input.value(),
            specific_heat=self.specific_heat_input.value(),
            thermal_conductivity=self.thermal_conductivity_input.value(),
            safety_class=self.safety_class_combo.currentText(),
            storage_conditions=self.storage_input.text().strip()
        )
        
        # 发送保存信号
        self.data_changed.emit()
        
    def reset_form(self):
        """重置表单"""
        self.current_material_id = None
        self.material_id_input.clear()
        self.material_name_input.clear()
        self.chemical_formula_input.clear()
        self.molar_mass_input.setValue(0)
        self.density_input.setValue(0)
        self.viscosity_input.setValue(0)
        self.specific_heat_input.setValue(0)
        self.thermal_conductivity_input.setValue(0)
        self.safety_class_combo.setCurrentIndex(0)
        self.storage_input.clear()
        self.properties_input.clear()
        
    def filter_materials(self):
        """过滤物料"""
        search_text = self.search_input.text().lower()
        
        for i in range(self.material_table.rowCount()):
            match = False
            for j in range(self.material_table.columnCount()):
                item = self.material_table.item(i, j)
                if item and search_text in item.text().lower():
                    match = True
                    break
                    
            self.material_table.setRowHidden(i, not match)
            
    def calculate_properties(self):
        """计算物料性质"""
        # 这里可以实现一些计算逻辑
        formula = self.chemical_formula_input.text().strip()
        if formula:
            # 简单的分子量计算示例（实际需要更复杂的解析）
            QMessageBox.information(self, "提示", "分子量计算功能待实现")
        else:
            QMessageBox.warning(self, "警告", "请输入化学式进行计算")
            
    def get_current_material(self):
        """获取当前表单中的物料数据"""
        if not self.material_id_input.text().strip():
            return None
            
        return MaterialParameter(
            material_id=self.material_id_input.text().strip(),
            name=self.material_name_input.text().strip(),
            chemical_formula=self.chemical_formula_input.text().strip(),
            molar_mass=self.molar_mass_input.value(),
            density=self.density_input.value(),
            viscosity=self.viscosity_input.value(),
            specific_heat=self.specific_heat_input.value(),
            thermal_conductivity=self.thermal_conductivity_input.value(),
            safety_class=self.safety_class_combo.currentText(),
            storage_conditions=self.storage_input.text().strip()
        )