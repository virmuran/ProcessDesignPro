from typing import Dict, Any
from PySide6.QtCore import QObject, Signal

class DataSyncEngine(QObject):
    """数据同步引擎，确保各模块间数据一致性"""
    
    sync_required = Signal(str, Dict[str, Any])  # 需要同步的信号
    
    def __init__(self):
        super().__init__()
        self.db_manager = None
        self.sync_rules = self._initialize_sync_rules()
        
    def initialize(self, db_manager):
        """初始化同步引擎"""
        self.db_manager = db_manager
        
    def _initialize_sync_rules(self) -> Dict[str, list]:
        """初始化同步规则"""
        return {
            "material_params": ["process_materials", "material_balance"],
            "process_materials": ["material_balance", "heat_balance", "water_balance"],
            "material_balance": ["heat_balance", "water_balance"],
            "process_flow": ["equipment_list"],
            # 其他模块的同步规则...
        }
        
    def sync_data(self, source_module: str, data: Dict[str, Any]):
        """同步数据到相关模块"""
        if source_module not in self.sync_rules:
            return
            
        target_modules = self.sync_rules[source_module]
        
        for target_module in target_modules:
            # 根据源模块和目标模块的规则处理数据
            processed_data = self._process_sync_data(source_module, target_module, data)
            
            if processed_data:
                # 保存到数据库
                self.db_manager.update_module_data(target_module, processed_data)
                
                # 发出同步信号
                self.sync_required.emit(target_module, processed_data)
                
    def _process_sync_data(self, source: str, target: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """根据同步规则处理数据"""
        # 这里实现具体的同步逻辑
        # 例如：当物料参数更新时，自动更新物料平衡的相关数据
        
        sync_processors = {
            ("material_params", "material_balance"): self._sync_material_to_balance,
            ("process_materials", "heat_balance"): self._sync_process_to_heat,
            # 其他同步处理器...
        }
        
        processor = sync_processors.get((source, target))
        if processor:
            return processor(data)
            
        return {}
        
    def _sync_material_to_balance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """同步物料参数到物料平衡"""
        # 实现具体的同步逻辑
        processed_data = {}
        # ... 处理数据
        return processed_data
        
    def _sync_process_to_heat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """同步过程物料到热量平衡"""
        # 实现具体的同步逻辑
        processed_data = {}
        # ... 处理数据
        return processed_data