"""
主窗口 UI 類
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from src.backend.database import Database
from src.backend.config_manager import ConfigManager
from src.ui.check_in_window import CheckInWindow
from src.ui.voting_window import VotingWindow
from src.ui.results_window import ResultsWindow
from src.ui.setup_dialog import SetupDialog
from src.ui.voting_item_dialog import VotingItemDialog


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
        
        # 創建菜單欄
        self.create_menu_bar()
        
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
        
        # 報到標籤
        self.check_in_window = CheckInWindow()
        tabs.addTab(self.check_in_window, "報到管理")
        
        # 投票標籤
        self.voting_window = VotingWindow()
        tabs.addTab(self.voting_window, "投票")
        
        # 結果標籤
        self.results_window = ResultsWindow()
        tabs.addTab(self.results_window, "結果統計")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)
    
    def create_menu_bar(self):
        """創建菜單欄"""
        menubar = self.menuBar()
        
        # 系統菜單
        system_menu = menubar.addMenu("系統")
        
        setup_action = system_menu.addAction("系統設置")
        setup_action.triggered.connect(self.open_setup_dialog)
        
        system_menu.addSeparator()
        
        exit_action = system_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 投票菜單
        voting_menu = menubar.addMenu("投票")
        
        items_action = voting_menu.addAction("管理投票項目")
        items_action.triggered.connect(self.open_voting_items_dialog)
        
        # 數據菜單
        data_menu = menubar.addMenu("數據")
        
        export_action = data_menu.addAction("導出數據")
        export_action.triggered.connect(self.export_all_data)
        
        clear_action = data_menu.addAction("清空數據")
        clear_action.triggered.connect(self.clear_all_data)
    
    def open_setup_dialog(self):
        """打開系統設置對話框"""
        dialog = SetupDialog(self)
        dialog.exec()
    
    def open_voting_items_dialog(self):
        """打開投票項目管理對話框"""
        dialog = VotingItemDialog(self)
        dialog.exec()
        # 刷新投票窗口
        self.voting_window.load_voting_items()
    
    def export_all_data(self):
        """導出所有數據"""
        if self.db.export_data():
            QMessageBox.information(self, "成功", "數據已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "數據導出失敗")
    
    def clear_all_data(self):
        """清空所有數據"""
        reply = QMessageBox.question(
            self, "確認", "確定要清空所有數據嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all_data()
            self.check_in_window.refresh_check_in_list()
            self.voting_window.load_voting_items()
            self.results_window.refresh_results()
            QMessageBox.information(self, "成功", "數據已清空")
