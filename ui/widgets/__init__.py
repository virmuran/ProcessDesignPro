#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件包
"""

from .material_widget import MaterialWidget
from .process_material_widget import ProcessMaterialWidget
from .msds_widget import MSDSWidget
from .equipment_widget import EquipmentWidget
from .material_balance_widget import MaterialBalanceWidget
from .heat_balance_widget import HeatBalanceWidget
from .water_balance_widget import WaterBalanceWidget

# 导入流程组件
try:
    from .flow_widget import FlowWidget as ProcessFlowWidget
    print("UI: 使用 FlowWidget 作为流程组件")
except ImportError:
    try:
        # 回退方案：如果 flow_widget 不存在，尝试其他组件
        from .process_flow_widget import ProcessFlowWidget
        print("UI: 使用 ProcessFlowWidget")
    except ImportError:
        try:
            from .simple_flow_widget import SimpleProcessFlowWidget as ProcessFlowWidget
            print("UI: 使用 SimpleProcessFlowWidget")
        except ImportError:
            # 最终回退：创建一个简单组件
            print("UI: 创建简易流程组件")
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            class ProcessFlowWidget(QWidget):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    layout = QVBoxLayout(self)
                    label = QLabel("流程组件正在开发中...")
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(label)
                    
                def set_units(self, units):
                    pass
                    
                def data_changed(self):
                    from PySide6.QtCore import Signal
                    return Signal()

__all__ = [
    'MaterialWidget',
    'ProcessMaterialWidget', 
    'ProcessFlowWidget',
    'MSDSWidget',
    'EquipmentWidget',
    'MaterialBalanceWidget',
    'HeatBalanceWidget',
    'WaterBalanceWidget'
]