#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QListWidget, QListWidgetItem,
    QMessageBox, QFileDialog, QInputDialog, QTabWidget, QGroupBox,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenuBar, QMenu,
    QStatusBar, QSplitter, QTreeWidget, QTreeWidgetItem, QToolBar,
    QProgressDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QAction, QIcon

from core.project_manager import ProjectManager
from core.models import MaterialParameter, ProcessMaterial, ProcessUnit, EquipmentItem
from config import BASE_DIR

# 导入UI组件 - 简化导入
try:
    from ui.widgets import (
        MaterialWidget, ProcessMaterialWidget, ProcessFlowWidget,
        MSDSWidget, EquipmentWidget, MaterialBalanceWidget,
        HeatBalanceWidget, WaterBalanceWidget
    )
    print("主窗口: 成功导入所有UI组件")
except ImportError as e:
    print(f"主窗口: 导入UI组件时出错 - {e}")
    # 创建占位组件
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
    
    class PlaceholderWidget(QWidget):
        def __init__(self, name, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            label = QLabel(f"{name}组件加载失败")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            
        def set_materials(self, materials): pass
        def set_streams(self, streams): pass
        def set_units(self, units): pass
        def set_equipment_list(self, equipment): pass
        def set_msds_records(self, records): pass
        def set_balance_records(self, records): pass
        def data_changed(self):
            from PySide6.QtCore import Signal
            return Signal()
    
    # 创建占位组件
    MaterialWidget = lambda: PlaceholderWidget("物料参数")
    ProcessMaterialWidget = lambda: PlaceholderWidget("过程物料")
    ProcessFlowWidget = lambda: PlaceholderWidget("工艺路线")
    MSDSWidget = lambda: PlaceholderWidget("MSDS数据")
    EquipmentWidget = lambda: PlaceholderWidget("设备清单")
    MaterialBalanceWidget = lambda: PlaceholderWidget("物料平衡")
    HeatBalanceWidget = lambda: PlaceholderWidget("热量平衡")
    WaterBalanceWidget = lambda: PlaceholderWidget("水平衡")

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化项目管理器
        self.project_manager = ProjectManager()
        
        # 设置窗口属性
        self.setWindowTitle("工艺设计程序")
        self.setGeometry(160, 50, 1600, 900)
        
        # 存储UI组件
        self.widgets = {}
        
        # 创建UI组件
        self._create_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 更新状态栏
        self._update_status_bar()
        
    def _create_ui(self):
        """创建UI界面"""
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建状态栏
        self.statusBar()
        
        # 创建主工作区
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # 左侧：导航面板（修改后）
        nav_panel = QWidget()
        nav_layout = QVBoxLayout(nav_panel)
        
        # 项目信息
        project_group = QGroupBox("项目信息")
        project_layout = QFormLayout()
        
        self.project_name_label = QLabel("无项目")
        project_layout.addRow("项目名称:", self.project_name_label)
        
        self.project_path_label = QLabel("未打开")
        project_layout.addRow("项目路径:", self.project_path_label)
        
        self.project_info_label = QLabel("")
        project_layout.addRow("项目信息:", self.project_info_label)
        
        project_group.setLayout(project_layout)
        nav_layout.addWidget(project_group)
        
        # 项目统计
        stats_group = QGroupBox("项目统计")
        stats_layout = QFormLayout()
        
        self.material_count_label = QLabel("0")
        self.stream_count_label = QLabel("0")
        self.unit_count_label = QLabel("0")
        self.equipment_count_label = QLabel("0")
        
        stats_layout.addRow("物料数量:", self.material_count_label)
        stats_layout.addRow("流股数量:", self.stream_count_label)
        stats_layout.addRow("设备数量:", self.unit_count_label)
        stats_layout.addRow("设备清单:", self.equipment_count_label)
        
        stats_group.setLayout(stats_layout)
        nav_layout.addWidget(stats_group)
        
        # 操作日志（从底部移到左侧）
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # 调整日志控件高度（适配左侧面板）
        self.log_text.setMinimumHeight(300)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        nav_layout.addWidget(log_group)
        
        # 左侧面板添加伸缩项
        nav_layout.addStretch()
        
        # 添加到分割器
        main_splitter.addWidget(nav_panel)
        
        # 右侧：主工作区
        self.main_tabs = QTabWidget()
        
        # 创建各个模块的标签页
        self._create_module_tabs()
        
        main_splitter.addWidget(self.main_tabs)
        
        # 设置分割器比例
        main_splitter.setSizes([250, 1150])
        
        # 移除原底部的日志区域（因为已经移到左侧）
        
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建项目", self)
        new_action.triggered.connect(self.create_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开项目", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存项目", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出项目", self)
        export_action.triggered.connect(self.export_project)
        file_menu.addAction(export_action)
        
        import_action = QAction("导入数据", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        undo_action = QAction("撤销", self)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        preferences_action = QAction("首选项", self)
        edit_menu.addAction(preferences_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        calculator_action = QAction("计算器", self)
        tools_menu.addAction(calculator_action)
        
        units_action = QAction("单位换算", self)
        tools_menu.addAction(units_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("设置", self)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        docs_action = QAction("文档", self)
        help_menu.addAction(docs_action)
        
        examples_action = QAction("示例", self)
        help_menu.addAction(examples_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # 项目操作
        new_btn = QAction("新建", self)
        new_btn.triggered.connect(self.create_project)
        toolbar.addAction(new_btn)
        
        open_btn = QAction("打开", self)
        open_btn.triggered.connect(self.open_project)
        toolbar.addAction(open_btn)
        
        save_btn = QAction("保存", self)
        save_btn.triggered.connect(self.save_project)
        toolbar.addAction(save_btn)
        
        toolbar.addSeparator()
        
        # 数据操作
        add_material_btn = QAction("添加物料", self)
        add_material_btn.triggered.connect(self.add_material)
        toolbar.addAction(add_material_btn)
        
        add_stream_btn = QAction("添加流股", self)
        add_stream_btn.triggered.connect(self.add_stream)
        toolbar.addAction(add_stream_btn)
        
        add_equipment_btn = QAction("添加设备", self)
        add_equipment_btn.triggered.connect(self.add_equipment)
        toolbar.addAction(add_equipment_btn)
        
        toolbar.addSeparator()
        
        # 计算工具
        calculate_btn = QAction("计算平衡", self)
        calculate_btn.triggered.connect(self.calculate_balances)
        toolbar.addAction(calculate_btn)
        
        calculate_all_btn = QAction("计算所有平衡", self)
        calculate_all_btn.triggered.connect(self.calculate_all_balances)
        toolbar.addAction(calculate_all_btn)
        
        report_btn = QAction("生成报告", self)
        report_btn.triggered.connect(self.generate_report)
        toolbar.addAction(report_btn)
        
    def calculate_all_balances(self):
        """计算所有平衡"""
        if not self.project_manager.is_project_open:
            QMessageBox.warning(self, "警告", "请先打开或创建一个项目")
            return
            
        # 显示进度对话框
        progress = QProgressDialog("正在计算物料平衡、热量平衡和水平衡...", "取消", 0, 100, self)
        progress.setWindowTitle("计算中")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        # 模拟进度更新
        for i in range(0, 101, 10):
            progress.setValue(i)
            QApplication.processEvents()
            if progress.wasCanceled():
                break
                
        # 执行计算
        success, message = self.project_manager.calculate_all_balances()
        
        progress.setValue(100)
        
        if success:
            QMessageBox.information(self, "成功", message)
            # 刷新数据
            self._load_all_data()
        else:
            QMessageBox.critical(self, "错误", message)
        
    def _update_status_with_calculation(self, results: Dict[str, Any]):
        """在状态栏显示计算结果"""
        calc_type = results.get('type', '')
        unit_id = results.get('unit_id', '')
        status = results.get('status', '')
        
        if calc_type and unit_id:
            self.statusBar().showMessage(f"{calc_type}计算完成: {unit_id} - {status}", 5000)
        
    def _create_module_tabs(self):
        """创建模块标签页"""
        # 物料参数
        self.material_widget = MaterialWidget()
        self.main_tabs.addTab(self.material_widget, "物料参数")
        self.widgets["material_params"] = self.material_widget
        
        # MSDS数据
        self.msds_widget = MSDSWidget()
        self.main_tabs.addTab(self.msds_widget, "MSDS数据")
        self.widgets["msds_data"] = self.msds_widget
        
        # 过程物料
        self.process_material_widget = ProcessMaterialWidget()
        self.main_tabs.addTab(self.process_material_widget, "过程物料")
        self.widgets["process_materials"] = self.process_material_widget
        
        # 工艺路线
        self.process_flow_widget = ProcessFlowWidget()
        self.main_tabs.addTab(self.process_flow_widget, "工艺路线")
        self.widgets["process_flow"] = self.process_flow_widget
        
        # 设备清单
        self.equipment_widget = EquipmentWidget()
        self.main_tabs.addTab(self.equipment_widget, "设备清单")
        self.widgets["equipment_list"] = self.equipment_widget
        
        # 物料平衡
        self.material_balance_widget = MaterialBalanceWidget()
        self.main_tabs.addTab(self.material_balance_widget, "物料平衡")
        self.widgets["material_balance"] = self.material_balance_widget
        
        # 热量平衡
        self.heat_balance_widget = HeatBalanceWidget()
        self.main_tabs.addTab(self.heat_balance_widget, "热量平衡")
        self.widgets["heat_balance"] = self.heat_balance_widget
        
        # 水平衡
        self.water_balance_widget = WaterBalanceWidget()
        self.main_tabs.addTab(self.water_balance_widget, "水平衡")
        self.widgets["water_balance"] = self.water_balance_widget
        
        # 报告生成（占位）
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        
        title = QLabel("<h2>报告生成</h2>")
        title.setAlignment(Qt.AlignCenter)
        report_layout.addWidget(title)
        
        info = QLabel("<p style='color: #666;'>报告生成模块正在开发中...</p>")
        info.setAlignment(Qt.AlignCenter)
        report_layout.addWidget(info)
        
        report_layout.addStretch()
        self.main_tabs.addTab(report_tab, "报告生成")
            
    def _connect_signals(self):
        """连接信号"""
        # 连接项目管理器信号
        if self.project_manager:
            self.project_manager.project_opened.connect(self._on_project_opened)
            self.project_manager.project_saved.connect(self._on_project_saved)
            self.project_manager.project_closed.connect(self._on_project_closed)
            self.project_manager.data_changed.connect(self._on_data_changed)
        
        # 连接物料组件信号
        self.material_widget.data_changed.connect(self._on_widget_data_changed)
        
    def _update_status_bar(self):
        """更新状态栏"""
        if self.project_manager.is_project_open:
            status = f"当前项目: {self.project_manager.project_name} | "
            status += f"路径: {self.project_manager.project_directory}"
        else:
            status = "无项目打开 | 请先新建或打开一个项目"
            
        self.statusBar().showMessage(status)
        
    def _log_message(self, message: str):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def _update_project_stats(self):
        """更新项目统计信息"""
        if not self.project_manager.is_project_open:
            self.material_count_label.setText("0")
            self.stream_count_label.setText("0")
            self.unit_count_label.setText("0")
            self.equipment_count_label.setText("0")
            return
            
        # 获取各种数据的数量
        materials = self.project_manager.get_data("material_params")
        streams = self.project_manager.get_data("process_materials")
        units = self.project_manager.get_data("process_flow")
        equipment = self.project_manager.get_data("equipment_list")
        
        self.material_count_label.setText(str(len(materials) if materials else 0))
        self.stream_count_label.setText(str(len(streams) if streams else 0))
        self.unit_count_label.setText(str(len(units) if units else 0))
        self.equipment_count_label.setText(str(len(equipment) if equipment else 0))
        
    # ========== 项目操作 ==========
    
    def create_project(self):
        """创建新项目"""
        # 获取项目名称
        name, ok = QInputDialog.getText(self, "新建项目", "请输入项目名称:")
        if not ok or not name:
            return
            
        # 获取保存路径
        path = QFileDialog.getExistingDirectory(self, "选择项目保存路径")
        if not path:
            return
            
        # 获取项目描述
        description, ok = QInputDialog.getText(self, "项目描述", "请输入项目描述:")
        if not ok:
            description = ""
            
        # 获取作者信息
        author, ok = QInputDialog.getText(self, "作者信息", "请输入作者姓名:")
        if not ok:
            author = ""
            
        # 创建项目
        success, message = self.project_manager.create_project(
            name=name,
            path=path,
            description=description,
            author=author
        )
        
        if success:
            self._log_message(f"项目创建成功: {name}")
            self._update_project_info()
            self._load_all_data()
            QMessageBox.information(self, "成功", message)
        else:
            self._log_message(f"项目创建失败: {message}")
            QMessageBox.critical(self, "错误", message)
            
    def open_project(self):
        """打开项目"""
        # 选择项目配置文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", 
            str(BASE_DIR / "data" / "projects"),
            "项目文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        # 打开项目
        success, message = self.project_manager.open_project(file_path)
        
        if success:
            self._log_message(f"项目打开成功: {file_path}")
            self._update_project_info()
            self._load_all_data()
            QMessageBox.information(self, "成功", message)
        else:
            self._log_message(f"项目打开失败: {message}")
            QMessageBox.critical(self, "错误", message)
            
    def save_project(self):
        """保存项目"""
        if not self.project_manager.is_project_open:
            QMessageBox.warning(self, "警告", "没有打开的项目")
            return
            
        success, message = self.project_manager.save_project()
        
        if success:
            self._log_message("项目保存成功")
            QMessageBox.information(self, "成功", message)
        else:
            self._log_message(f"项目保存失败: {message}")
            QMessageBox.critical(self, "错误", message)
            
    def close_project(self):
        """关闭项目"""
        if not self.project_manager.is_project_open:
            return
            
        reply = QMessageBox.question(
            self, "确认", 
            "确定要关闭当前项目吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.project_manager.close_project()
            
    def export_project(self):
        """导出项目"""
        if not self.project_manager.is_project_open:
            QMessageBox.warning(self, "警告", "请先打开或创建一个项目")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出项目", 
            str(BASE_DIR / "data" / "exports" / f"{self.project_manager.project_name}_export.json"),
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        success, message = self.project_manager.export_project(file_path)
        
        if success:
            self._log_message(f"项目导出成功: {file_path}")
            QMessageBox.information(self, "成功", message)
        else:
            self._log_message(f"项目导出失败: {message}")
            QMessageBox.critical(self, "错误", message)
            
    # ========== 数据操作 ==========
    
    def add_material(self):
        """添加物料"""
        if not self.project_manager.is_project_open:
            QMessageBox.warning(self, "警告", "请先打开或创建一个项目")
            return
            
        # 切换到物料参数标签页
        self.main_tabs.setCurrentWidget(self.material_widget)
        self.material_widget.add_material()
        
    def add_stream(self):
        """添加流股"""
        if not self.project_manager.is_project_open:
            QMessageBox.warning(self, "警告", "请先打开或创建一个项目")
            return
            
        # 切换到过程物料标签页
        self.main_tabs.setCurrentWidget(self.process_material_widget)
        self.process_material_widget.add_stream()
        
    def add_equipment(self):
        """添加设备"""
        if not self.project_manager.is_project_open:
            QMessageBox.warning(self, "警告", "请先打开或创建一个项目")
            return
            
        # 简单示例：添加一个测试设备
        equipment_id = f"EQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        equipment = EquipmentItem(
            equipment_id=equipment_id,
            name="测试设备",
            type="反应器",
            specifications={"材质": "不锈钢"},
            quantity=1
        )
        
        success, message = self.project_manager.add_data("equipment_list", equipment)
        
        if success:
            self._log_message(f"设备添加成功: {equipment_id}")
            self._update_project_stats()
            QMessageBox.information(self, "成功", message)
        else:
            self._log_message(f"设备添加失败: {message}")
            QMessageBox.critical(self, "错误", message)
            
    def import_data(self):
        """导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入数据", 
            str(BASE_DIR / "data" / "exports"),
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        success, message = self.project_manager.import_data(file_path)
        
        if success:
            self._log_message(f"数据导入成功: {file_path}")
            self._load_all_data()
            QMessageBox.information(self, "成功", message)
        else:
            self._log_message(f"数据导入失败: {message}")
            QMessageBox.critical(self, "错误", message)
            
    # ========== 数据加载 ==========
    
    def _load_all_data(self):
        """加载所有数据"""
        if not self.project_manager.is_project_open:
            return
            
        # 加载物料数据
        materials = self.project_manager.get_data("material_params")
        if materials:
            self.material_widget.set_materials(materials)
            self.msds_widget.set_materials(materials)
            self.process_material_widget.set_materials(materials)
            self.material_balance_widget.set_materials(materials)
            self.heat_balance_widget.set_materials(materials)
            
        # 加载过程物料数据
        streams = self.project_manager.get_data("process_materials")
        if streams:
            self.process_material_widget.set_streams(streams)
            self.material_balance_widget.set_streams(streams)
            self.heat_balance_widget.set_streams(streams)
            self.water_balance_widget.set_streams(streams)
            
        # 加载工艺单元数据
        units = self.project_manager.get_data("process_flow")
        if units:
            self.process_flow_widget.set_units(units)
            self.material_balance_widget.set_units(units)
            self.heat_balance_widget.set_units(units)
            self.water_balance_widget.set_units(units)
            
        # 加载设备数据
        equipment = self.project_manager.get_data("equipment_list")
        if equipment:
            self.equipment_widget.set_equipment_list(equipment)
            
        # 加载MSDS数据
        msds_data = self.project_manager.get_data("msds_data")
        if msds_data:
            self.msds_widget.set_msds_records(msds_data)
            
        # 加载平衡数据
        material_balance_data = self.project_manager.get_data("material_balance")
        if material_balance_data:
            self.material_balance_widget.set_balance_records(material_balance_data)
            
        # 更新统计信息
        self._update_project_stats()
        
    # ========== UI更新 ==========
    
    def _update_project_info(self):
        """更新项目信息显示"""
        if self.project_manager.is_project_open:
            info = self.project_manager.project_info_data
            
            if info:
                self.project_name_label.setText(info.name)
                self.project_path_label.setText(self.project_manager.project_directory)
                self.project_info_label.setText(f"{info.description} (作者: {info.author})")
        else:
            self.project_name_label.setText("无项目")
            self.project_path_label.setText("未打开")
            self.project_info_label.setText("")
            
        self._update_status_bar()
        
    def refresh_all(self):
        """刷新所有数据"""
        if self.project_manager.is_project_open:
            self._load_all_data()
            self._log_message("数据已刷新")
            
    def calculate_balances(self):
        """计算物料平衡"""
        QMessageBox.information(self, "提示", "物料平衡计算功能正在开发中")
        
    def generate_report(self):
        """生成报告"""
        QMessageBox.information(self, "提示", "报告生成功能正在开发中")
        
    # ========== 信号槽 ==========
    
    @Slot(str)
    def _on_project_opened(self, project_path: str):
        """项目打开信号处理"""
        self._log_message(f"项目已打开: {project_path}")
        self._update_project_info()
        
    @Slot(str)
    def _on_project_saved(self, project_path: str):
        """项目保存信号处理"""
        self._log_message(f"项目已保存: {project_path}")
        
    @Slot()
    def _on_project_closed(self):
        """项目关闭信号处理"""
        self._log_message("项目已关闭")
        self._update_project_info()
        self._clear_all_data()
        
    @Slot(str, str, str)
    def _on_data_changed(self, module: str, data_id: str, operation: str):
        """数据变更信号处理"""
        self._log_message(f"数据变更: {module} - {data_id} - {operation}")
        
        # 刷新相关数据
        self._load_all_data()
        
    @Slot()
    def _on_widget_data_changed(self):
        """组件数据变更信号处理"""
        self._log_message("组件数据变更，需要保存项目")
        # 自动保存项目
        if self.project_manager.is_project_open:
            self.project_manager.save_project(backup=True)
            
    def _clear_all_data(self):
        """清空所有数据"""
        self.material_widget.set_materials([])
        self.process_material_widget.set_streams([])
        self.process_flow_widget.set_units([])
        self._update_project_stats()
        
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>工艺设计程序</h2>
        <p>版本: 1.0.0</p>
        <p>一个用于化工工艺设计的专业应用程序</p>
        <p>主要功能：</p>
        <ul>
            <li>物料参数管理 - 管理物料物性数据</li>
            <li>MSDS数据管理 - 管理安全数据表</li>
            <li>过程物料管理 - 设计和管理工艺流股</li>
            <li>工艺路线设计 - 可视化流程设计</li>
            <li>设备清单管理 - 设备选型和清单</li>
            <li>物料平衡计算 - 工艺物料衡算</li>
            <li>热量平衡计算 - 工艺能量衡算</li>
            <li>水平衡计算 - 工艺水系统设计</li>
        </ul>
        <p>数据库: SQLite | 界面框架: PySide6</p>
        <p>© 2024 工艺设计团队 | 保留所有权利</p>
        """
        
        QMessageBox.about(self, "关于", about_text)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.project_manager.is_project_open:
            reply = QMessageBox.question(
                self, "确认", 
                "确定要退出程序吗？未保存的数据可能会丢失。",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.project_manager.close_project()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())