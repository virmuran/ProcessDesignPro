#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSDS数据管理组件
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QTextEdit, QLabel, QSplitter, QMessageBox, QTabWidget,
    QDateEdit, QTimeEdit, QFileDialog, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont
from core.models import MSDSData

class MSDSWidget(QWidget):
    """MSDS数据管理组件"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.msds_records = []
        self.materials = []  # 物料列表
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # MSDS列表标签页
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        
        # 搜索和筛选
        filter_group = QGroupBox("搜索和筛选")
        filter_layout = QFormLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入物料名称、ID或MSDS编号搜索...")
        self.material_filter_combo = QComboBox()
        self.material_filter_combo.addItem("所有物料")
        self.hazard_class_filter_combo = QComboBox()
        self.hazard_class_filter_combo.addItems(["所有等级", "非危险品", "易燃液体", "腐蚀品", "毒性物质", "氧化剂", "爆炸品"])
        
        filter_layout.addRow("关键字搜索:", self.search_input)
        filter_layout.addRow("物料筛选:", self.material_filter_combo)
        filter_layout.addRow("危险等级筛选:", self.hazard_class_filter_combo)
        
        filter_group.setLayout(filter_layout)
        list_layout.addWidget(filter_group)
        
        # MSDS列表
        list_group = QGroupBox("MSDS列表")
        list_group_layout = QVBoxLayout()
        
        self.msds_table = QTableWidget()
        self.msds_table.setColumnCount(8)
        self.msds_table.setHorizontalHeaderLabels([
            "物料ID", "物料名称", "MSDS编号", "危险等级", "编制日期", 
            "修订日期", "有效期至", "状态"
        ])
        self.msds_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.msds_table.itemSelectionChanged.connect(self.on_msds_selected)
        
        list_group_layout.addWidget(self.msds_table)
        list_group.setLayout(list_group_layout)
        list_layout.addWidget(list_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.add_msds_btn = QPushButton("新增MSDS")
        self.add_msds_btn.clicked.connect(self.add_msds)
        self.edit_msds_btn = QPushButton("编辑")
        self.edit_msds_btn.clicked.connect(self.edit_msds)
        self.delete_msds_btn = QPushButton("删除")
        self.delete_msds_btn.clicked.connect(self.delete_msds)
        self.export_msds_btn = QPushButton("导出PDF")
        self.print_msds_btn = QPushButton("打印")
        
        button_layout.addWidget(self.add_msds_btn)
        button_layout.addWidget(self.edit_msds_btn)
        button_layout.addWidget(self.delete_msds_btn)
        button_layout.addWidget(self.export_msds_btn)
        button_layout.addWidget(self.print_msds_btn)
        button_layout.addStretch()
        
        list_layout.addLayout(button_layout)
        
        tab_widget.addTab(list_tab, "MSDS列表")
        
        # MSDS详情标签页
        detail_tab = QWidget()
        detail_layout = QVBoxLayout(detail_tab)
        
        # 创建可滚动区域
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        self.material_select_combo = QComboBox()
        self.material_select_combo.addItem("请选择物料")
        
        self.msds_number_input = QLineEdit()
        self.msds_number_input.setPlaceholderText("如: MSDS-001")
        
        self.prepare_date_input = QDateEdit()
        self.prepare_date_input.setCalendarPopup(True)
        self.prepare_date_input.setDate(QDate.currentDate())
        
        self.revise_date_input = QDateEdit()
        self.revise_date_input.setCalendarPopup(True)
        self.revise_date_input.setDate(QDate.currentDate())
        
        self.expire_date_input = QDateEdit()
        self.expire_date_input.setCalendarPopup(True)
        self.expire_date_input.setDate(QDate.currentDate().addYears(3))
        
        self.msds_status_combo = QComboBox()
        self.msds_status_combo.addItems(["有效", "已过期", "待审核", "已作废"])
        
        basic_layout.addRow("选择物料:", self.material_select_combo)
        basic_layout.addRow("MSDS编号:", self.msds_number_input)
        basic_layout.addRow("编制日期:", self.prepare_date_input)
        basic_layout.addRow("修订日期:", self.revise_date_input)
        basic_layout.addRow("有效期至:", self.expire_date_input)
        basic_layout.addRow("状态:", self.msds_status_combo)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # 危险标识
        hazard_group = QGroupBox("危险标识")
        hazard_layout = QFormLayout()
        
        self.hazard_classification_input = QLineEdit()
        self.hazard_classification_input.setPlaceholderText("如: 易燃液体, 类别2")
        
        self.hazard_symbols_input = QLineEdit()
        self.hazard_symbols_input.setPlaceholderText("如: 火焰, 感叹号")
        
        self.signal_words_combo = QComboBox()
        self.signal_words_combo.addItems(["警告", "危险"])
        
        hazard_layout.addRow("危险分类:", self.hazard_classification_input)
        hazard_layout.addRow("危险象形图:", self.hazard_symbols_input)
        hazard_layout.addRow("信号词:", self.signal_words_combo)
        
        hazard_group.setLayout(hazard_layout)
        scroll_layout.addWidget(hazard_group)
        
        # 防范说明
        precaution_group = QGroupBox("防范说明")
        precaution_layout = QVBoxLayout()
        
        self.precaution_statements_input = QTextEdit()
        self.precaution_statements_input.setPlaceholderText("输入防范说明...")
        self.precaution_statements_input.setMinimumHeight(100)
        
        precaution_layout.addWidget(self.precaution_statements_input)
        precaution_group.setLayout(precaution_layout)
        scroll_layout.addWidget(precaution_group)
        
        # 急救措施
        first_aid_group = QGroupBox("急救措施")
        first_aid_layout = QFormLayout()
        
        self.inhalation_input = QTextEdit()
        self.inhalation_input.setMinimumHeight(60)
        self.inhalation_input.setPlaceholderText("吸入急救措施")
        
        self.skin_contact_input = QTextEdit()
        self.skin_contact_input.setMinimumHeight(60)
        self.skin_contact_input.setPlaceholderText("皮肤接触急救措施")
        
        self.eye_contact_input = QTextEdit()
        self.eye_contact_input.setMinimumHeight(60)
        self.eye_contact_input.setPlaceholderText("眼睛接触急救措施")
        
        self.ingestion_input = QTextEdit()
        self.ingestion_input.setMinimumHeight(60)
        self.ingestion_input.setPlaceholderText("食入急救措施")
        
        first_aid_layout.addRow("吸入:", self.inhalation_input)
        first_aid_layout.addRow("皮肤接触:", self.skin_contact_input)
        first_aid_layout.addRow("眼睛接触:", self.eye_contact_input)
        first_aid_layout.addRow("食入:", self.ingestion_input)
        
        first_aid_group.setLayout(first_aid_layout)
        scroll_layout.addWidget(first_aid_group)
        
        # 消防措施
        fire_group = QGroupBox("消防措施")
        fire_layout = QFormLayout()
        
        self.suitable_extinguishers_input = QLineEdit()
        self.suitable_extinguishers_input.setPlaceholderText("如: 二氧化碳、干粉、砂土")
        
        self.hazardous_combustion_input = QTextEdit()
        self.hazardous_combustion_input.setMinimumHeight(60)
        self.hazardous_combustion_input.setPlaceholderText("有害燃烧产物")
        
        self.fire_fighting_measures_input = QTextEdit()
        self.fire_fighting_measures_input.setMinimumHeight(80)
        self.fire_fighting_measures_input.setPlaceholderText("消防措施")
        
        fire_layout.addRow("适用灭火剂:", self.suitable_extinguishers_input)
        fire_layout.addRow("有害燃烧产物:", self.hazardous_combustion_input)
        fire_layout.addRow("消防措施:", self.fire_fighting_measures_input)
        
        fire_group.setLayout(fire_layout)
        scroll_layout.addWidget(fire_group)
        
        # 泄露应急处理
        leak_group = QGroupBox("泄露应急处理")
        leak_layout = QVBoxLayout()
        
        self.leak_measures_input = QTextEdit()
        self.leak_measures_input.setMinimumHeight(100)
        self.leak_measures_input.setPlaceholderText("泄露应急处理措施")
        
        leak_layout.addWidget(self.leak_measures_input)
        leak_group.setLayout(leak_layout)
        scroll_layout.addWidget(leak_group)
        
        # 操作处置与储存
        storage_group = QGroupBox("操作处置与储存")
        storage_layout = QFormLayout()
        
        self.handling_precautions_input = QTextEdit()
        self.handling_precautions_input.setMinimumHeight(80)
        self.handling_precautions_input.setPlaceholderText("操作注意事项")
        
        self.storage_conditions_input = QTextEdit()
        self.storage_conditions_input.setMinimumHeight(80)
        self.storage_conditions_input.setPlaceholderText("储存条件")
        
        storage_layout.addRow("操作处置:", self.handling_precautions_input)
        storage_layout.addRow("储存:", self.storage_conditions_input)
        
        storage_group.setLayout(storage_layout)
        scroll_layout.addWidget(storage_group)
        
        # 接触控制和个体防护
        protection_group = QGroupBox("接触控制和个体防护")
        protection_layout = QFormLayout()
        
        self.exposure_limits_input = QLineEdit()
        self.exposure_limits_input.setPlaceholderText("如: TWA 50 ppm")
        
        self.engineering_controls_input = QTextEdit()
        self.engineering_controls_input.setMinimumHeight(60)
        self.engineering_controls_input.setPlaceholderText("工程控制")
        
        self.personal_protection_input = QTextEdit()
        self.personal_protection_input.setMinimumHeight(100)
        self.personal_protection_input.setPlaceholderText("个体防护装备")
        
        protection_layout.addRow("接触限值:", self.exposure_limits_input)
        protection_layout.addRow("工程控制:", self.engineering_controls_input)
        protection_layout.addRow("个体防护:", self.personal_protection_input)
        
        protection_group.setLayout(protection_layout)
        scroll_layout.addWidget(protection_group)
        
        # 理化特性
        properties_group = QGroupBox("理化特性")
        properties_layout = QFormLayout()
        
        self.appearance_input = QLineEdit()
        self.appearance_input.setPlaceholderText("外观与性状")
        
        self.odor_input = QLineEdit()
        self.odor_input.setPlaceholderText("气味")
        
        properties_layout.addRow("外观:", self.appearance_input)
        properties_layout.addRow("气味:", self.odor_input)
        
        properties_group.setLayout(properties_layout)
        scroll_layout.addWidget(properties_group)
        
        # 稳定性和反应性
        stability_group = QGroupBox("稳定性和反应性")
        stability_layout = QFormLayout()
        
        self.stability_input = QLineEdit()
        self.stability_input.setPlaceholderText("稳定性")
        
        self.avoid_conditions_input = QTextEdit()
        self.avoid_conditions_input.setMinimumHeight(60)
        self.avoid_conditions_input.setPlaceholderText("应避免的条件")
        
        self.incompatible_materials_input = QTextEdit()
        self.incompatible_materials_input.setMinimumHeight(60)
        self.incompatible_materials_input.setPlaceholderText("禁配物")
        
        stability_layout.addRow("稳定性:", self.stability_input)
        stability_layout.addRow("应避免的条件:", self.avoid_conditions_input)
        stability_layout.addRow("禁配物:", self.incompatible_materials_input)
        
        stability_group.setLayout(stability_layout)
        scroll_layout.addWidget(stability_group)
        
        # 毒理学信息
        toxicology_group = QGroupBox("毒理学信息")
        toxicology_layout = QFormLayout()
        
        self.toxicity_input = QTextEdit()
        self.toxicity_input.setMinimumHeight(80)
        self.toxicity_input.setPlaceholderText("急性毒性、慢性毒性等")
        
        self.carcinogenicity_input = QLineEdit()
        self.carcinogenicity_input.setPlaceholderText("致癌性")
        
        toxicology_layout.addRow("毒性信息:", self.toxicity_input)
        toxicology_layout.addRow("致癌性:", self.carcinogenicity_input)
        
        toxicology_group.setLayout(toxicology_layout)
        scroll_layout.addWidget(toxicology_group)
        
        # 生态学信息
        ecology_group = QGroupBox("生态学信息")
        ecology_layout = QFormLayout()
        
        self.ecotoxicity_input = QTextEdit()
        self.ecotoxicity_input.setMinimumHeight(80)
        self.ecotoxicity_input.setPlaceholderText("生态毒性信息")
        
        self.persistence_input = QLineEdit()
        self.persistence_input.setPlaceholderText("持久性和降解性")
        
        ecology_layout.addRow("生态毒性:", self.ecotoxicity_input)
        ecology_layout.addRow("持久性:", self.persistence_input)
        
        ecology_group.setLayout(ecology_layout)
        scroll_layout.addWidget(ecology_group)
        
        # 废弃处置
        disposal_group = QGroupBox("废弃处置")
        disposal_layout = QVBoxLayout()
        
        self.disposal_method_input = QTextEdit()
        self.disposal_method_input.setMinimumHeight(80)
        self.disposal_method_input.setPlaceholderText("废弃处置方法")
        
        disposal_layout.addWidget(self.disposal_method_input)
        disposal_group.setLayout(disposal_layout)
        scroll_layout.addWidget(disposal_group)
        
        # 运输信息
        transport_group = QGroupBox("运输信息")
        transport_layout = QFormLayout()
        
        self.transport_class_input = QLineEdit()
        self.transport_class_input.setPlaceholderText("运输危险类别")
        
        self.packaging_group_input = QLineEdit()
        self.packaging_group_input.setPlaceholderText("包装组")
        
        transport_layout.addRow("运输类别:", self.transport_class_input)
        transport_layout.addRow("包装组:", self.packaging_group_input)
        
        transport_group.setLayout(transport_layout)
        scroll_layout.addWidget(transport_group)
        
        # 法规信息
        regulatory_group = QGroupBox("法规信息")
        regulatory_layout = QFormLayout()
        
        self.regulatory_info_input = QTextEdit()
        self.regulatory_info_input.setMinimumHeight(100)
        self.regulatory_info_input.setPlaceholderText("相关法律法规")
        
        regulatory_layout.addRow("法规信息:", self.regulatory_info_input)
        
        regulatory_group.setLayout(regulatory_layout)
        scroll_layout.addWidget(regulatory_group)
        
        # 其他信息
        other_group = QGroupBox("其他信息")
        other_layout = QVBoxLayout()
        
        self.other_info_input = QTextEdit()
        self.other_info_input.setMinimumHeight(80)
        self.other_info_input.setPlaceholderText("其他需要说明的信息")
        
        other_layout.addWidget(self.other_info_input)
        other_group.setLayout(other_layout)
        scroll_layout.addWidget(other_group)
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        
        detail_layout.addWidget(scroll_area)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_msds_btn = QPushButton("保存MSDS")
        self.save_msds_btn.clicked.connect(self.save_msds)
        self.save_msds_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        self.reset_msds_btn = QPushButton("重置表单")
        self.reset_msds_btn.clicked.connect(self.reset_form)
        
        self.preview_btn = QPushButton("预览")
        
        save_layout.addWidget(self.save_msds_btn)
        save_layout.addWidget(self.reset_msds_btn)
        save_layout.addWidget(self.preview_btn)
        save_layout.addStretch()
        
        detail_layout.addLayout(save_layout)
        
        tab_widget.addTab(detail_tab, "MSDS详情")
        
        # 模板管理标签页
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)
        
        template_info = QLabel("<h3>MSDS模板管理</h3>")
        template_info.setAlignment(Qt.AlignCenter)
        template_layout.addWidget(template_info)
        
        template_list = QLabel("模板列表功能正在开发中...")
        template_list.setAlignment(Qt.AlignCenter)
        template_layout.addWidget(template_list)
        
        template_layout.addStretch()
        tab_widget.addTab(template_tab, "模板管理")
        
        main_layout.addWidget(tab_widget)
        
    def set_msds_records(self, records):
        """设置MSDS记录"""
        self.msds_records = records
        self.update_table()
        
    def set_materials(self, materials):
        """设置物料列表"""
        self.materials = materials
        self.update_material_lists()
        
    def update_material_lists(self):
        """更新物料下拉列表"""
        self.material_filter_combo.clear()
        self.material_filter_combo.addItem("所有物料")
        
        self.material_select_combo.clear()
        self.material_select_combo.addItem("请选择物料")
        
        for material in self.materials:
            if hasattr(material, 'material_id'):
                item_text = f"{material.material_id} - {material.name}"
                self.material_filter_combo.addItem(item_text, material.material_id)
                self.material_select_combo.addItem(item_text, material.material_id)
                
    def update_table(self):
        """更新表格"""
        self.msds_table.setRowCount(len(self.msds_records))
        
        for i, msds in enumerate(self.msds_records):
            if hasattr(msds, 'material_id'):
                # 查找物料名称
                material_name = msds.material_id
                for material in self.materials:
                    if hasattr(material, 'material_id') and material.material_id == msds.material_id:
                        material_name = material.name
                        break
                        
                self.msds_table.setItem(i, 0, QTableWidgetItem(msds.material_id))
                self.msds_table.setItem(i, 1, QTableWidgetItem(material_name))
                self.msds_table.setItem(i, 2, QTableWidgetItem(msds.msds_number or ""))
                self.msds_table.setItem(i, 3, QTableWidgetItem(msds.hazard_classification or ""))
                self.msds_table.setItem(i, 4, QTableWidgetItem("2024-01-01"))  # 示例日期
                self.msds_table.setItem(i, 5, QTableWidgetItem("2024-01-01"))  # 示例日期
                self.msds_table.setItem(i, 6, QTableWidgetItem("2027-01-01"))  # 示例日期
                self.msds_table.setItem(i, 7, QTableWidgetItem("有效"))
                
    def on_msds_selected(self):
        """MSDS选择变化"""
        selected_items = self.msds_table.selectedItems()
        if not selected_items:
            return
            
        row = self.msds_table.currentRow()
        material_id = self.msds_table.item(row, 0).text()
        
        # 查找MSDS记录
        msds_record = None
        for msds in self.msds_records:
            if hasattr(msds, 'material_id') and msds.material_id == material_id:
                msds_record = msds
                break
                
        if msds_record:
            self.load_msds(msds_record)
            
    def load_msds(self, msds):
        """加载MSDS数据到表单"""
        # 设置物料
        for i in range(self.material_select_combo.count()):
            if self.material_select_combo.itemData(i) == msds.material_id:
                self.material_select_combo.setCurrentIndex(i)
                break
                
        self.msds_number_input.setText(msds.msds_number or "")
        self.hazard_classification_input.setText(msds.hazard_classification or "")
        self.precaution_statements_input.setText(msds.precautionary_statements or "")
        self.inhalation_input.setText(msds.first_aid_measures or "")
        self.fire_fighting_measures_input.setText(msds.fire_fighting_measures or "")
        self.leak_measures_input.setText(msds.accidental_release_measures or "")
        self.handling_precautions_input.setText(msds.handling_and_storage or "")
        self.storage_conditions_input.setText(msds.handling_and_storage or "")
        self.exposure_limits_input.setText(msds.exposure_controls or "")
        self.stability_input.setText(msds.stability_and_reactivity or "")
        self.toxicity_input.setText(msds.toxicological_information or "")
        self.ecotoxicity_input.setText(msds.ecological_information or "")
        self.disposal_method_input.setText(msds.disposal_considerations or "")
        self.transport_class_input.setText(msds.transport_information or "")
        self.regulatory_info_input.setText(msds.regulatory_information or "")
        self.other_info_input.setText(msds.other_information or "")
        
    def add_msds(self):
        """添加新的MSDS"""
        self.reset_form()
        # 自动生成MSDS编号
        import random
        msds_number = f"MSDS-{random.randint(1000, 9999)}"
        self.msds_number_input.setText(msds_number)
        
    def edit_msds(self):
        """编辑MSDS"""
        selected_items = self.msds_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个MSDS记录")
            return
            
        # 切换到详情标签页
        self.parent().parent().parent().setCurrentIndex(1)  # 切换到详情标签页
        
    def delete_msds(self):
        """删除MSDS"""
        selected_items = self.msds_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个MSDS记录")
            return
            
        row = self.msds_table.currentRow()
        material_id = self.msds_table.item(row, 0).text()
        material_name = self.msds_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除物料 '{material_name}' 的MSDS记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_changed.emit()
            
    def save_msds(self):
        """保存MSDS"""
        material_index = self.material_select_combo.currentIndex()
        if material_index <= 0:
            QMessageBox.warning(self, "警告", "请选择物料")
            return
            
        material_id = self.material_select_combo.itemData(material_index)
        msds_number = self.msds_number_input.text().strip()
        
        if not msds_number:
            QMessageBox.warning(self, "警告", "MSDS编号不能为空")
            return
            
        # 创建MSDS对象
        msds = MSDSData(
            material_id=material_id,
            msds_number=msds_number,
            hazard_classification=self.hazard_classification_input.text().strip(),
            precautionary_statements=self.precaution_statements_input.toPlainText().strip(),
            first_aid_measures=self.inhalation_input.toPlainText().strip(),
            fire_fighting_measures=self.fire_fighting_measures_input.toPlainText().strip(),
            accidental_release_measures=self.leak_measures_input.toPlainText().strip(),
            handling_and_storage=self.handling_precautions_input.toPlainText().strip(),
            exposure_controls=self.exposure_limits_input.text().strip(),
            stability_and_reactivity=self.stability_input.text().strip(),
            toxicological_information=self.toxicity_input.toPlainText().strip(),
            ecological_information=self.ecotoxicity_input.toPlainText().strip(),
            disposal_considerations=self.disposal_method_input.toPlainText().strip(),
            transport_information=self.transport_class_input.text().strip(),
            regulatory_information=self.regulatory_info_input.toPlainText().strip(),
            other_information=self.other_info_input.toPlainText().strip()
        )
        
        self.data_changed.emit()
        QMessageBox.information(self, "成功", f"MSDS记录已保存: {msds_number}")
        
    def reset_form(self):
        """重置表单"""
        self.material_select_combo.setCurrentIndex(0)
        self.msds_number_input.clear()
        self.prepare_date_input.setDate(QDate.currentDate())
        self.revise_date_input.setDate(QDate.currentDate())
        self.expire_date_input.setDate(QDate.currentDate().addYears(3))
        self.msds_status_combo.setCurrentIndex(0)
        
        self.hazard_classification_input.clear()
        self.hazard_symbols_input.clear()
        self.signal_words_combo.setCurrentIndex(0)
        self.precaution_statements_input.clear()
        
        self.inhalation_input.clear()
        self.skin_contact_input.clear()
        self.eye_contact_input.clear()
        self.ingestion_input.clear()
        
        self.suitable_extinguishers_input.clear()
        self.hazardous_combustion_input.clear()
        self.fire_fighting_measures_input.clear()
        
        self.leak_measures_input.clear()
        self.handling_precautions_input.clear()
        self.storage_conditions_input.clear()
        
        self.exposure_limits_input.clear()
        self.engineering_controls_input.clear()
        self.personal_protection_input.clear()
        
        self.appearance_input.clear()
        self.odor_input.clear()
        
        self.stability_input.clear()
        self.avoid_conditions_input.clear()
        self.incompatible_materials_input.clear()
        
        self.toxicity_input.clear()
        self.carcinogenicity_input.clear()
        
        self.ecotoxicity_input.clear()
        self.persistence_input.clear()
        
        self.disposal_method_input.clear()
        self.transport_class_input.clear()
        self.packaging_group_input.clear()
        self.regulatory_info_input.clear()
        self.other_info_input.clear()