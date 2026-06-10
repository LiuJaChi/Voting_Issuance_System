"""
主窗口 UI 類
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from src.backend.database import Database
from src.backend.config_manager import ConfigManager


class MainWindow(QMainWindow):
    """主應用窗口"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.setWindowTitle("投票系統 v1.0.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化數據庫和配置
        self.db = Database()
        self.config_manager = ConfigManager()
        
        # 構建 UI
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        # 創建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 創建主佈局
        main_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("投票系統")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # 創建標籤頁
        tabs = QTabWidget()
        
        # 系統設置標籤
        setup_widget = self.create_setup_tab()
        tabs.addTab(setup_widget, "系統設置")
        
        # 報到標籤
        check_in_widget = self.create_check_in_tab()
        tabs.addTab(check_in_widget, "報到")
        
        # 投票標籤
        voting_widget = self.create_voting_tab()
        tabs.addTab(voting_widget, "投票")
        
        # 結果標籤
        results_widget = self.create_results_tab()
        tabs.addTab(results_widget, "結果")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)
    
    def create_setup_tab(self) -> QWidget:
        """創建系統設置標籤"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("系統設置功能開發中...")
        layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget
    
    def create_check_in_tab(self) -> QWidget:
        """創建報到標籤"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("報到功能開發中...")
        layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget
    
    def create_voting_tab(self) -> QWidget:
        """創建投票標籤"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("投票功能開發中...")
        layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget
    
    def create_results_tab(self) -> QWidget:
        """創建結果標籤"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("結果統計功能開發中...")
        layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget