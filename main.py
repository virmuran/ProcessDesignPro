import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt
from ui.main_window import MainWindow
from core.project_manager import ProjectManager

def main():
    # 设置高DPI支持
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    
    app = QApplication(sys.argv)
    
    # 应用样式
    apply_styles(app)
    
    # 初始化项目管理器
    project_manager = ProjectManager()
    
    # 创建主窗口
    window = MainWindow(project_manager)
    window.show()
    
    sys.exit(app.exec())

def apply_styles(app):
    """应用样式表"""
    style_path = os.path.join(os.path.dirname(__file__), "ui", "styles", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())

if __name__ == "__main__":
    main()