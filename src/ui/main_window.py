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
from src.ui.barcode_print_dialog import BarcodePrintDialog
from src.ui.household_manager_dialog import HouseholdManagerDialog
from src.ui.check_in_printer_dialog import CheckInPrinterDialog
from src.ui.voting_ballot_printer_dialog import VotingBallotPrinterDialog


class MainWindow(QMainWindow):
    """主應用窗口"""

    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.setWindowTitle("投票系統 v2.0.0")
        self.setGeometry(100, 100, 1200, 800)

        self.db = Database()
        self.config_manager = ConfigManager()

        self.init_ui()

    def init_ui(self):
        """初始化用戶界面"""
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
        """創建菜單欄"""
        menubar = self.menuBar()

        # 系統菜單
        system_menu = menubar.addMenu("系統")

        setup_action = system_menu.addAction("系統設置")
        setup_action.triggered.connect(self.open_setup_dialog)

        system_menu.addSeparator()

        exit_action = system_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        # 住戶菜單
        household_menu = menubar.addMenu("住戶管理")

        manage_household_action = household_menu.addAction("管理住戶（戶號/姓名）")
        manage_household_action.triggered.connect(self.open_household_manager)

        # 投票菜單
        voting_menu = menubar.addMenu("投票")

        items_action = voting_menu.addAction("管理投票案號")
        items_action.triggered.connect(self.open_voting_items_dialog)

        # 打印菜單
        print_menu = menubar.addMenu("打印")

        check_in_print_action = print_menu.addAction("打印報到單 PDF")
        check_in_print_action.triggered.connect(self.open_check_in_printer_dialog)

        ballot_print_action = print_menu.addAction("打印投票單 PDF")
        ballot_print_action.triggered.connect(self.open_voting_ballot_printer_dialog)

        print_menu.addSeparator()

        barcode_action = print_menu.addAction("生成條碼圖片")
        barcode_action.triggered.connect(self.open_barcode_dialog)

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

    def open_household_manager(self):
        """打開住戶管理對話框"""
        dialog = HouseholdManagerDialog(self)
        dialog.exec()
        self.check_in_window.refresh_check_in_list()

    def open_voting_items_dialog(self):
        """打開投票項目管理對話框"""
        dialog = VotingItemDialog(self)
        dialog.exec()
        self.voting_window.load_voting_items()

    def open_check_in_printer_dialog(self):
        """打開報到單打印對話框"""
        dialog = CheckInPrinterDialog(self)
        dialog.exec()

    def open_voting_ballot_printer_dialog(self):
        """打開投票單打印對話框"""
        dialog = VotingBallotPrinterDialog(self)
        dialog.exec()

    def open_barcode_dialog(self):
        """打開條碼生成對話框"""
        dialog = BarcodePrintDialog(self)
        dialog.exec()

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
