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
        self.material_table.setColumnCount(7)  # 增加一列用于CAS号
        self.material_table.setHorizontalHeaderLabels([
            "ID", "名称", "化学式", "CAS号", "分子量", "密度", "安全等级"
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
        
        # ========== 基本属性部分 ==========
        basic_group = QGroupBox("基本属性")
        basic_layout = QFormLayout()
        
        self.material_id_input = QLineEdit()
        self.material_id_input.setPlaceholderText("如: MAT-001")
        
        self.material_name_input = QLineEdit()
        self.material_name_input.setPlaceholderText("物料名称")
        
        self.chemical_formula_input = QLineEdit()
        self.chemical_formula_input.setPlaceholderText("如: H2O")
        
        self.cas_input = QLineEdit()
        self.cas_input.setPlaceholderText("如: 7664-93-9")
        
        basic_layout.addRow("物料ID:", self.material_id_input)
        basic_layout.addRow("物料名称:", self.material_name_input)
        basic_layout.addRow("化学式:", self.chemical_formula_input)
        basic_layout.addRow("CAS号:", self.cas_input)
        
        basic_group.setLayout(basic_layout)
        detail_layout.addRow(basic_group)
        
        # ========== 物性参数部分 ==========
        physical_group = QGroupBox("物性参数")
        physical_layout = QFormLayout()
        
        self.molar_mass_input = QDoubleSpinBox()
        self.molar_mass_input.setRange(0, 10000)
        self.molar_mass_input.setSuffix(" g/mol")
        self.molar_mass_input.setDecimals(3)
        self.molar_mass_input.setSpecialValueText("未设置")
        
        self.density_input = QDoubleSpinBox()
        self.density_input.setRange(0, 10000)
        self.density_input.setSuffix(" kg/m³")
        self.density_input.setDecimals(2)
        self.density_input.setSpecialValueText("未设置")
        
        self.viscosity_input = QDoubleSpinBox()
        self.viscosity_input.setRange(0, 1000)
        self.viscosity_input.setSuffix(" Pa·s")
        self.viscosity_input.setDecimals(6)
        self.viscosity_input.setSpecialValueText("未设置")
        
        self.specific_heat_input = QDoubleSpinBox()
        self.specific_heat_input.setRange(0, 10000)
        self.specific_heat_input.setSuffix(" J/(kg·K)")
        self.specific_heat_input.setDecimals(2)
        self.specific_heat_input.setSpecialValueText("未设置")
        
        self.thermal_conductivity_input = QDoubleSpinBox()
        self.thermal_conductivity_input.setRange(0, 1000)
        self.thermal_conductivity_input.setSuffix(" W/(m·K)")
        self.thermal_conductivity_input.setDecimals(3)
        self.thermal_conductivity_input.setSpecialValueText("未设置")
        
        physical_layout.addRow("分子量:", self.molar_mass_input)
        physical_layout.addRow("密度:", self.density_input)
        physical_layout.addRow("粘度:", self.viscosity_input)
        physical_layout.addRow("比热:", self.specific_heat_input)
        physical_layout.addRow("热导率:", self.thermal_conductivity_input)
        
        physical_group.setLayout(physical_layout)
        detail_layout.addRow(physical_group)
        
        # ========== 质量指标部分（基于硫酸标准GB 29205-2012） ==========
        quality_group = QGroupBox("质量指标")
        quality_layout = QFormLayout()
        
        self.sulfuric_acid_92_input = QDoubleSpinBox()
        self.sulfuric_acid_92_input.setRange(0, 100)
        self.sulfuric_acid_92_input.setSuffix(" %")
        self.sulfuric_acid_92_input.setDecimals(1)
        self.sulfuric_acid_92_input.setSpecialValueText("未设置")
        
        self.sulfuric_acid_98_input = QDoubleSpinBox()
        self.sulfuric_acid_98_input.setRange(0, 100)
        self.sulfuric_acid_98_input.setSuffix(" %")
        self.sulfuric_acid_98_input.setDecimals(1)
        self.sulfuric_acid_98_input.setSpecialValueText("未设置")
        
        self.nitrate_input = QDoubleSpinBox()
        self.nitrate_input.setRange(0, 1)
        self.nitrate_input.setSuffix(" %")
        self.nitrate_input.setDecimals(3)
        self.nitrate_input.setSpecialValueText("未设置")
        
        self.chloride_input = QDoubleSpinBox()
        self.chloride_input.setRange(0, 0.1)
        self.chloride_input.setSuffix(" %")
        self.chloride_input.setDecimals(3)
        self.chloride_input.setSpecialValueText("未设置")
        
        self.iron_input = QDoubleSpinBox()
        self.iron_input.setRange(0, 0.1)
        self.iron_input.setSuffix(" %")
        self.iron_input.setDecimals(4)
        self.iron_input.setSpecialValueText("未设置")
        
        self.lead_input = QDoubleSpinBox()
        self.lead_input.setRange(0, 100)
        self.lead_input.setSuffix(" mg/kg")
        self.lead_input.setDecimals(1)
        self.lead_input.setSpecialValueText("未设置")
        
        self.arsenic_input = QDoubleSpinBox()
        self.arsenic_input.setRange(0, 100)
        self.arsenic_input.setSuffix(" mg/kg")
        self.arsenic_input.setDecimals(1)
        self.arsenic_input.setSpecialValueText("未设置")
        
        self.selenium_input = QDoubleSpinBox()
        self.selenium_input.setRange(0, 100)
        self.selenium_input.setSuffix(" mg/kg")
        self.selenium_input.setDecimals(1)
        self.selenium_input.setSpecialValueText("未设置")
        
        self.reducing_substances_check = QCheckBox("通过还原性物质检测")
        
        quality_layout.addRow("92酸含量:", self.sulfuric_acid_92_input)
        quality_layout.addRow("98酸含量:", self.sulfuric_acid_98_input)
        quality_layout.addRow("硝酸盐含量:", self.nitrate_input)
        quality_layout.addRow("氯化物含量:", self.chloride_input)
        quality_layout.addRow("铁含量:", self.iron_input)
        quality_layout.addRow("铅含量:", self.lead_input)
        quality_layout.addRow("砷含量:", self.arsenic_input)
        quality_layout.addRow("硒含量:", self.selenium_input)
        quality_layout.addRow("还原性物质:", self.reducing_substances_check)
        
        quality_group.setLayout(quality_layout)
        detail_layout.addRow(quality_group)
        
        # ========== 安全信息部分 ==========
        safety_group = QGroupBox("安全信息")
        safety_layout = QFormLayout()
        
        self.safety_class_combo = QComboBox()
        self.safety_class_combo.addItems([
            "非危险品", "易燃液体", "腐蚀品", "毒性物质", 
            "氧化剂", "爆炸品", "放射性物质", "其他"
        ])
        
        self.hazard_classification_input = QLineEdit()
        self.hazard_classification_input.setPlaceholderText("如: 腐蚀品")
        
        self.storage_input = QLineEdit()
        self.storage_input.setPlaceholderText("如: 阴凉通风处")
        
        safety_layout.addRow("安全等级:", self.safety_class_combo)
        safety_layout.addRow("危险分类:", self.hazard_classification_input)
        safety_layout.addRow("储存条件:", self.storage_input)
        
        safety_group.setLayout(safety_layout)
        detail_layout.addRow(safety_group)
        
        # ========== 其他属性部分 ==========
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
        
        # ========== 按钮组 ==========
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
        
        # ========== 添加到主布局 ==========
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
                self.material_table.setItem(i, 3, QTableWidgetItem(material.cas_number or ""))  # 新增CAS号列
                self.material_table.setItem(i, 4, QTableWidgetItem(str(material.molar_mass or "")))
                self.material_table.setItem(i, 5, QTableWidgetItem(str(material.density or "")))
                self.material_table.setItem(i, 6, QTableWidgetItem(material.safety_class or ""))
                
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
        
        # 基本属性
        self.material_id_input.setText(material.material_id)
        self.material_name_input.setText(material.name)
        self.chemical_formula_input.setText(material.chemical_formula or "")
        self.cas_input.setText(material.cas_number or "")
        
        # 物性参数
        self.molar_mass_input.setValue(material.molar_mass or 0)
        self.density_input.setValue(material.density or 0)
        self.viscosity_input.setValue(material.viscosity or 0)
        self.specific_heat_input.setValue(material.specific_heat or 0)
        self.thermal_conductivity_input.setValue(material.thermal_conductivity or 0)
        
        # 质量指标
        self.sulfuric_acid_92_input.setValue(material.sulfuric_acid_content_92 or 0)
        self.sulfuric_acid_98_input.setValue(material.sulfuric_acid_content_98 or 0)
        self.nitrate_input.setValue(material.nitrate_content or 0)
        self.chloride_input.setValue(material.chloride_content or 0)
        self.iron_input.setValue(material.iron_content or 0)
        self.lead_input.setValue(material.lead_content or 0)
        self.arsenic_input.setValue(material.arsenic_content or 0)
        self.selenium_input.setValue(material.selenium_content or 0)
        self.reducing_substances_check.setChecked(material.reducing_substances)
        
        # 安全信息
        index = self.safety_class_combo.findText(material.safety_class or "非危险品")
        if index >= 0:
            self.safety_class_combo.setCurrentIndex(index)
            
        self.hazard_classification_input.setText(material.hazard_classification or "")
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
            # 从数据库中删除
            parent_window = self.window()
            if hasattr(parent_window, 'project_manager') and parent_window.project_manager.is_project_open:
                success, message = parent_window.project_manager.delete_data("material_params", material_id)
                if not success:
                    QMessageBox.critical(self, "错误", message)
                    return
            
            # 从表格中删除
            self.material_table.removeRow(row)
            
            # 发送删除信号
            self.data_changed.emit()
            QMessageBox.information(self, "成功", f"物料 {material_id} 已删除")
            
    def save_material(self):
        """保存物料"""
        material_id = self.material_id_input.text().strip()
        if not material_id:
            QMessageBox.warning(self, "警告", "物料ID不能为空")
            return
            
        if not self.material_name_input.text().strip():
            QMessageBox.warning(self, "警告", "物料名称不能为空")
            return
        
        # 创建物料对象（需要先更新models.py中的MaterialParameter类）
        material = MaterialParameter(
            material_id=material_id,
            name=self.material_name_input.text().strip(),
            chemical_formula=self.chemical_formula_input.text().strip(),
            cas_number=self.cas_input.text().strip(),
            
            # 物性参数
            molar_mass=self.molar_mass_input.value() if self.molar_mass_input.value() > 0 else None,
            density=self.density_input.value() if self.density_input.value() > 0 else None,
            viscosity=self.viscosity_input.value() if self.viscosity_input.value() > 0 else None,
            specific_heat=self.specific_heat_input.value() if self.specific_heat_input.value() > 0 else None,
            thermal_conductivity=self.thermal_conductivity_input.value() if self.thermal_conductivity_input.value() > 0 else None,
            
            # 质量指标（基于硫酸标准）
            sulfuric_acid_content_92=self.sulfuric_acid_92_input.value() if self.sulfuric_acid_92_input.value() > 0 else None,
            sulfuric_acid_content_98=self.sulfuric_acid_98_input.value() if self.sulfuric_acid_98_input.value() > 0 else None,
            nitrate_content=self.nitrate_input.value() if self.nitrate_input.value() > 0 else None,
            chloride_content=self.chloride_input.value() if self.chloride_input.value() > 0 else None,
            iron_content=self.iron_input.value() if self.iron_input.value() > 0 else None,
            lead_content=self.lead_input.value() if self.lead_input.value() > 0 else None,
            arsenic_content=self.arsenic_input.value() if self.arsenic_input.value() > 0 else None,
            selenium_content=self.selenium_input.value() if self.selenium_input.value() > 0 else None,
            reducing_substances=self.reducing_substances_check.isChecked(),
            
            # 安全信息
            safety_class=self.safety_class_combo.currentText(),
            storage_conditions=self.storage_input.text().strip(),
            hazard_classification=self.hazard_classification_input.text().strip()
        )
        
        # 重要：需要获取父窗口的project_manager来保存数据
        parent_window = self.window()
        if hasattr(parent_window, 'project_manager') and parent_window.project_manager.is_project_open:
            # 检查是新增还是更新
            existing_material = parent_window.project_manager.get_data("material_params", material_id)
            
            if existing_material:
                # 更新现有物料
                success, message = parent_window.project_manager.update_data("material_params", material)
            else:
                # 添加新物料
                success, message = parent_window.project_manager.add_data("material_params", material)
            
            if not success:
                QMessageBox.critical(self, "错误", message)
                return
        else:
            QMessageBox.warning(self, "警告", "请先打开一个项目")
            return
        
        # 更新表格
        self._update_material_in_table(material)
        
        # 发射信号
        self.data_changed.emit()
        
        QMessageBox.information(self, "成功", f"物料 {material_id} 已保存")
        
    def _update_material_in_table(self, material):
        """在表格中更新或添加物料"""
        # 查找是否已存在
        found = False
        for i in range(self.material_table.rowCount()):
            item = self.material_table.item(i, 0)
            if item and item.text() == material.material_id:
                # 更新现有行
                self.material_table.setItem(i, 1, QTableWidgetItem(material.name))
                self.material_table.setItem(i, 2, QTableWidgetItem(material.chemical_formula or ""))
                self.material_table.setItem(i, 3, QTableWidgetItem(material.cas_number or ""))
                self.material_table.setItem(i, 4, QTableWidgetItem(str(material.molar_mass or "")))
                self.material_table.setItem(i, 5, QTableWidgetItem(str(material.density or "")))
                self.material_table.setItem(i, 6, QTableWidgetItem(material.safety_class or ""))
                found = True
                break
                
        if not found:
            # 添加新行
            row = self.material_table.rowCount()
            self.material_table.insertRow(row)
            self.material_table.setItem(row, 0, QTableWidgetItem(material.material_id))
            self.material_table.setItem(row, 1, QTableWidgetItem(material.name))
            self.material_table.setItem(row, 2, QTableWidgetItem(material.chemical_formula or ""))
            self.material_table.setItem(row, 3, QTableWidgetItem(material.cas_number or ""))
            self.material_table.setItem(row, 4, QTableWidgetItem(str(material.molar_mass or "")))
            self.material_table.setItem(row, 5, QTableWidgetItem(str(material.density or "")))
            self.material_table.setItem(row, 6, QTableWidgetItem(material.safety_class or ""))
        
    def reset_form(self):
        """重置表单"""
        self.current_material_id = None
        
        # 基本属性
        self.material_id_input.clear()
        self.material_name_input.clear()
        self.chemical_formula_input.clear()
        self.cas_input.clear()
        
        # 物性参数
        self.molar_mass_input.setValue(0)
        self.density_input.setValue(0)
        self.viscosity_input.setValue(0)
        self.specific_heat_input.setValue(0)
        self.thermal_conductivity_input.setValue(0)
        
        # 质量指标
        self.sulfuric_acid_92_input.setValue(0)
        self.sulfuric_acid_98_input.setValue(0)
        self.nitrate_input.setValue(0)
        self.chloride_input.setValue(0)
        self.iron_input.setValue(0)
        self.lead_input.setValue(0)
        self.arsenic_input.setValue(0)
        self.selenium_input.setValue(0)
        self.reducing_substances_check.setChecked(True)
        
        # 安全信息
        self.safety_class_combo.setCurrentIndex(0)
        self.hazard_classification_input.clear()
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
            cas_number=self.cas_input.text().strip(),
            molar_mass=self.molar_mass_input.value(),
            density=self.density_input.value(),
            viscosity=self.viscosity_input.value(),
            specific_heat=self.specific_heat_input.value(),
            thermal_conductivity=self.thermal_conductivity_input.value(),
            sulfuric_acid_content_92=self.sulfuric_acid_92_input.value(),
            sulfuric_acid_content_98=self.sulfuric_acid_98_input.value(),
            nitrate_content=self.nitrate_input.value(),
            chloride_content=self.chloride_input.value(),
            iron_content=self.iron_input.value(),
            lead_content=self.lead_input.value(),
            arsenic_content=self.arsenic_input.value(),
            selenium_content=self.selenium_input.value(),
            reducing_substances=self.reducing_substances_check.isChecked(),
            safety_class=self.safety_class_combo.currentText(),
            storage_conditions=self.storage_input.text().strip(),
            hazard_classification=self.hazard_classification_input.text().strip()
        )