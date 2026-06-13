"""
主窗口 UI 類
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox, QMenuBar, QMenu,
    QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from src.backend.database import Database
from src.backend.config_manager import ConfigManager
from src.backend.check_in_printer import CheckInPrinter
from src.backend.voting_ballot_printer import VotingBallotPrinter
from src.backend.barcode_generator import BarcodeGenerator
from src.ui.check_in_window import CheckInWindow
from src.ui.voting_window import VotingWindow
from src.ui.results_window import ResultsWindow
from src.ui.setup_dialog import SetupDialog
from src.ui.voting_item_dialog import VotingItemDialog
from src.ui.household_manager_dialog import HouseholdManagerDialog


class MainWindow(QMainWindow):
    """主應用窗口"""
    
    # 設置變更信號
    settings_changed = pyqtSignal()

    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        self.db = Database()
        self.config_manager = ConfigManager()
        
        # 初始化窗口標題（從配置讀取）
        self.update_window_title()
        self.setGeometry(100, 100, 1200, 800)
        
        # 存儲標題標籤以便後續更新
        self.title_label = None

        self.init_ui()

    def update_window_title(self):
        """從配置更新窗口標題"""
        system_name = self.config_manager.get_config('system_name', '投票系統')
        version = "v2.0.0"
        self.setWindowTitle(f"{system_name} {version}")
        print(f"✓ 窗口標題已更新: {system_name} {version}")

    def init_ui(self):
        """初始化用戶界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.create_menu_bar()

        main_layout = QVBoxLayout()

        # 標題 - 從配置讀取系統名稱
        system_name = self.config_manager.get_config('system_name', '投票系統')
        self.title_label = QLabel(system_name)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        tabs = QTabWidget()

        self.check_in_window = CheckInWindow()
        tabs.addTab(self.check_in_window, "報到管理")

        self.voting_window = VotingWindow()
        tabs.addTab(self.voting_window, "投票")

        #self.results_window = ResultsWindow()
        #tabs.addTab(self.results_window, "結果統計")

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
        print_menu = menubar.addMenu("列印")

        check_in_print_action = print_menu.addAction("印報到單 PDF")
        check_in_print_action.triggered.connect(self.print_check_in_ballots)

        ballot_print_action = print_menu.addAction("印投票單 PDF")
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
        
        # 連接設置變更信號
        dialog.settings_changed.connect(self.on_settings_changed)
        
        dialog.exec()

    def on_settings_changed(self):
        """設置變更回調 - 更新窗口標題和內容"""
        print("⚙️ 檢測到設置變更，正在更新窗口...")
        
        # 更新窗口標題
        self.update_window_title()
        
        # 更新標題標籤
        if self.title_label:
            system_name = self.config_manager.get_config('system_name', '投票系統')
            self.title_label.setText(system_name)
            print(f"✓ UI 標題已更新: {system_name}")

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
        """打印報到單 PDF - 使用戶號作為條碼內容"""
        try:
            # 從數據庫獲取所有住戶
            households = self.db.get_all_households()
            
            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據，無法生成報到單")
                return

            # 構建住戶數據字典列表 - 使用戶號作為條碼內容
            households_for_pdf = []
            for h in households:
                households_for_pdf.append({
                    'household_id': h['household_id'],
                    'name': h['name'],
                    'share_amount': h.get('share_amount', 0.0),
                    'barcode': h['household_id']  # 使用戶號作為條碼內容
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
            pdf_path = printer.generate_pdf(households_for_pdf, filename=pdf_filename)

            QMessageBox.information(
                self, "成功",
                f"報到單已生成完成！\n\n"
                f"📄 PDF 報到單: {pdf_filename}\n\n"
                f"位置: {output_dir}"
            )
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成報到單失敗: {str(e)}")

    def print_voting_ballots(self):
        """打印投票單 PDF - 格式：第幾案 項目名稱 描述 住戶條碼 一張A4紙 印8張投票單"""
        try:
            # 從數據庫獲取所有投票項目
            voting_items = self.db.get_all_voting_items()
            
            if not voting_items:
                QMessageBox.warning(self, "警告", "沒有投票項目，無法生成投票單")
                return
            
            # 從數據庫獲取所有住戶
            households = self.db.get_all_households()
            
            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據，無法生成投票單")
                return

            # 構建投票數據
            voting_data = []
            for item in voting_items:
                voting_data.append({
                    'case_number': item['case_number'],
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'households': households
                })

            print(f"\n📋 準備生成投票單:")
            print(f"   投票案號數: {len(voting_data)}")
            print(f"   住戶數: {len(households)}")
            print(f"   總投票單數: {len(voting_data) * len(households)}")

            # 選擇輸出位置
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "選擇投票單輸出目錄",
                "exports/voting_ballots"
            )

            if not output_dir:
                return

            # 初始化投票單打印機
            printer = VotingBallotPrinter(output_dir=output_dir)

            # 生成 PDF 投票單
            pdf_filename = "voting_ballots.pdf"
            pdf_path = printer.generate_pdf(voting_data, filename=pdf_filename)

            total_ballots = len(voting_data) * len(households)
            QMessageBox.information(
                self, "成功",
                f"投票單已生成完成！\n\n"
                f"📄 PDF 投票單: {pdf_filename}\n"
                f"投票案號: {len(voting_data)} 個\n"
                f"住戶: {len(households)} 個\n"
                f"總投票單: {total_ballots} 張\n\n"
                f"位置: {output_dir}"
            )
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成投票單失敗: {str(e)}")
            import traceback
            traceback.print_exc()

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
