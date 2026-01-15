#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备清单管理组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox, QTabWidget,
    QDateEdit, QTreeWidget, QTreeWidgetItem, QHeaderView as QTreeHeader
)
from PySide6.QtCore import Qt, Signal, QDate
from core.models import EquipmentItem

class EquipmentWidget(QWidget):
    """设备清单管理组件"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.equipment_list = []
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 设备清单标签页
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        
        # 设备树形视图
        tree_group = QGroupBox("设备分类")
        tree_layout = QVBoxLayout()
        
        self.equipment_tree = QTreeWidget()
        self.equipment_tree.setColumnCount(3)
        self.equipment_tree.setHeaderLabels(["设备名称", "数量", "状态"])
        self.equipment_tree.itemSelectionChanged.connect(self.on_equipment_selected)
        
        tree_layout.addWidget(self.equipment_tree)
        tree_group.setLayout(tree_layout)
        list_layout.addWidget(tree_group)
        
        # 设备表格
        table_group = QGroupBox("设备清单")
        table_layout = QVBoxLayout()
        
        self.equipment_table = QTableWidget()
        self.equipment_table.setColumnCount(8)
        self.equipment_table.setHorizontalHeaderLabels([
            "设备ID", "设备名称", "类型", "型号", "数量", 
            "材质", "制造商", "状态"
        ])
        self.equipment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.equipment_table.itemSelectionChanged.connect(self.on_table_selected)
        
        table_layout.addWidget(self.equipment_table)
        table_group.setLayout(table_layout)
        list_layout.addWidget(table_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.add_equipment_btn = QPushButton("新增设备")
        self.add_equipment_btn.clicked.connect(self.add_equipment)
        self.edit_equipment_btn = QPushButton("编辑")
        self.delete_equipment_btn = QPushButton("删除")
        self.duplicate_equipment_btn = QPushButton("复制")
        self.export_equipment_btn = QPushButton("导出清单")
        
        button_layout.addWidget(self.add_equipment_btn)
        button_layout.addWidget(self.edit_equipment_btn)
        button_layout.addWidget(self.delete_equipment_btn)
        button_layout.addWidget(self.duplicate_equipment_btn)
        button_layout.addWidget(self.export_equipment_btn)
        button_layout.addStretch()
        
        list_layout.addLayout(button_layout)
        
        tab_widget.addTab(list_tab, "设备清单")
        
        # 设备详情标签页
        detail_tab = QWidget()
        detail_layout = QVBoxLayout(detail_tab)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        self.equipment_id_input = QLineEdit()
        self.equipment_id_input.setPlaceholderText("如: EQ-001")
        
        self.equipment_name_input = QLineEdit()
        self.equipment_name_input.setPlaceholderText("设备名称")
        
        self.equipment_type_combo = QComboBox()
        self.equipment_type_combo.addItems([
            "反应器", "分离器", "换热器", "泵", "压缩机", 
            "储罐", "塔器", "干燥器", "过滤器", "混合器",
            "阀门", "管道", "仪表", "电气设备", "其他"
        ])
        
        self.equipment_model_input = QLineEdit()
        self.equipment_model_input.setPlaceholderText("设备型号")
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1000)
        self.quantity_input.setValue(1)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["设计中", "采购中", "已到货", "安装中", "已安装", "运行中", "维修中", "停用"])
        
        basic_layout.addRow("设备ID:", self.equipment_id_input)
        basic_layout.addRow("设备名称:", self.equipment_name_input)
        basic_layout.addRow("设备类型:", self.equipment_type_combo)
        basic_layout.addRow("设备型号:", self.equipment_model_input)
        basic_layout.addRow("数量:", self.quantity_input)
        basic_layout.addRow("状态:", self.status_combo)
        
        basic_group.setLayout(basic_layout)
        detail_layout.addWidget(basic_group)
        
        # 详细参数
        spec_group = QGroupBox("详细参数")
        spec_layout = QFormLayout()
        
        self.material_input = QLineEdit()
        self.material_input.setPlaceholderText("如: 316L不锈钢")
        
        self.capacity_input = QDoubleSpinBox()
        self.capacity_input.setRange(0, 100000)
        self.capacity_input.setSuffix(" L")
        self.capacity_input.setValue(1000)
        
        self.design_pressure_input = QDoubleSpinBox()
        self.design_pressure_input.setRange(0, 1000)
        self.design_pressure_input.setSuffix(" bar")
        self.design_pressure_input.setValue(10)
        
        self.design_temperature_input = QDoubleSpinBox()
        self.design_temperature_input.setRange(-273, 1000)
        self.design_temperature_input.setSuffix(" °C")
        self.design_temperature_input.setValue(150)
        
        self.dimensions_input = QLineEdit()
        self.dimensions_input.setPlaceholderText("如: Φ1000×2000")
        
        spec_layout.addRow("设备材质:", self.material_input)
        spec_layout.addRow("容积/能力:", self.capacity_input)
        spec_layout.addRow("设计压力:", self.design_pressure_input)
        spec_layout.addRow("设计温度:", self.design_temperature_input)
        spec_layout.addRow("外形尺寸:", self.dimensions_input)
        
        spec_group.setLayout(spec_layout)
        detail_layout.addWidget(spec_group)
        
        # 操作条件
        operation_group = QGroupBox("操作条件")
        operation_layout = QFormLayout()
        
        self.operating_pressure_input = QDoubleSpinBox()
        self.operating_pressure_input.setRange(0, 1000)
        self.operating_pressure_input.setSuffix(" bar")
        self.operating_pressure_input.setValue(5)
        
        self.operating_temperature_input = QDoubleSpinBox()
        self.operating_temperature_input.setRange(-273, 1000)
        self.operating_temperature_input.setSuffix(" °C")
        self.operating_temperature_input.setValue(100)
        
        self.flow_rate_input = QDoubleSpinBox()
        self.flow_rate_input.setRange(0, 1000000)
        self.flow_rate_input.setSuffix(" m³/h")
        
        self.media_input = QLineEdit()
        self.media_input.setPlaceholderText("处理的介质")
        
        operation_layout.addRow("操作压力:", self.operating_pressure_input)
        operation_layout.addRow("操作温度:", self.operating_temperature_input)
        operation_layout.addRow("流量:", self.flow_rate_input)
        operation_layout.addRow("介质:", self.media_input)
        
        operation_group.setLayout(operation_layout)
        detail_layout.addWidget(operation_group)
        
        # 公用工程需求
        utility_group = QGroupBox("公用工程需求")
        utility_layout = QFormLayout()
        
        self.power_input = QDoubleSpinBox()
        self.power_input.setRange(0, 10000)
        self.power_input.setSuffix(" kW")
        
        self.water_consumption_input = QDoubleSpinBox()
        self.water_consumption_input.setRange(0, 1000)
        self.water_consumption_input.setSuffix(" m³/h")
        
        self.steam_consumption_input = QDoubleSpinBox()
        self.steam_consumption_input.setRange(0, 1000)
        self.steam_consumption_input.setSuffix(" kg/h")
        
        self.cooling_water_input = QDoubleSpinBox()
        self.cooling_water_input.setRange(0, 1000)
        self.cooling_water_input.setSuffix(" m³/h")
        
        utility_layout.addRow("电力:", self.power_input)
        utility_layout.addRow("用水:", self.water_consumption_input)
        utility_layout.addRow("蒸汽:", self.steam_consumption_input)
        utility_layout.addRow("冷却水:", self.cooling_water_input)
        
        utility_group.setLayout(utility_layout)
        detail_layout.addWidget(utility_group)
        
        # 供应商信息
        vendor_group = QGroupBox("供应商信息")
        vendor_layout = QFormLayout()
        
        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText("制造商")
        
        self.supplier_input = QLineEdit()
        self.supplier_input.setPlaceholderText("供应商")
        
        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("联系人")
        
        self.contact_phone_input = QLineEdit()
        self.contact_phone_input.setPlaceholderText("联系电话")
        
        self.delivery_date_input = QDateEdit()
        self.delivery_date_input.setCalendarPopup(True)
        self.delivery_date_input.setDate(QDate.currentDate().addMonths(1))
        
        vendor_layout.addRow("制造商:", self.manufacturer_input)
        vendor_layout.addRow("供应商:", self.supplier_input)
        vendor_layout.addRow("联系人:", self.contact_person_input)
        vendor_layout.addRow("联系电话:", self.contact_phone_input)
        vendor_layout.addRow("交货日期:", self.delivery_date_input)
        
        vendor_group.setLayout(vendor_layout)
        detail_layout.addWidget(vendor_group)
        
        # 备注
        remark_group = QGroupBox("备注")
        remark_layout = QVBoxLayout()
        
        self.remark_input = QTextEdit()
        self.remark_input.setMinimumHeight(50)
        self.remark_input.setPlaceholderText("其他备注信息...")
        
        remark_layout.addWidget(self.remark_input)
        remark_group.setLayout(remark_layout)
        detail_layout.addWidget(remark_group)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_equipment_btn = QPushButton("保存设备")
        self.save_equipment_btn.clicked.connect(self.save_equipment)
        self.save_equipment_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        self.reset_equipment_btn = QPushButton("重置")
        self.reset_equipment_btn.clicked.connect(self.reset_form)
        
        self.calculate_btn = QPushButton("计算参数")
        
        save_layout.addWidget(self.save_equipment_btn)
        save_layout.addWidget(self.reset_equipment_btn)
        save_layout.addWidget(self.calculate_btn)
        save_layout.addStretch()
        
        detail_layout.addLayout(save_layout)
        
        tab_widget.addTab(detail_tab, "设备详情")
        
        # 设备汇总标签页
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        summary_info = QLabel("<h3>设备汇总统计</h3>")
        summary_info.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(summary_info)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QFormLayout()
        
        self.total_equipment_label = QLabel("0")
        self.total_value_label = QLabel("¥0.00")
        self.by_type_label = QLabel("--")
        self.by_status_label = QLabel("--")
        
        stats_layout.addRow("设备总数:", self.total_equipment_label)
        stats_layout.addRow("总价值:", self.total_value_label)
        stats_layout.addRow("按类型统计:", self.by_type_label)
        stats_layout.addRow("按状态统计:", self.by_status_label)
        
        stats_group.setLayout(stats_layout)
        summary_layout.addWidget(stats_group)
        
        summary_layout.addStretch()
        tab_widget.addTab(summary_tab, "设备汇总")
        
        main_layout.addWidget(tab_widget)
        
    def set_equipment_list(self, equipment_list):
        """设置设备列表"""
        self.equipment_list = equipment_list
        self.update_tree()
        self.update_table()
        self.update_stats()
        
    def update_tree(self):
        """更新树形视图"""
        self.equipment_tree.clear()
        
        # 按设备类型分类
        type_categories = {}
        for equipment in self.equipment_list:
            if hasattr(equipment, 'type'):
                eq_type = equipment.type
                if eq_type not in type_categories:
                    type_categories[eq_type] = []
                type_categories[eq_type].append(equipment)
                
        # 创建树节点
        for eq_type, equipments in type_categories.items():
            type_item = QTreeWidgetItem([eq_type, str(len(equipments)), ""])
            
            total_qty = sum(eq.quantity for eq in equipments if hasattr(eq, 'quantity'))
            type_item.setText(1, str(total_qty))
            
            for equipment in equipments:
                if hasattr(equipment, 'equipment_id'):
                    child_item = QTreeWidgetItem([
                        equipment.name,
                        str(equipment.quantity),
                        self.status_combo.currentText() if hasattr(self, 'status_combo') else ""
                    ])
                    child_item.setData(0, Qt.UserRole, equipment.equipment_id)
                    type_item.addChild(child_item)
                    
            self.equipment_tree.addTopLevelItem(type_item)
            
        self.equipment_tree.expandAll()
        
    def update_table(self):
        """更新表格"""
        self.equipment_table.setRowCount(len(self.equipment_list))
        
        for i, equipment in enumerate(self.equipment_list):
            if hasattr(equipment, 'equipment_id'):
                self.equipment_table.setItem(i, 0, QTableWidgetItem(equipment.equipment_id))
                self.equipment_table.setItem(i, 1, QTableWidgetItem(equipment.name))
                self.equipment_table.setItem(i, 2, QTableWidgetItem(equipment.type))
                self.equipment_table.setItem(i, 3, QTableWidgetItem(equipment.model or ""))
                self.equipment_table.setItem(i, 4, QTableWidgetItem(str(equipment.quantity)))
                self.equipment_table.setItem(i, 5, QTableWidgetItem(equipment.material_of_construction or ""))
                self.equipment_table.setItem(i, 6, QTableWidgetItem(equipment.manufacturer or ""))
                self.equipment_table.setItem(i, 7, QTableWidgetItem("设计中"))
                
    def update_stats(self):
        """更新统计信息"""
        total_count = len(self.equipment_list)
        total_qty = sum(eq.quantity for eq in self.equipment_list if hasattr(eq, 'quantity'))
        
        self.total_equipment_label.setText(f"{total_count} 台 ({total_qty} 件)")
        
        # 按类型统计
        type_stats = {}
        for equipment in self.equipment_list:
            if hasattr(equipment, 'type'):
                eq_type = equipment.type
                type_stats[eq_type] = type_stats.get(eq_type, 0) + equipment.quantity
                
        type_text = ", ".join([f"{k}: {v}" for k, v in type_stats.items()])
        self.by_type_label.setText(type_text[:50] + "..." if len(type_text) > 50 else type_text)
        
    def on_equipment_selected(self):
        """设备树选择变化"""
        selected_items = self.equipment_tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        equipment_id = item.data(0, Qt.UserRole)
        
        if equipment_id:
            # 查找设备
            equipment = None
            for eq in self.equipment_list:
                if hasattr(eq, 'equipment_id') and eq.equipment_id == equipment_id:
                    equipment = eq
                    break
                    
            if equipment:
                self.load_equipment(equipment)
                
    def on_table_selected(self):
        """表格选择变化"""
        selected_items = self.equipment_table.selectedItems()
        if not selected_items:
            return
            
        row = self.equipment_table.currentRow()
        equipment_id = self.equipment_table.item(row, 0).text()
        
        # 查找设备
        equipment = None
        for eq in self.equipment_list:
            if hasattr(eq, 'equipment_id') and eq.equipment_id == equipment_id:
                equipment = eq
                break
                
        if equipment:
            self.load_equipment(equipment)
            
    def load_equipment(self, equipment):
        """加载设备数据到表单"""
        self.equipment_id_input.setText(equipment.equipment_id)
        self.equipment_name_input.setText(equipment.name)
        
        # 设置设备类型
        index = self.equipment_type_combo.findText(equipment.type)
        if index >= 0:
            self.equipment_type_combo.setCurrentIndex(index)
            
        self.equipment_model_input.setText(equipment.model or "")
        self.quantity_input.setValue(equipment.quantity)
        self.material_input.setText(equipment.material_of_construction or "")
        self.manufacturer_input.setText(equipment.manufacturer or "")
        
    def add_equipment(self):
        """添加新设备"""
        self.reset_form()
        import random
        new_id = f"EQ-{random.randint(1000, 9999)}"
        self.equipment_id_input.setText(new_id)
        self.equipment_name_input.setFocus()
        
    def save_equipment(self):
        """保存设备"""
        equipment_id = self.equipment_id_input.text().strip()
        if not equipment_id:
            QMessageBox.warning(self, "警告", "设备ID不能为空")
            return
            
        equipment_name = self.equipment_name_input.text().strip()
        if not equipment_name:
            QMessageBox.warning(self, "警告", "设备名称不能为空")
            return
            
        # 创建设备对象
        equipment = EquipmentItem(
            equipment_id=equipment_id,
            name=equipment_name,
            type=self.equipment_type_combo.currentText(),
            model=self.equipment_model_input.text().strip(),
            quantity=self.quantity_input.value(),
            material_of_construction=self.material_input.text().strip(),
            manufacturer=self.manufacturer_input.text().strip(),
            specifications={
                "capacity": self.capacity_input.value(),
                "design_pressure": self.design_pressure_input.value(),
                "design_temperature": self.design_temperature_input.value(),
                "dimensions": self.dimensions_input.text().strip()
            },
            operating_conditions={
                "operating_pressure": self.operating_pressure_input.value(),
                "operating_temperature": self.operating_temperature_input.value(),
                "flow_rate": self.flow_rate_input.value(),
                "media": self.media_input.text().strip()
            },
            utility_requirements={
                "power": self.power_input.value(),
                "water": self.water_consumption_input.value(),
                "steam": self.steam_consumption_input.value(),
                "cooling_water": self.cooling_water_input.value()
            }
        )
        
        self.data_changed.emit()
        QMessageBox.information(self, "成功", f"设备 {equipment_id} 已保存")
        
    def reset_form(self):
        """重置表单"""
        self.equipment_id_input.clear()
        self.equipment_name_input.clear()
        self.equipment_type_combo.setCurrentIndex(0)
        self.equipment_model_input.clear()
        self.quantity_input.setValue(1)
        self.status_combo.setCurrentIndex(0)
        
        self.material_input.clear()
        self.capacity_input.setValue(1000)
        self.design_pressure_input.setValue(10)
        self.design_temperature_input.setValue(150)
        self.dimensions_input.clear()
        
        self.operating_pressure_input.setValue(5)
        self.operating_temperature_input.setValue(100)
        self.flow_rate_input.setValue(0)
        self.media_input.clear()
        
        self.power_input.setValue(0)
        self.water_consumption_input.setValue(0)
        self.steam_consumption_input.setValue(0)
        self.cooling_water_input.setValue(0)
        
        self.manufacturer_input.clear()
        self.supplier_input.clear()
        self.contact_person_input.clear()
        self.contact_phone_input.clear()
        self.delivery_date_input.setDate(QDate.currentDate().addMonths(1))
        
        self.remark_input.clear()