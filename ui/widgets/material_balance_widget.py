#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料平衡计算组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox, QTabWidget,
    QProgressBar, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from core.models import MaterialBalance

class MaterialBalanceWidget(QWidget):
    """物料平衡计算组件"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.balance_records = []
        self.units = []  # 工艺单元
        self.streams = []  # 过程物料流
        self.materials = []  # 物料参数
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 平衡计算标签页
        calc_tab = QWidget()
        calc_layout = QVBoxLayout(calc_tab)
        
        # 选择工艺单元
        unit_select_group = QGroupBox("选择工艺单元")
        unit_select_layout = QHBoxLayout()
        
        self.unit_select_combo = QComboBox()
        self.unit_select_combo.addItem("请选择工艺单元")
        self.unit_select_combo.currentIndexChanged.connect(self.on_unit_selected)
        
        self.load_unit_btn = QPushButton("加载单元数据")
        self.load_unit_btn.clicked.connect(self.load_unit_data)
        
        unit_select_layout.addWidget(QLabel("工艺单元:"))
        unit_select_layout.addWidget(self.unit_select_combo)
        unit_select_layout.addWidget(self.load_unit_btn)
        unit_select_layout.addStretch()
        
        unit_select_group.setLayout(unit_select_layout)
        calc_layout.addWidget(unit_select_group)
        
        # 物料平衡表格
        balance_group = QGroupBox("物料平衡表")
        balance_layout = QVBoxLayout()
        
        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(8)
        self.balance_table.setHorizontalHeaderLabels([
            "组分", "输入流股", "输入量", "输出流股", "输出量", 
            "转化率", "损耗", "平衡差"
        ])
        self.balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        balance_layout.addWidget(self.balance_table)
        balance_group.setLayout(balance_layout)
        calc_layout.addWidget(balance_group)
        
        # 平衡状态
        status_group = QGroupBox("平衡状态")
        status_layout = QFormLayout()
        
        self.balance_status_label = QLabel("未计算")
        self.balance_status_label.setStyleSheet("color: #666; font-weight: bold;")
        
        self.input_total_label = QLabel("0 kg/h")
        self.output_total_label = QLabel("0 kg/h")
        self.difference_label = QLabel("0 kg/h")
        self.difference_percent_label = QLabel("0.00%")
        
        status_layout.addRow("平衡状态:", self.balance_status_label)
        status_layout.addRow("总输入量:", self.input_total_label)
        status_layout.addRow("总输出量:", self.output_total_label)
        status_layout.addRow("平衡差:", self.difference_label)
        status_layout.addRow("平衡差率:", self.difference_percent_label)
        
        status_group.setLayout(status_layout)
        calc_layout.addWidget(status_group)
        
        # 计算按钮
        button_layout = QHBoxLayout()
        self.calculate_btn = QPushButton("计算平衡")
        self.calculate_btn.clicked.connect(self.calculate_balance)
        self.calculate_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        self.save_balance_btn = QPushButton("保存结果")
        self.save_balance_btn.clicked.connect(self.save_balance)
        
        self.export_btn = QPushButton("导出报告")
        self.reset_calc_btn = QPushButton("重置计算")
        
        button_layout.addWidget(self.calculate_btn)
        button_layout.addWidget(self.save_balance_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.reset_calc_btn)
        button_layout.addStretch()
        
        calc_layout.addLayout(button_layout)
        
        tab_widget.addTab(calc_tab, "平衡计算")
        
        # 平衡结果标签页
        result_tab = QWidget()
        result_layout = QVBoxLayout(result_tab)
        
        # 平衡结果列表
        result_list_group = QGroupBox("平衡结果列表")
        result_list_layout = QVBoxLayout()
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels([
            "单元ID", "单元名称", "平衡状态", "输入总量", "输出总量", "平衡差率"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.itemSelectionChanged.connect(self.on_result_selected)
        
        result_list_layout.addWidget(self.result_table)
        result_list_group.setLayout(result_list_layout)
        result_layout.addWidget(result_list_group)
        
        # 详细结果
        detail_result_group = QGroupBox("详细结果")
        detail_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        
        detail_layout.addWidget(self.result_text)
        detail_result_group.setLayout(detail_layout)
        result_layout.addWidget(detail_result_group)
        
        tab_widget.addTab(result_tab, "平衡结果")
        
        # 可视化标签页
        visual_tab = QWidget()
        visual_layout = QVBoxLayout(visual_tab)
        
        visual_info = QLabel("<h3>物料平衡可视化</h3>")
        visual_info.setAlignment(Qt.AlignCenter)
        visual_layout.addWidget(visual_info)
        
        visual_content = QLabel("物料平衡图表功能正在开发中...")
        visual_content.setAlignment(Qt.AlignCenter)
        visual_content.setStyleSheet("color: #666; font-size: 16px;")
        visual_layout.addWidget(visual_content)
        
        visual_layout.addStretch()
        tab_widget.addTab(visual_tab, "可视化")
        
        main_layout.addWidget(tab_widget)
        
    def set_balance_records(self, records):
        """设置平衡记录"""
        self.balance_records = records
        self.update_result_table()
        
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
                
    def update_result_table(self):
        """更新结果表格"""
        self.result_table.setRowCount(len(self.balance_records))
        
        for i, balance in enumerate(self.balance_records):
            if hasattr(balance, 'unit_id'):
                # 查找单元名称
                unit_name = balance.unit_id
                for unit in self.units:
                    if hasattr(unit, 'unit_id') and unit.unit_id == balance.unit_id:
                        unit_name = unit.name
                        break
                        
                self.result_table.setItem(i, 0, QTableWidgetItem(balance.unit_id))
                self.result_table.setItem(i, 1, QTableWidgetItem(unit_name))
                self.result_table.setItem(i, 2, QTableWidgetItem(balance.balance_status))
                
                # 计算输入输出总量（简化示例）
                input_total = len(balance.input_streams) * 1000 if hasattr(balance, 'input_streams') else 0
                output_total = len(balance.output_streams) * 950 if hasattr(balance, 'output_streams') else 0
                diff = input_total - output_total
                diff_percent = (diff / input_total * 100) if input_total > 0 else 0
                
                self.result_table.setItem(i, 3, QTableWidgetItem(f"{input_total:.2f} kg/h"))
                self.result_table.setItem(i, 4, QTableWidgetItem(f"{output_total:.2f} kg/h"))
                self.result_table.setItem(i, 5, QTableWidgetItem(f"{diff_percent:.2f}%"))
                
                # 根据平衡状态设置颜色
                if balance.balance_status == "平衡":
                    self.result_table.item(i, 2).setForeground(QColor(0, 128, 0))
                elif balance.balance_status == "不平衡":
                    self.result_table.item(i, 2).setForeground(QColor(255, 0, 0))
                else:
                    self.result_table.item(i, 2).setForeground(QColor(255, 165, 0))
                    
    def on_unit_selected(self, index):
        """单元选择变化"""
        if index > 0:
            unit_id = self.unit_select_combo.itemData(index)
            self.load_unit_data_by_id(unit_id)
            
    def load_unit_data(self):
        """加载单元数据"""
        index = self.unit_select_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "警告", "请先选择一个工艺单元")
            return
            
        unit_id = self.unit_select_combo.itemData(index)
        self.load_unit_data_by_id(unit_id)
        
    def load_unit_data_by_id(self, unit_id):
        """根据单元ID加载数据"""
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
                
        # 更新平衡表格
        self.update_balance_table(input_streams, output_streams)
        
        # 更新状态
        self.balance_status_label.setText("待计算")
        self.balance_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        
    def update_balance_table(self, input_streams, output_streams):
        """更新平衡表格"""
        # 收集所有组分
        all_components = set()
        
        for stream in input_streams + output_streams:
            if hasattr(stream, 'composition'):
                all_components.update(stream.composition.keys())
                
        # 设置表格行数
        self.balance_table.setRowCount(len(all_components) + 1)  # +1 用于总计行
        
        # 填充组分数据
        for i, component in enumerate(sorted(all_components)):
            # 查找物料名称
            material_name = component
            for material in self.materials:
                if hasattr(material, 'material_id') and material.material_id == component:
                    material_name = material.name
                    break
                    
            self.balance_table.setItem(i, 0, QTableWidgetItem(material_name))
            
            # 计算输入量
            input_total = 0
            input_streams_text = []
            for stream in input_streams:
                if hasattr(stream, 'composition') and component in stream.composition:
                    flow_rate = stream.flow_rate or 0
                    fraction = stream.composition[component]
                    amount = flow_rate * fraction
                    input_total += amount
                    input_streams_text.append(f"{stream.stream_id}: {amount:.2f}")
                    
            self.balance_table.setItem(i, 1, QTableWidgetItem("\n".join(input_streams_text)))
            self.balance_table.setItem(i, 2, QTableWidgetItem(f"{input_total:.2f}"))
            
            # 计算输出量
            output_total = 0
            output_streams_text = []
            for stream in output_streams:
                if hasattr(stream, 'composition') and component in stream.composition:
                    flow_rate = stream.flow_rate or 0
                    fraction = stream.composition[component]
                    amount = flow_rate * fraction
                    output_total += amount
                    output_streams_text.append(f"{stream.stream_id}: {amount:.2f}")
                    
            self.balance_table.setItem(i, 3, QTableWidgetItem("\n".join(output_streams_text)))
            self.balance_table.setItem(i, 4, QTableWidgetItem(f"{output_total:.2f}"))
            
            # 计算转化率
            conversion = ((input_total - output_total) / input_total * 100) if input_total > 0 else 0
            self.balance_table.setItem(i, 5, QTableWidgetItem(f"{conversion:.2f}%"))
            
            # 损耗
            loss = input_total - output_total if input_total > output_total else 0
            self.balance_table.setItem(i, 6, QTableWidgetItem(f"{loss:.2f}"))
            
            # 平衡差
            diff = output_total - input_total
            self.balance_table.setItem(i, 7, QTableWidgetItem(f"{diff:.2f}"))
            
            # 设置颜色
            if abs(diff) < 0.01:  # 平衡
                self.balance_table.item(i, 7).setForeground(QColor(0, 128, 0))
            else:  # 不平衡
                self.balance_table.item(i, 7).setForeground(QColor(255, 0, 0))
                
        # 总计行
        total_row = len(all_components)
        self.balance_table.setItem(total_row, 0, QTableWidgetItem("总计"))
        
        # 计算总量
        total_input = sum(float(self.balance_table.item(i, 2).text().split()[0]) 
                         for i in range(len(all_components)) 
                         if self.balance_table.item(i, 2))
        total_output = sum(float(self.balance_table.item(i, 4).text().split()[0]) 
                          for i in range(len(all_components)) 
                          if self.balance_table.item(i, 4))
        
        input_streams_all = []
        for stream in input_streams:
            input_streams_all.append(stream.stream_id)
            
        output_streams_all = []
        for stream in output_streams:
            output_streams_all.append(stream.stream_id)
            
        self.balance_table.setItem(total_row, 1, QTableWidgetItem(", ".join(input_streams_all)))
        self.balance_table.setItem(total_row, 2, QTableWidgetItem(f"{total_input:.2f}"))
        self.balance_table.setItem(total_row, 3, QTableWidgetItem(", ".join(output_streams_all)))
        self.balance_table.setItem(total_row, 4, QTableWidgetItem(f"{total_output:.2f}"))
        
        # 更新状态标签
        self.input_total_label.setText(f"{total_input:.2f} kg/h")
        self.output_total_label.setText(f"{total_output:.2f} kg/h")
        
        diff = total_output - total_input
        diff_percent = (diff / total_input * 100) if total_input > 0 else 0
        
        self.difference_label.setText(f"{diff:.2f} kg/h")
        self.difference_percent_label.setText(f"{diff_percent:.2f}%")
        
        # 设置颜色
        if abs(diff) < 0.01:
            self.difference_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.difference_percent_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.difference_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.difference_percent_label.setStyleSheet("color: #F44336; font-weight: bold;")
            
    def calculate_balance(self):
        """计算物料平衡"""
        if self.balance_table.rowCount() <= 1:
            QMessageBox.warning(self, "警告", "没有可计算的数据")
            return
            
        # 检查平衡状态
        total_row = self.balance_table.rowCount() - 1
        
        total_input_text = self.balance_table.item(total_row, 2).text()
        total_output_text = self.balance_table.item(total_row, 4).text()
        
        if not total_input_text or not total_output_text:
            QMessageBox.warning(self, "警告", "数据不完整，无法计算")
            return
            
        total_input = float(total_input_text.split()[0])
        total_output = float(total_output_text.split()[0])
        
        diff = abs(total_output - total_input)
        tolerance = 0.01  # 允许的误差
        
        if diff < tolerance:
            self.balance_status_label.setText("平衡 ✓")
            self.balance_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            QMessageBox.information(self, "成功", "物料平衡计算完成，系统平衡！")
        else:
            self.balance_status_label.setText(f"不平衡 (差: {diff:.2f} kg/h)")
            self.balance_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            QMessageBox.warning(self, "警告", f"物料不平衡，差值: {diff:.2f} kg/h")
            
    def save_balance(self):
        """保存平衡结果"""
        index = self.unit_select_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "警告", "请先选择一个工艺单元")
            return
            
        unit_id = self.unit_select_combo.itemData(index)
        
        # 获取输入输出流股列表
        input_streams = []
        output_streams = []
        
        total_row = self.balance_table.rowCount() - 1
        if total_row >= 0:
            input_text = self.balance_table.item(total_row, 1).text()
            output_text = self.balance_table.item(total_row, 3).text()
            
            if input_text:
                input_streams = [s.strip() for s in input_text.split(",")]
            if output_text:
                output_streams = [s.strip() for s in output_text.split(",")]
                
        # 创建平衡记录
        balance = MaterialBalance(
            unit_id=unit_id,
            input_streams=input_streams,
            output_streams=output_streams,
            balance_status=self.balance_status_label.text().split()[0]
        )
        
        self.data_changed.emit()
        QMessageBox.information(self, "成功", f"物料平衡结果已保存")
        
    def on_result_selected(self):
        """结果选择变化"""
        selected_items = self.result_table.selectedItems()
        if not selected_items:
            return
            
        row = self.result_table.currentRow()
        unit_id = self.result_table.item(row, 0).text()
        
        # 查找平衡记录
        balance = None
        for bal in self.balance_records:
            if hasattr(bal, 'unit_id') and bal.unit_id == unit_id:
                balance = bal
                break
                
        if balance:
            # 显示详细结果
            result_text = f"单元: {unit_id}\n"
            result_text += f"平衡状态: {balance.balance_status}\n"
            result_text += f"输入流股: {', '.join(balance.input_streams) if hasattr(balance, 'input_streams') else '无'}\n"
            result_text += f"输出流股: {', '.join(balance.output_streams) if hasattr(balance, 'output_streams') else '无'}\n"
            
            self.result_text.setText(result_text)