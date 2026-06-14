"""
投票系統 UI 主窗口（整合版）
- 統一 key：meeting_pass_percentage / system_title_font_size
- 新增：匯出投票結果報表 PDF
- 修正：報到單/投票單列印方法名稱相容（避免 method not found）
"""

import traceback
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from src.backend.database import Database
from src.backend.config_manager import ConfigManager
from src.backend.check_in_printer import CheckInPrinter
from src.backend.voting_ballot_printer import VotingBallotPrinter
from src.backend.voting_result_report_printer import VotingResultReportPrinter
from src.backend.barcode_generator import BarcodeGenerator
from src.ui.check_in_window import CheckInWindow
from src.ui.voting_window import VotingWindow
from src.ui.setup_dialog import SetupDialog
from src.ui.voting_item_dialog import VotingItemDialog
from src.ui.household_manager_dialog import HouseholdManagerDialog


class MainWindow(QMainWindow):
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.config_manager = ConfigManager()
        self.db = Database(config_manager=self.config_manager)

        self.title_label = None
        self.header_widget = None
        self.tabs = None
        self.results_window = None

        self.logo_overlay = QLabel(self)
        self.logo_overlay.setObjectName("LogoOverlay")
        self.logo_overlay.setFixedSize(96, 96)
        self.logo_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.logo_overlay.hide()

        self.update_window_title()
        self.setGeometry(100, 100, 1400, 900)

        self.init_ui()
        self.apply_professional_theme()
        self._load_logo()
        self._position_logo_overlay()

    def _cfg_get(self, key, default=None):
        if hasattr(self.config_manager, "get_config"):
            return self.config_manager.get_config(key, default)
        if hasattr(self.config_manager, "get_setting"):
            v = self.config_manager.get_setting(key, default)
            return default if v is None else v
        return default

    def _to_int(self, value, default=0):
        try:
            return int(float(value))
        except Exception:
            return int(default)

    def update_window_title(self):
        system_name = self._cfg_get("system_name", "投票系統")
        version = "v2.0.0"
        self.setWindowTitle(f"{system_name} {version}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.create_menu_bar()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.header_widget = QWidget()
        self.header_widget.setObjectName("HeaderBar")
        self.header_widget.setMinimumHeight(96)
        self.header_widget.setMaximumHeight(96)

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(12, 0, 12, 0)

        self.title_label = QLabel()
        self.title_label.setObjectName("SystemTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_system_title_style()

        header_layout.addStretch()
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        main_layout.addWidget(self.header_widget)

        self.tabs = QTabWidget()
        self.check_in_window = CheckInWindow(config_manager=self.config_manager)
        self.tabs.addTab(self.check_in_window, "報到管理")

        self.voting_window = VotingWindow()
        self.tabs.addTab(self.voting_window, "投票")

        main_layout.addWidget(self.tabs, 1)
        central_widget.setLayout(main_layout)

    def apply_system_title_style(self):
        if not self.title_label:
            return
        system_name = self._cfg_get("system_name", "投票系統")
        title_size = self._to_int(self._cfg_get("system_title_font_size", 46), 46)
        self.title_label.setText(system_name)
        self.title_label.setStyleSheet(f"""
            QLabel#SystemTitle {{
                font-family: "Microsoft JhengHei", "Noto Sans TC", sans-serif;
                font-size: {title_size}px;
                font-weight: 900;
                letter-spacing: 2px;
                color: #F5F7FA;
                background: transparent;
            }}
        """)

    def _load_logo(self):
        candidates = [
            Path("assets/custom_logo.png"),
            Path("assets/logo_gold.png"),
            Path("assets/logo.png"),
        ]
        logo_path = next((p for p in candidates if p.exists()), None)

        if not logo_path:
            self.logo_overlay.hide()
            return

        pix = QPixmap(str(logo_path))
        if pix.isNull():
            self.logo_overlay.hide()
            return

        self.logo_overlay.setPixmap(
            pix.scaled(88, 88, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
        self.logo_overlay.show()

    def _position_logo_overlay(self):
        margin_top = 28
        margin_right = 20
        x = self.width() - self.logo_overlay.width() - margin_right
        y = margin_top
        self.logo_overlay.move(max(0, x), max(0, y))
        self.logo_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_logo_overlay()

    def change_logo(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "選擇 Logo 圖片", "",
                "圖片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
            )
            if not file_path:
                return

            assets_dir = Path("assets")
            assets_dir.mkdir(parents=True, exist_ok=True)
            dst = assets_dir / "custom_logo.png"
            shutil.copyfile(Path(file_path), dst)

            self._load_logo()
            self._position_logo_overlay()
            QMessageBox.information(self, "成功", f"Logo 已更新：{dst.as_posix()}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"更換 Logo 失敗：{e}")

    def apply_professional_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1f2229;
                color: #e8eaed;
                font-family: "Microsoft JhengHei", "Noto Sans TC", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            #HeaderBar {
                background-color: #1c212b;
                border: 1px solid #313845;
                border-radius: 8px;
            }
            #LogoOverlay { background-color: #1f2229; border: none; }
        """)

    def create_menu_bar(self):
        menubar = self.menuBar()

        system_menu = menubar.addMenu("系統")
        system_menu.addAction("系統設置").triggered.connect(self.open_setup_dialog)
        system_menu.addAction("更換 Logo").triggered.connect(self.change_logo)
        system_menu.addSeparator()
        system_menu.addAction("退出").triggered.connect(self.close)

        household_menu = menubar.addMenu("住戶管理")
        household_menu.addAction("管理住戶（戶號/姓名）").triggered.connect(self.manage_households)

        voting_menu = menubar.addMenu("投票")
        voting_menu.addAction("管理投票案號").triggered.connect(self.open_voting_items_dialog)

        print_menu = menubar.addMenu("列印")
        print_menu.addAction("印報到單 PDF").triggered.connect(self.print_check_in_ballots)
        print_menu.addAction("印投票單 PDF").triggered.connect(self.print_voting_ballots)
        print_menu.addAction("匯出投票結果報表 PDF").triggered.connect(self.export_voting_result_report_pdf)
        print_menu.addSeparator()
        print_menu.addAction("生成條碼圖片").triggered.connect(self.generate_barcodes)

        data_menu = menubar.addMenu("數據")
        data_menu.addAction("導出數據").triggered.connect(self.export_all_data)
        data_menu.addAction("導入數據").triggered.connect(self.open_import_dialog)
        data_menu.addAction("清空數據").triggered.connect(self.clear_all_data)

    def _refresh_all_views(self):
        for obj, fn in [
            (self.check_in_window, "refresh_check_in_list"),
            (self.voting_window, "load_voting_items"),
            (self.voting_window, "refresh_data"),
            (self.results_window, "refresh_results"),
        ]:
            try:
                if obj and hasattr(obj, fn):
                    getattr(obj, fn)()
            except Exception:
                pass

    def open_setup_dialog(self):
        dialog = SetupDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()

    def on_settings_changed(self):
        self.update_window_title()
        self.apply_system_title_style()
        try:
            if hasattr(self.check_in_window, "refresh_check_in_list"):
                self.check_in_window.refresh_check_in_list()
        except Exception:
            pass

    def manage_households(self):
        dialog = HouseholdManagerDialog(self)
        dialog.exec()
        self._refresh_all_views()

    def open_voting_items_dialog(self):
        dialog = VotingItemDialog(self)
        dialog.exec()
        self._refresh_all_views()

    def print_check_in_ballots(self):
        try:
            households = self.db.get_all_households()
            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據，無法生成報到單")
                return

            output_dir = QFileDialog.getExistingDirectory(self, "選擇輸出目錄", "exports")
            if not output_dir:
                return

            printer = CheckInPrinter(output_dir=output_dir)

            if hasattr(printer, "generate_check_in_ballots"):
                pdf_filename = printer.generate_check_in_ballots(households)
            elif hasattr(printer, "generate_pdf"):
                pdf_filename = printer.generate_pdf(households)
            else:
                methods = [m for m in dir(printer) if callable(getattr(printer, m)) and not m.startswith("_")]
                raise AttributeError(f"CheckInPrinter 無可用匯出方法，可用方法: {methods}")

            QMessageBox.information(self, "成功", f"報到單已生成：{pdf_filename}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成報到單失敗: {e}")
            traceback.print_exc()

    def print_voting_ballots(self):
        try:
            voting_data = self.db.get_all_voting_items()
            households = self.db.get_all_households()
            if not voting_data:
                QMessageBox.warning(self, "警告", "沒有投票項目")
                return
            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據")
                return

            pass_percentage = self._cfg_get("meeting_pass_percentage", None)
            if pass_percentage is None:
                pass_percentage = self._cfg_get("pass_percentage", 50.0)
            pass_percentage = float(pass_percentage)

            normalized_households = [
                {
                    "household_id": str(h.get("household_id", "")),
                    "name": str(h.get("name", "")),
                }
                for h in households if str(h.get("household_id", "")).strip()
            ]

            for case in voting_data:
                case.setdefault("meeting_pass_percentage", pass_percentage)
                if not case.get("households"):
                    case["households"] = normalized_households

            output_dir = QFileDialog.getExistingDirectory(self, "選擇輸出目錄", "exports")
            if not output_dir:
                return

            printer = VotingBallotPrinter(output_dir=output_dir)

            if hasattr(printer, "generate_voting_ballots"):
                pdf_filename = printer.generate_voting_ballots(voting_data, households)
            elif hasattr(printer, "generate_pdf"):
                pdf_filename = printer.generate_pdf(voting_data)
            else:
                methods = [m for m in dir(printer) if callable(getattr(printer, m)) and not m.startswith("_")]
                raise AttributeError(f"VotingBallotPrinter 無可用匯出方法，可用方法: {methods}")

            if not pdf_filename or not Path(pdf_filename).exists():
                raise FileNotFoundError(f"投票單未產生檔案，回傳路徑: {pdf_filename}")

            QMessageBox.information(self, "成功", f"投票單已生成：{pdf_filename}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成投票單失敗: {e}")
            traceback.print_exc()

    def export_voting_result_report_pdf(self):
        try:
            voting_data = self.db.get_all_voting_items()
            if not voting_data:
                QMessageBox.warning(self, "警告", "沒有投票項目")
                return

            pass_percentage = self._cfg_get("meeting_pass_percentage", None)
            if pass_percentage is None:
                pass_percentage = self._cfg_get("pass_percentage", 50.0)
            pass_percentage = float(pass_percentage)

            for case in voting_data:
                case.setdefault("meeting_pass_percentage", pass_percentage)

            output_dir = QFileDialog.getExistingDirectory(self, "選擇輸出目錄", "exports")
            if not output_dir:
                return

            printer = VotingResultReportPrinter(output_dir=output_dir)
            pdf_path = printer.generate_pdf(
                voting_data=voting_data,
                filename="voting_result_report.pdf",
                default_pass_percentage=pass_percentage
            )
            QMessageBox.information(self, "成功", f"投票結果報表已生成：\n{pdf_path}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯出投票結果報表失敗: {e}")

    def generate_barcodes(self):
        try:
            households = self.db.get_all_households()
            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據，無法生成條碼")
                return
            output_dir = QFileDialog.getExistingDirectory(self, "選擇條碼輸出目錄", "exports/barcodes")
            if not output_dir:
                return
            generator = BarcodeGenerator(output_dir=output_dir)
            generator.generate_household_barcodes_batch([(h["household_id"], h["name"]) for h in households], show_text=True)
            QMessageBox.information(self, "成功", f"條碼圖片已生成\n位置: {output_dir}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"生成條碼失敗: {e}")

    def export_all_data(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "導出完整資料包", "exports/full_data.xlsx", "Excel 文件 (*.xlsx)")
            if not file_path:
                return
            if not file_path.lower().endswith(".xlsx"):
                file_path += ".xlsx"
            export_path = self.db.export_data(file_path)
            if export_path:
                QMessageBox.information(self, "成功", f"完整資料包已導出：\n{export_path}")
            else:
                QMessageBox.critical(self, "錯誤", "完整資料包導出失敗")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"數據導出失敗: {e}\n\n{traceback.format_exc()}")

    def open_import_dialog(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "導入數據（Excel）", "", "Excel 文件 (*.xlsx)")
            if not file_path:
                return
            ok = self.db.import_excel_data(file_path)
            if ok:
                self._refresh_all_views()
                QMessageBox.information(self, "成功", f"📥 數據已導入\n\n來源: {file_path}")
            else:
                QMessageBox.critical(self, "錯誤", "數據導入失敗")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"數據導入失敗: {e}\n\n{traceback.format_exc()}")

    def clear_all_data(self):
        reply = QMessageBox.question(
            self, "確認", "確定要清空所有數據嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = self.db.clear_all_data()
            self._refresh_all_views()
            QMessageBox.information(self, "成功", "數據已清空" if ok else "清空數據失敗")
