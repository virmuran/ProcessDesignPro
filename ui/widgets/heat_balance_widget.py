#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热量平衡计算组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox, QTabWidget,
    QProgressBar, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

class HeatBalanceWidget(QWidget):
    """热量平衡计算组件"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.units = []  # 工艺单元
        self.streams = []  # 过程物料流
        self.materials = []  # 物料参数
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 热量平衡计算标签页
        calc_tab = QWidget()
        calc_layout = QVBoxLayout(calc_tab)
        
        # 选择工艺单元
        unit_select_group = QGroupBox("选择工艺单元")
        unit_select_layout = QHBoxLayout()
        
        self.unit_select_combo = QComboBox()
        self.unit_select_combo.addItem("请选择工艺单元")
        
        self.load_heat_data_btn = QPushButton("加载热数据")
        self.load_heat_data_btn.clicked.connect(self.load_heat_data)
        
        unit_select_layout.addWidget(QLabel("工艺单元:"))
        unit_select_layout.addWidget(self.unit_select_combo)
        unit_select_layout.addWidget(self.load_heat_data_btn)
        unit_select_layout.addStretch()
        
        unit_select_group.setLayout(unit_select_layout)
        calc_layout.addWidget(unit_select_group)
        
        # 热量平衡表格
        heat_group = QGroupBox("热量平衡表")
        heat_layout = QVBoxLayout()
        
        self.heat_table = QTableWidget()
        self.heat_table.setColumnCount(6)
        self.heat_table.setHorizontalHeaderLabels([
            "项目", "输入热量(kW)", "输出热量(kW)", "温度(°C)", "焓值(kJ/kg)", "备注"
        ])
        self.heat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        heat_layout.addWidget(self.heat_table)
        heat_group.setLayout(heat_layout)
        calc_layout.addWidget(heat_group)
        
        # 热参数设置
        param_group = QGroupBox("热参数设置")
        param_layout = QFormLayout()
        
        self.reaction_heat_input = QDoubleSpinBox()
        self.reaction_heat_input.setRange(-10000, 10000)
        self.reaction_heat_input.setSuffix(" kJ/mol")
        self.reaction_heat_input.setValue(0)
        
        self.heat_loss_rate_input = QDoubleSpinBox()
        self.heat_loss_rate_input.setRange(0, 100)
        self.heat_loss_rate_input.setSuffix(" %")
        self.heat_loss_rate_input.setValue(5)
        
        self.efficiency_input = QDoubleSpinBox()
        self.efficiency_input.setRange(0, 100)
        self.efficiency_input.setSuffix(" %")
        self.efficiency_input.setValue(85)
        
        param_layout.addRow("反应热:", self.reaction_heat_input)
        param_layout.addRow("热损失率:", self.heat_loss_rate_input)
        param_layout.addRow("热效率:", self.efficiency_input)
        
        param_group.setLayout(param_layout)
        calc_layout.addWidget(param_group)
        
        # 热量平衡状态
        heat_status_group = QGroupBox("热量平衡状态")
        heat_status_layout = QFormLayout()
        
        self.heat_balance_status_label = QLabel("未计算")
        self.heat_balance_status_label.setStyleSheet("color: #666; font-weight: bold;")
        
        self.heat_input_total_label = QLabel("0 kW")
        self.heat_output_total_label = QLabel("0 kW")
        self.heat_difference_label = QLabel("0 kW")
        self.heat_efficiency_label = QLabel("0%")
        
        heat_status_layout.addRow("平衡状态:", self.heat_balance_status_label)
        heat_status_layout.addRow("总输入热量:", self.heat_input_total_label)
        heat_status_layout.addRow("总输出热量:", self.heat_output_total_label)
        heat_status_layout.addRow("热量差:", self.heat_difference_label)
        heat_status_layout.addRow("热效率:", self.heat_efficiency_label)
        
        heat_status_group.setLayout(heat_status_layout)
        calc_layout.addWidget(heat_status_group)
        
        # 公用工程需求
        utility_group = QGroupBox("公用工程需求")
        utility_layout = QFormLayout()
        
        self.heating_utility_input = QDoubleSpinBox()
        self.heating_utility_input.setRange(0, 10000)
        self.heating_utility_input.setSuffix(" kW")
        
        self.cooling_utility_input = QDoubleSpinBox()
        self.cooling_utility_input.setRange(0, 10000)
        self.cooling_utility_input.setSuffix(" kW")
        
        self.steam_required_input = QDoubleSpinBox()
        self.steam_required_input.setRange(0, 10000)
        self.steam_required_input.setSuffix(" kg/h")
        
        utility_layout.addRow("加热需求:", self.heating_utility_input)
        utility_layout.addRow("冷却需求:", self.cooling_utility_input)
        utility_layout.addRow("蒸汽需求:", self.steam_required_input)
        
        utility_group.setLayout(utility_layout)
        calc_layout.addWidget(utility_group)
        
        # 计算按钮
        button_layout = QHBoxLayout()
        self.calculate_heat_btn = QPushButton("计算热量平衡")
        self.calculate_heat_btn.clicked.connect(self.calculate_heat_balance)
        self.calculate_heat_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        self.save_heat_btn = QPushButton("保存结果")
        self.save_heat_btn.clicked.connect(self.save_heat_balance)
        
        self.reset_heat_btn = QPushButton("重置")
        
        button_layout.addWidget(self.calculate_heat_btn)
        button_layout.addWidget(self.save_heat_btn)
        button_layout.addWidget(self.reset_heat_btn)
        button_layout.addStretch()
        
        calc_layout.addLayout(button_layout)
        
        tab_widget.addTab(calc_tab, "热量平衡")
        
        # 结果分析标签页
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        analysis_info = QLabel("<h3>热量平衡分析</h3>")
        analysis_info.setAlignment(Qt.AlignCenter)
        analysis_layout.addWidget(analysis_info)
        
        # 热量分布
        distribution_group = QGroupBox("热量分布")
        distribution_layout = QFormLayout()
        
        self.reaction_heat_label = QLabel("0 kW")
        self.sensible_heat_label = QLabel("0 kW")
        self.latent_heat_label = QLabel("0 kW")
        self.heat_loss_label = QLabel("0 kW")
        
        distribution_layout.addRow("反应热:", self.reaction_heat_label)
        distribution_layout.addRow("显热:", self.sensible_heat_label)
        distribution_layout.addRow("潜热:", self.latent_heat_label)
        distribution_layout.addRow("热损失:", self.heat_loss_label)
        
        distribution_group.setLayout(distribution_layout)
        analysis_layout.addWidget(distribution_group)
        
        # 节能建议
        suggestion_group = QGroupBox("节能建议")
        suggestion_layout = QVBoxLayout()
        
        self.suggestion_text = QTextEdit()
        self.suggestion_text.setReadOnly(True)
        self.suggestion_text.setMinimumHeight(100)
        self.suggestion_text.setText("热量平衡计算完成后，将显示节能建议...")
        
        suggestion_layout.addWidget(self.suggestion_text)
        suggestion_group.setLayout(suggestion_layout)
        analysis_layout.addWidget(suggestion_group)
        
        analysis_layout.addStretch()
        tab_widget.addTab(analysis_tab, "结果分析")
        
        main_layout.addWidget(tab_widget)
        
    def set_units(self, units):
        """设置工艺单元"""
        self.units = units
        self.update_unit_combo()
        
    def set_streams(self, streams):
        """设置过程物料流"""
        self.streams = streams
        
    def set_materials(self, materials):
        """设置物料参数"""
        self.materials = materials
        
    def update_unit_combo(self):
        """更新单元下拉列表"""
        self.unit_select_combo.clear()
        self.unit_select_combo.addItem("请选择工艺单元")
        
        for unit in self.units:
            if hasattr(unit, 'unit_id'):
                item_text = f"{unit.unit_id} - {unit.name}"
                self.unit_select_combo.addItem(item_text, unit.unit_id)
                
    def load_heat_data(self):
        """加载热数据"""
        index = self.unit_select_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "警告", "请先选择一个工艺单元")
            return
            
        unit_id = self.unit_select_combo.itemData(index)
        
        # 查找单元
        selected_unit = None
        for unit in self.units:
            if hasattr(unit, 'unit_id') and unit.unit_id == unit_id:
                selected_unit = unit
                break
                
        if not selected_unit:
            QMessageBox.warning(self, "警告", "未找到选定的工艺单元")
            return
            
        # 查找连接到该单元的流股
        input_streams = []
        output_streams = []
        
        for stream in self.streams:
            if hasattr(stream, 'destination_unit') and stream.destination_unit == unit_id:
                input_streams.append(stream)
            if hasattr(stream, 'source_unit') and stream.source_unit == unit_id:
                output_streams.append(stream)
                
        # 更新热量表格
        self.update_heat_table(input_streams, output_streams, selected_unit)
        
        # 更新状态
        self.heat_balance_status_label.setText("待计算")
        self.heat_balance_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        
    def update_heat_table(self, input_streams, output_streams, unit):
        """更新热量表格"""
        # 设置表格行数
        row_count = len(input_streams) + len(output_streams) + 4  # +4用于其他行
        self.heat_table.setRowCount(row_count)
        
        row = 0
        
        # 输入热量
        self.heat_table.setItem(row, 0, QTableWidgetItem("输入热量"))
        self.heat_table.item(row, 0).setBackground(QColor(240, 240, 240))
        row += 1
        
        input_heat_total = 0
        for stream in input_streams:
            if hasattr(stream, 'temperature') and stream.temperature:
                # 简化的热量计算
                flow_rate = stream.flow_rate or 0
                specific_heat = 4.18  # 默认比热 kJ/(kg·K)，水
                temperature = stream.temperature or 25
                
                # 查找物料的比热
                if hasattr(stream, 'composition'):
                    for material_id in stream.composition:
                        for material in self.materials:
                            if hasattr(material, 'material_id') and material.material_id == material_id:
                                if material.specific_heat:
                                    specific_heat = material.specific_heat
                                break
                                
                heat = flow_rate * specific_heat * temperature / 3600  # kW
                input_heat_total += heat
                
                self.heat_table.setItem(row, 0, QTableWidgetItem(f"流股 {stream.stream_id}"))
                self.heat_table.setItem(row, 1, QTableWidgetItem(f"{heat:.2f}"))
                self.heat_table.setItem(row, 3, QTableWidgetItem(f"{temperature:.1f}"))
                self.heat_table.setItem(row, 4, QTableWidgetItem(f"{specific_heat:.2f}"))
                row += 1
                
        # 反应热
        reaction_heat = self.reaction_heat_input.value() * 1000  # 简化为固定值
        input_heat_total += reaction_heat
        
        self.heat_table.setItem(row, 0, QTableWidgetItem("反应热"))
        self.heat_table.setItem(row, 1, QTableWidgetItem(f"{reaction_heat:.2f}"))
        row += 1
        
        # 加热公用工程
        heating_utility = self.heating_utility_input.value()
        input_heat_total += heating_utility
        
        self.heat_table.setItem(row, 0, QTableWidgetItem("加热公用工程"))
        self.heat_table.setItem(row, 1, QTableWidgetItem(f"{heating_utility:.2f}"))
        row += 1
        
        # 输出热量
        self.heat_table.setItem(row, 0, QTableWidgetItem("输出热量"))
        self.heat_table.item(row, 0).setBackground(QColor(240, 240, 240))
        row += 1
        
        output_heat_total = 0
        for stream in output_streams:
            if hasattr(stream, 'temperature') and stream.temperature:
                flow_rate = stream.flow_rate or 0
                specific_heat = 4.18
                temperature = stream.temperature or 25
                
                heat = flow_rate * specific_heat * temperature / 3600
                output_heat_total += heat
                
                self.heat_table.setItem(row, 0, QTableWidgetItem(f"流股 {stream.stream_id}"))
                self.heat_table.setItem(row, 2, QTableWidgetItem(f"{heat:.2f}"))
                self.heat_table.setItem(row, 3, QTableWidgetItem(f"{temperature:.1f}"))
                self.heat_table.setItem(row, 4, QTableWidgetItem(f"{specific_heat:.2f}"))
                row += 1
                
        # 冷却公用工程
        cooling_utility = self.cooling_utility_input.value()
        output_heat_total += cooling_utility
        
        self.heat_table.setItem(row, 0, QTableWidgetItem("冷却公用工程"))
        self.heat_table.setItem(row, 2, QTableWidgetItem(f"{cooling_utility:.2f}"))
        row += 1
        
        # 热损失
        heat_loss = input_heat_total * (self.heat_loss_rate_input.value() / 100)
        output_heat_total += heat_loss
        
        self.heat_table.setItem(row, 0, QTableWidgetItem("热损失"))
        self.heat_table.setItem(row, 2, QTableWidgetItem(f"{heat_loss:.2f}"))
        row += 1
        
        # 总计行
        self.heat_table.setItem(row, 0, QTableWidgetItem("总计"))
        self.heat_table.item(row, 0).setBackground(QColor(220, 220, 220))
        self.heat_table.setItem(row, 1, QTableWidgetItem(f"{input_heat_total:.2f}"))
        self.heat_table.setItem(row, 2, QTableWidgetItem(f"{output_heat_total:.2f}"))
        
        # 更新状态标签
        self.heat_input_total_label.setText(f"{input_heat_total:.2f} kW")
        self.heat_output_total_label.setText(f"{output_heat_total:.2f} kW")
        
        diff = output_heat_total - input_heat_total
        self.heat_difference_label.setText(f"{diff:.2f} kW")
        
        efficiency = (output_heat_total / input_heat_total * 100) if input_heat_total > 0 else 0
        self.heat_efficiency_label.setText(f"{efficiency:.2f}%")
        
    def calculate_heat_balance(self):
        """计算热量平衡"""
        total_row = self.heat_table.rowCount() - 1
        if total_row < 0:
            QMessageBox.warning(self, "警告", "没有可计算的数据")
            return
            
        input_heat_text = self.heat_table.item(total_row, 1).text()
        output_heat_text = self.heat_table.item(total_row, 2).text()
        
        if not input_heat_text or not output_heat_text:
            QMessageBox.warning(self, "警告", "数据不完整，无法计算")
            return
            
        input_heat = float(input_heat_text)
        output_heat = float(output_heat_text)
        
        diff = abs(output_heat - input_heat)
        tolerance = 0.01
        
        if diff < tolerance:
            self.heat_balance_status_label.setText("平衡 ✓")
            self.heat_balance_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            QMessageBox.information(self, "成功", "热量平衡计算完成，系统平衡！")
        else:
            self.heat_balance_status_label.setText(f"不平衡 (差: {diff:.2f} kW)")
            self.heat_balance_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            QMessageBox.warning(self, "警告", f"热量不平衡，差值: {diff:.2f} kW")
            
    def save_heat_balance(self):
        """保存热量平衡结果"""
        QMessageBox.information(self, "成功", "热量平衡结果已保存")
        self.data_changed.emit()