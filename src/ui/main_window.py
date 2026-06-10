"""
主窗口 UI 類
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from src.backend.config_manager import ConfigManager
from src.backend.database import Database
from src.ui.barcode_print_dialog import BarcodePrintDialog
from src.ui.check_in_window import CheckInWindow
from src.ui.results_window import ResultsWindow
from src.ui.setup_dialog import SetupDialog
from src.ui.voter_import_dialog import VoterImportDialog
from src.ui.voting_item_dialog import VotingItemDialog
from src.ui.voting_window import VotingWindow


class MainWindow(QMainWindow):
    """主應用窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("投票系統 v1.0.0")
        self.setGeometry(100, 100, 1200, 800)
        self.db = Database()
        self.config_manager = ConfigManager()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.create_menu_bar()

        main_layout = QVBoxLayout()
        title = QLabel("投票系統")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        tabs = QTabWidget()
        self.check_in_window = CheckInWindow()
        tabs.addTab(self.check_in_window, "報到管理")

        self.voting_window = VotingWindow()
        tabs.addTab(self.voting_window, "投票")

        self.results_window = ResultsWindow()
        tabs.addTab(self.results_window, "結果統計")

        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)

    def create_menu_bar(self):
        menubar = self.menuBar()

        system_menu = menubar.addMenu("系統")
        setup_action = system_menu.addAction("系統設置")
        setup_action.triggered.connect(self.open_setup_dialog)
        system_menu.addSeparator()
        exit_action = system_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        voting_menu = menubar.addMenu("投票")
        items_action = voting_menu.addAction("管理投票項目")
        items_action.triggered.connect(self.open_voting_items_dialog)
        import_voters_action = voting_menu.addAction("匯入投票者 CSV")
        import_voters_action.triggered.connect(self.open_voter_import_dialog)
        barcode_action = voting_menu.addAction("生成條碼")
        barcode_action.triggered.connect(self.open_barcode_dialog)

        data_menu = menubar.addMenu("數據")
        export_action = data_menu.addAction("導出數據")
        export_action.triggered.connect(self.export_all_data)
        clear_action = data_menu.addAction("清空數據")
        clear_action.triggered.connect(self.clear_all_data)

    def open_setup_dialog(self):
        dialog = SetupDialog(self)
        dialog.exec()

    def open_voting_items_dialog(self):
        dialog = VotingItemDialog(self)
        dialog.exec()
        self.voting_window.load_voting_items()
        self.results_window.refresh_results()

    def open_voter_import_dialog(self):
        dialog = VoterImportDialog(self)
        dialog.exec()
        self.check_in_window.refresh_check_in_list()
        self.voting_window.load_voting_items()

    def open_barcode_dialog(self):
        dialog = BarcodePrintDialog(self)
        dialog.exec()

    def export_all_data(self):
        if self.db.export_data():
            QMessageBox.information(self, "成功", "數據已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "數據導出失敗")

    def clear_all_data(self):
        reply = QMessageBox.question(
            self,
            "確認",
            "確定要清空所有數據嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all_data()
            self.check_in_window.refresh_check_in_list()
            self.voting_window.clear_current_voter()
            self.voting_window.load_voting_items()
            self.results_window.refresh_results()
            QMessageBox.information(self, "成功", "數據已清空")
