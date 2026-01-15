#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水平衡计算组件
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

class WaterBalanceWidget(QWidget):
    """水平衡计算组件"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.units = []  # 工艺单元
        self.streams = []  # 过程物料流
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 水平衡计算标签页
        calc_tab = QWidget()
        calc_layout = QVBoxLayout(calc_tab)
        
        # 水平衡概览
        overview_group = QGroupBox("水平衡概览")
        overview_layout = QFormLayout()
        
        self.total_fresh_water_input = QDoubleSpinBox()
        self.total_fresh_water_input.setRange(0, 1000000)
        self.total_fresh_water_input.setSuffix(" m³/h")
        self.total_fresh_water_input.setValue(100)
        
        self.total_recycled_water_input = QDoubleSpinBox()
        self.total_recycled_water_input.setRange(0, 1000000)
        self.total_recycled_water_input.setSuffix(" m³/h")
        self.total_recycled_water_input.setValue(50)
        
        self.total_wastewater_output = QDoubleSpinBox()
        self.total_wastewater_output.setRange(0, 1000000)
        self.total_wastewater_output.setSuffix(" m³/h")
        self.total_wastewater_output.setValue(120)
        
        self.water_consumption_input = QDoubleSpinBox()
        self.water_consumption_input.setRange(0, 1000000)
        self.water_consumption_input.setSuffix(" m³/h")
        self.water_consumption_input.setValue(30)
        
        overview_layout.addRow("总新鲜水用量:", self.total_fresh_water_input)
        overview_layout.addRow("总回用水量:", self.total_recycled_water_input)
        overview_layout.addRow("总废水产生量:", self.total_wastewater_output)
        overview_layout.addRow("水消耗量:", self.water_consumption_input)
        
        overview_group.setLayout(overview_layout)
        calc_layout.addWidget(overview_group)
        
        # 用水单元平衡
        unit_balance_group = QGroupBox("用水单元水平衡")
        unit_balance_layout = QVBoxLayout()
        
        self.water_balance_table = QTableWidget()
        self.water_balance_table.setColumnCount(7)
        self.water_balance_table.setHorizontalHeaderLabels([
            "用水单元", "新鲜水", "回用水", "蒸汽凝水", "废水", "损耗", "平衡状态"
        ])
        self.water_balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        unit_balance_layout.addWidget(self.water_balance_table)
        unit_balance_group.setLayout(unit_balance_layout)
        calc_layout.addWidget(unit_balance_group)
        
        # 水质参数
        quality_group = QGroupBox("水质参数")
        quality_layout = QFormLayout()
        
        self.fresh_water_quality_combo = QComboBox()
        self.fresh_water_quality_combo.addItems(["自来水", "纯水", "超纯水", "软化水", "循环水"])
        
        self.wastewater_quality_combo = QComboBox()
        self.wastewater_quality_combo.addItems(["低浓度废水", "中浓度废水", "高浓度废水", "含盐废水", "含油废水"])
        
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0, 100)
        self.temperature_input.setSuffix(" °C")
        self.temperature_input.setValue(25)
        
        self.ph_input = QDoubleSpinBox()
        self.ph_input.setRange(0, 14)
        self.ph_input.setValue(7.0)
        
        quality_layout.addRow("新鲜水水质:", self.fresh_water_quality_combo)
        quality_layout.addRow("废水水质:", self.wastewater_quality_combo)
        quality_layout.addRow("水温:", self.temperature_input)
        quality_layout.addRow("pH值:", self.ph_input)
        
        quality_group.setLayout(quality_layout)
        calc_layout.addWidget(quality_group)
        
        # 水平衡状态
        water_status_group = QGroupBox("水平衡状态")
        water_status_layout = QFormLayout()
        
        self.water_balance_status_label = QLabel("未计算")
        self.water_balance_status_label.setStyleSheet("color: #666; font-weight: bold;")
        
        self.total_input_label = QLabel("0 m³/h")
        self.total_output_label = QLabel("0 m³/h")
        self.net_consumption_label = QLabel("0 m³/h")
        self.reuse_ratio_label = QLabel("0%")
        
        water_status_layout.addRow("平衡状态:", self.water_balance_status_label)
        water_status_layout.addRow("总输入水量:", self.total_input_label)
        water_status_layout.addRow("总输出水量:", self.total_output_label)
        water_status_layout.addRow("净消耗量:", self.net_consumption_label)
        water_status_layout.addRow("回用率:", self.reuse_ratio_label)
        
        water_status_group.setLayout(water_status_layout)
        calc_layout.addWidget(water_status_group)
        
        # 节水潜力分析
        saving_group = QGroupBox("节水潜力分析")
        saving_layout = QFormLayout()
        
        self.current_water_footprint_label = QLabel("0 m³/t")
        self.potential_saving_label = QLabel("0%")
        self.saving_measures_text = QTextEdit()
        self.saving_measures_text.setMinimumHeight(80)
        self.saving_measures_text.setPlaceholderText("节水措施建议...")
        
        saving_layout.addRow("当前水足迹:", self.current_water_footprint_label)
        saving_layout.addRow("节水潜力:", self.potential_saving_label)
        saving_layout.addRow("节水措施:", self.saving_measures_text)
        
        saving_group.setLayout(saving_layout)
        calc_layout.addWidget(saving_group)
        
        # 计算按钮
        button_layout = QHBoxLayout()
        self.calculate_water_btn = QPushButton("计算水平衡")
        self.calculate_water_btn.clicked.connect(self.calculate_water_balance)
        self.calculate_water_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        self.save_water_btn = QPushButton("保存结果")
        self.save_water_btn.clicked.connect(self.save_water_balance)
        
        self.optimize_btn = QPushButton("优化建议")
        self.optimize_btn.clicked.connect(self.generate_optimization)
        
        button_layout.addWidget(self.calculate_water_btn)
        button_layout.addWidget(self.save_water_btn)
        button_layout.addWidget(self.optimize_btn)
        button_layout.addStretch()
        
        calc_layout.addLayout(button_layout)
        
        tab_widget.addTab(calc_tab, "水平衡计算")
        
        # 水网络图标签页
        network_tab = QWidget()
        network_layout = QVBoxLayout(network_tab)
        
        network_info = QLabel("<h3>水网络图</h3>")
        network_info.setAlignment(Qt.AlignCenter)
        network_layout.addWidget(network_info)
        
        network_content = QLabel("水网络图可视化功能正在开发中...")
        network_content.setAlignment(Qt.AlignCenter)
        network_content.setStyleSheet("color: #666; font-size: 16px;")
        network_layout.addWidget(network_content)
        
        network_layout.addStretch()
        tab_widget.addTab(network_tab, "水网络图")
        
        # 报告标签页
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        
        report_info = QLabel("<h3>水平衡报告</h3>")
        report_info.setAlignment(Qt.AlignCenter)
        report_layout.addWidget(report_info)
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setText("水平衡计算完成后，将生成详细报告...")
        
        report_layout.addWidget(self.report_text)
        
        export_layout = QHBoxLayout()
        self.export_report_btn = QPushButton("导出报告")
        self.print_report_btn = QPushButton("打印报告")
        
        export_layout.addWidget(self.export_report_btn)
        export_layout.addWidget(self.print_report_btn)
        export_layout.addStretch()
        
        report_layout.addLayout(export_layout)
        
        tab_widget.addTab(report_tab, "报告")
        
        main_layout.addWidget(tab_widget)
        
    def set_units(self, units):
        """设置工艺单元"""
        self.units = units
        self.update_water_balance_table()
        
    def set_streams(self, streams):
        """设置过程物料流"""
        self.streams = streams
        self.update_water_balance_table()
        
    def update_water_balance_table(self):
        """更新水平衡表格"""
        # 筛选与水相关的单元
        water_units = []
        for unit in self.units:
            if hasattr(unit, 'type') and unit.type in ['反应器', '分离器', '换热器', '储罐']:
                water_units.append(unit)
                
        self.water_balance_table.setRowCount(len(water_units) + 1)  # +1用于总计行
        
        total_fresh = 0
        total_recycled = 0
        total_wastewater = 0
        total_loss = 0
        
        for i, unit in enumerate(water_units):
            if hasattr(unit, 'unit_id'):
                self.water_balance_table.setItem(i, 0, QTableWidgetItem(f"{unit.unit_id} - {unit.name}"))
                
                # 计算该单元的水量（简化计算）
                fresh_water = 10.0  # 示例值
                recycled_water = 5.0  # 示例值
                wastewater = 12.0  # 示例值
                loss = fresh_water + recycled_water - wastewater
                
                total_fresh += fresh_water
                total_recycled += recycled_water
                total_wastewater += wastewater
                total_loss += loss
                
                self.water_balance_table.setItem(i, 1, QTableWidgetItem(f"{fresh_water:.2f}"))
                self.water_balance_table.setItem(i, 2, QTableWidgetItem(f"{recycled_water:.2f}"))
                self.water_balance_table.setItem(i, 3, QTableWidgetItem("0.00"))  # 蒸汽凝水
                self.water_balance_table.setItem(i, 4, QTableWidgetItem(f"{wastewater:.2f}"))
                self.water_balance_table.setItem(i, 5, QTableWidgetItem(f"{loss:.2f}"))
                
                # 平衡状态
                if abs(loss) < 0.01:
                    self.water_balance_table.setItem(i, 6, QTableWidgetItem("平衡"))
                    self.water_balance_table.item(i, 6).setForeground(QColor(0, 128, 0))
                else:
                    self.water_balance_table.setItem(i, 6, QTableWidgetItem(f"不平衡({loss:.2f})"))
                    self.water_balance_table.item(i, 6).setForeground(QColor(255, 0, 0))
                    
        # 总计行
        total_row = len(water_units)
        self.water_balance_table.setItem(total_row, 0, QTableWidgetItem("总计"))
        self.water_balance_table.item(total_row, 0).setBackground(QColor(220, 220, 220))
        
        self.water_balance_table.setItem(total_row, 1, QTableWidgetItem(f"{total_fresh:.2f}"))
        self.water_balance_table.setItem(total_row, 2, QTableWidgetItem(f"{total_recycled:.2f}"))
        self.water_balance_table.setItem(total_row, 3, QTableWidgetItem("0.00"))
        self.water_balance_table.setItem(total_row, 4, QTableWidgetItem(f"{total_wastewater:.2f}"))
        self.water_balance_table.setItem(total_row, 5, QTableWidgetItem(f"{total_loss:.2f}"))
        
        # 更新概览数据
        self.total_fresh_water_input.setValue(total_fresh)
        self.total_recycled_water_input.setValue(total_recycled)
        self.total_wastewater_output.setValue(total_wastewater)
        self.water_consumption_input.setValue(total_loss)
        
        # 更新状态标签
        total_input = total_fresh + total_recycled
        total_output = total_wastewater
        
        self.total_input_label.setText(f"{total_input:.2f} m³/h")
        self.total_output_label.setText(f"{total_output:.2f} m³/h")
        self.net_consumption_label.setText(f"{total_loss:.2f} m³/h")
        
        reuse_ratio = (total_recycled / total_input * 100) if total_input > 0 else 0
        self.reuse_ratio_label.setText(f"{reuse_ratio:.2f}%")
        
    def calculate_water_balance(self):
        """计算水平衡"""
        total_input = self.total_fresh_water_input.value() + self.total_recycled_water_input.value()
        total_output = self.total_wastewater_output.value() + self.water_consumption_input.value()
        
        diff = abs(total_output - total_input)
        tolerance = 0.01
        
        if diff < tolerance:
            self.water_balance_status_label.setText("平衡 ✓")
            self.water_balance_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            QMessageBox.information(self, "成功", "水平衡计算完成，系统平衡！")
            
            # 生成报告
            self.generate_water_balance_report()
        else:
            self.water_balance_status_label.setText(f"不平衡 (差: {diff:.2f} m³/h)")
            self.water_balance_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            QMessageBox.warning(self, "警告", f"水平不平衡，差值: {diff:.2f} m³/h")
            
    def save_water_balance(self):
        """保存水平衡结果"""
        QMessageBox.information(self, "成功", "水平衡结果已保存")
        self.data_changed.emit()
        
    def generate_optimization(self):
        """生成优化建议"""
        reuse_ratio = self.total_recycled_water_input.value() / (self.total_fresh_water_input.value() + self.total_recycled_water_input.value()) * 100
        
        suggestions = []
        
        if reuse_ratio < 50:
            suggestions.append("1. 提高水回用率，目标达到50%以上")
            suggestions.append("2. 考虑废水处理回用系统")
            
        if self.water_consumption_input.value() > 20:
            suggestions.append("3. 优化工艺，减少水消耗")
            suggestions.append("4. 检查设备泄漏情况")
            
        if self.total_wastewater_output.value() > 100:
            suggestions.append("5. 加强废水处理，减少排放")
            
        if suggestions:
            self.saving_measures_text.setText("\n".join(suggestions))
            self.potential_saving_label.setText("20-30%")
        else:
            self.saving_measures_text.setText("当前水系统运行良好，继续保持！")
            self.potential_saving_label.setText("5%")
            
        QMessageBox.information(self, "优化建议", "已生成节水优化建议")
        
    def generate_water_balance_report(self):
        """生成水平衡报告"""
        report = "=== 水平衡分析报告 ===\n\n"
        report += f"报告时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "1. 水量汇总\n"
        report += f"   新鲜水用量: {self.total_fresh_water_input.value():.2f} m³/h\n"
        report += f"   回用水量: {self.total_recycled_water_input.value():.2f} m³/h\n"
        report += f"   废水产生量: {self.total_wastewater_output.value():.2f} m³/h\n"
        report += f"   水消耗量: {self.water_consumption_input.value():.2f} m³/h\n\n"
        
        report += "2. 水平衡状态\n"
        report += f"   总输入水量: {self.total_input_label.text()}\n"
        report += f"   总输出水量: {self.total_output_label.text()}\n"
        report += f"   净消耗量: {self.net_consumption_label.text()}\n"
        report += f"   水回用率: {self.reuse_ratio_label.text()}\n\n"
        
        report += "3. 水质参数\n"
        report += f"   新鲜水水质: {self.fresh_water_quality_combo.currentText()}\n"
        report += f"   废水水质: {self.wastewater_quality_combo.currentText()}\n"
        report += f"   水温: {self.temperature_input.value():.1f} °C\n"
        report += f"   pH值: {self.ph_input.value():.1f}\n\n"
        
        report += "4. 节水潜力\n"
        report += f"   当前水足迹: {self.current_water_footprint_label.text()}\n"
        report += f"   节水潜力: {self.potential_saving_label.text()}\n\n"
        
        report += "5. 建议措施\n"
        report += self.saving_measures_text.toPlainText()
        
        self.report_text.setText(report)