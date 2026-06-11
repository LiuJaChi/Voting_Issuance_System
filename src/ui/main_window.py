"""
主窗口 UI 類
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox, QMenuBar, QMenu,
    QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from src.backend.database import Database
from src.backend.config_manager import ConfigManager
from src.backend.check_in_printer import CheckInPrinter
from src.backend.barcode_generator import BarcodeGenerator
from src.ui.check_in_window import CheckInWindow
from src.ui.voting_window import VotingWindow
from src.ui.results_window import ResultsWindow
from src.ui.setup_dialog import SetupDialog
from src.ui.voting_item_dialog import VotingItemDialog
from src.ui.household_manager_dialog import HouseholdManagerDialog


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
        manage_household_action.triggered.connect(self.manage_households)

        # 投票菜單
        voting_menu = menubar.addMenu("投票")

        items_action = voting_menu.addAction("管理投票案號")
        items_action.triggered.connect(self.open_voting_items_dialog)

        # 打印菜單
        print_menu = menubar.addMenu("打印")

        check_in_print_action = print_menu.addAction("打印報到單 PDF + 導出報到.xlsx")
        check_in_print_action.triggered.connect(self.print_check_in_ballots)

        ballot_print_action = print_menu.addAction("打印投票單 PDF")
        ballot_print_action.triggered.connect(self.print_voting_ballots)

        print_menu.addSeparator()

        barcode_action = print_menu.addAction("生成條碼圖片")
        barcode_action.triggered.connect(self.generate_barcodes)

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

    def manage_households(self):
        """管理住戶"""
        dialog = HouseholdManagerDialog(self)
        dialog.exec()
        # 刷新報到窗口數據
        self.check_in_window.refresh_check_in_list()

    def open_voting_items_dialog(self):
        """打開投票項目管理對話框"""
        dialog = VotingItemDialog(self)
        dialog.exec()
        self.voting_window.load_voting_items()

    def print_check_in_ballots(self):
        """打印報到單 PDF + 導出報到.xlsx"""
        try:
            # 從數據庫獲取所有住戶
            households = self.db.get_all_households()
            
            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據，無法生成報到單")
                return

            # 構建住戶數據字典列表，包含條碼信息
            households_with_barcode = []
            for h in households:
                household_id = h['household_id']
                barcode = self.db.get_barcode_by_household_id(household_id) or household_id
                
                households_with_barcode.append({
                    'household_id': household_id,
                    'name': h['name'],
                    'share_amount': h.get('share_amount', 0.0),
                    'barcode': barcode
                })

            # 選擇輸出位置
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "選擇報到單輸出目錄",
                "exports/check_in_ballots"
            )

            if not output_dir:
                return

            # 初始化打印機
            printer = CheckInPrinter(output_dir=output_dir)

            # 生成 PDF 報到單
            pdf_filename = "check_in_ballots.pdf"
            pdf_path = printer.generate_pdf(households_with_barcode, filename=pdf_filename)

            # 導出 Excel 報到條碼文件
            xlsx_filename = "報到.xlsx"
            xlsx_path = printer.export_check_in_xlsx(households_with_barcode, filename=xlsx_filename)

            QMessageBox.information(
                self, "成功",
                f"報到單已生成完成！\n\n"
                f"📄 PDF 報到單: {pdf_filename}\n"
                f"📊 報到條碼: {xlsx_filename}\n\n"
                f"位置: {output_dir}"
            )
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成報到單失敗: {str(e)}")

    def print_voting_ballots(self):
        """打印投票單 PDF"""
        try:
            QMessageBox.information(
                self, "投票單打印",
                "投票單打印功能即將推出"
            )
            # TODO: 實現投票單 PDF 生成功能
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成投票單失敗: {str(e)}")

    def generate_barcodes(self):
        """生成條碼圖片"""
        try:
            # 從數據庫獲取所有住戶
            households = self.db.get_all_households()

            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據，無法生成條碼")
                return

            # 選擇輸出目錄
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "選擇條碼輸出目錄",
                "exports/barcodes"
            )

            if not output_dir:
                return

            # 生成條碼 - 使用正確的方法
            generator = BarcodeGenerator(output_dir=output_dir)
            
            # 轉換為 (household_id, name) 元組列表
            household_tuples = [(h['household_id'], h['name']) for h in households]
            
            # 生成住戶報到條碼
            generator.generate_household_barcodes_batch(household_tuples, show_text=True)

            QMessageBox.information(
                self, "成功",
                f"條碼圖片已生成\n位置: {output_dir}\n共 {len(households)} 個條碼"
            )
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成條碼失敗: {str(e)}")

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
