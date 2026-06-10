"""
投票單打印對話框

功能：
- 選擇住戶和投票案號
- 生成投票單 PDF（A4，每頁 8 張）
- 每張投票單包含：戶號、姓名、案號、條碼、投票選項
"""
import subprocess
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QCheckBox, QLineEdit, QTabWidget, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt

from src.backend.database import Database
from src.backend.voting_ballot_printer import VotingBallotPrinter


class VotingBallotPrinterDialog(QDialog):
    """投票單打印對話框"""

    def __init__(self, parent=None):
        """初始化投票單打印對話框"""
        super().__init__(parent)
        self.setWindowTitle("投票單打印")
        self.setGeometry(100, 100, 800, 600)
        self.db = Database()
        self.printer = VotingBallotPrinter()
        self.init_ui()

    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()

        # 說明
        info_label = QLabel(
            "選擇住戶和投票案號，生成投票單 PDF。\n"
            "每頁 A4 排列 8 張投票單（2 欄 × 4 列），每張包含條碼和投票選項。"
        )
        info_label.setStyleSheet("color: #555;")
        main_layout.addWidget(info_label)

        # 使用 Tab 頁切換選擇模式
        tab_widget = QTabWidget()

        # ── 全部住戶 × 全部案號 ──
        all_tab = QWidget()
        all_layout = QVBoxLayout()
        all_layout.addWidget(QLabel(
            "為所有住戶生成所有案號的投票單，輸出為單一 PDF 文件。"
        ))

        all_output_layout = QHBoxLayout()
        all_output_layout.addWidget(QLabel("輸出文件名:"))
        self.all_output_filename = QLineEdit()
        self.all_output_filename.setText("voting_ballots_all.pdf")
        all_output_layout.addWidget(self.all_output_filename)
        all_layout.addLayout(all_output_layout)
        all_layout.addStretch()
        all_tab.setLayout(all_layout)
        tab_widget.addTab(all_tab, "批量：全部住戶 × 全部案號")

        # ── 選擇住戶 × 選擇案號 ──
        select_tab = QWidget()
        select_layout = QHBoxLayout()

        # 住戶選擇
        household_group = QGroupBox("選擇住戶")
        household_group_layout = QVBoxLayout()

        hh_ctrl = QHBoxLayout()
        self.hh_select_all_cb = QCheckBox("全選")
        self.hh_select_all_cb.clicked.connect(self.toggle_select_all_households)
        hh_ctrl.addWidget(self.hh_select_all_cb)
        self.hh_search = QLineEdit()
        self.hh_search.setPlaceholderText("搜尋戶號/姓名...")
        self.hh_search.textChanged.connect(self.filter_households)
        hh_ctrl.addWidget(self.hh_search)
        household_group_layout.addLayout(hh_ctrl)

        self.households_table = QTableWidget()
        self.households_table.setColumnCount(3)
        self.households_table.setHorizontalHeaderLabels(["勾選", "戶號", "姓名"])
        self.households_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.households_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.households_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        household_group_layout.addWidget(self.households_table)
        household_group.setLayout(household_group_layout)
        select_layout.addWidget(household_group)

        # 案號選擇
        case_group = QGroupBox("選擇案號")
        case_group_layout = QVBoxLayout()

        cn_ctrl = QHBoxLayout()
        self.cn_select_all_cb = QCheckBox("全選")
        self.cn_select_all_cb.clicked.connect(self.toggle_select_all_cases)
        cn_ctrl.addWidget(self.cn_select_all_cb)
        cn_ctrl.addStretch()
        case_group_layout.addLayout(cn_ctrl)

        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(3)
        self.cases_table.setHorizontalHeaderLabels(["勾選", "案號", "項目名稱"])
        self.cases_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.cases_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.cases_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        case_group_layout.addWidget(self.cases_table)
        case_group.setLayout(case_group_layout)
        select_layout.addWidget(case_group)

        select_tab.setLayout(select_layout)
        tab_widget.addTab(select_tab, "選擇住戶和案號")

        main_layout.addWidget(tab_widget)
        self._tab_widget = tab_widget

        # 輸出文件名（選擇模式）
        select_output_layout = QHBoxLayout()
        select_output_layout.addWidget(QLabel("選擇模式輸出文件名:"))
        self.select_output_filename = QLineEdit()
        self.select_output_filename.setText("voting_ballots_selected.pdf")
        select_output_layout.addWidget(self.select_output_filename)
        main_layout.addLayout(select_output_layout)

        # 按鈕佈局
        button_layout = QHBoxLayout()

        generate_button = QPushButton("生成投票單 PDF")
        generate_button.setMinimumHeight(40)
        generate_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 11pt;")
        generate_button.clicked.connect(self.generate_pdf)
        button_layout.addWidget(generate_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self._all_households = []
        self.load_data()

    def load_data(self):
        """載入住戶和案號資料"""
        self._all_households = self.db.get_all_households()
        self._display_households(self._all_households)

        voting_items = self.db.get_all_voting_items()
        self.cases_table.setRowCount(0)
        for row_idx, item in enumerate(voting_items):
            self.cases_table.insertRow(row_idx)
            cb = QCheckBox()
            cb.setChecked(True)
            self.cases_table.setCellWidget(row_idx, 0, cb)
            self.cases_table.setItem(row_idx, 1, QTableWidgetItem(item['case_number']))
            self.cases_table.setItem(row_idx, 2, QTableWidgetItem(item['name']))

    def _display_households(self, households):
        """顯示住戶列表"""
        self.households_table.setRowCount(0)
        for row_idx, h in enumerate(households):
            self.households_table.insertRow(row_idx)
            cb = QCheckBox()
            cb.setChecked(True)
            self.households_table.setCellWidget(row_idx, 0, cb)
            self.households_table.setItem(row_idx, 1, QTableWidgetItem(h['household_id']))
            self.households_table.setItem(row_idx, 2, QTableWidgetItem(h['name']))

    def toggle_select_all_households(self):
        checked = self.hh_select_all_cb.isChecked()
        for row in range(self.households_table.rowCount()):
            cb = self.households_table.cellWidget(row, 0)
            if cb:
                cb.setChecked(checked)

    def toggle_select_all_cases(self):
        checked = self.cn_select_all_cb.isChecked()
        for row in range(self.cases_table.rowCount()):
            cb = self.cases_table.cellWidget(row, 0)
            if cb:
                cb.setChecked(checked)

    def filter_households(self, text: str):
        text = text.strip().lower()
        if not text:
            self._display_households(self._all_households)
            return
        filtered = [
            h for h in self._all_households
            if text in h['household_id'].lower() or text in h['name'].lower()
        ]
        self._display_households(filtered)

    def get_selected_households(self):
        """獲取已勾選的住戶"""
        selected = []
        for row in range(self.households_table.rowCount()):
            cb = self.households_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                household_id = self.households_table.item(row, 1).text()
                name = self.households_table.item(row, 2).text()
                selected.append((household_id, name))
        return selected

    def get_selected_cases(self):
        """獲取已勾選的案號"""
        selected = []
        for row in range(self.cases_table.rowCount()):
            cb = self.cases_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                case_number = self.cases_table.item(row, 1).text()
                case_name = self.cases_table.item(row, 2).text()
                selected.append((case_number, case_name))
        return selected

    def generate_pdf(self):
        """生成投票單 PDF"""
        current_tab = self._tab_widget.currentIndex()

        if current_tab == 0:
            # 全部住戶 × 全部案號
            households = [(h['household_id'], h['name']) for h in self._all_households]
            cases = [
                (item['case_number'], item['name'])
                for item in self.db.get_all_voting_items()
            ]
            filename = self.all_output_filename.text().strip() or "voting_ballots_all.pdf"
        else:
            # 選擇模式
            households = self.get_selected_households()
            cases = self.get_selected_cases()
            filename = self.select_output_filename.text().strip() or "voting_ballots_selected.pdf"

        if not households:
            QMessageBox.warning(self, "警告", "請至少選擇一個住戶")
            return
        if not cases:
            QMessageBox.warning(self, "警告", "請至少選擇一個投票案號")
            return

        if not filename.endswith(".pdf"):
            filename += ".pdf"

        total = len(households) * len(cases)

        try:
            output_path = self.printer.generate_pdf_for_all(households, cases, filename)
            abs_path = str(Path(output_path).resolve())

            reply = QMessageBox.information(
                self, "成功",
                f"投票單 PDF 已生成！\n\n"
                f"共 {len(households)} 戶 × {len(cases)} 個案號 = {total} 張投票單\n"
                f"保存位置：{abs_path}\n\n"
                f"是否立即打開文件？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._open_file(abs_path)

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"PDF 生成失敗：{e}")

    def _open_file(self, path: str):
        """用系統默認程序打開文件"""
        try:
            if sys.platform == 'win32':
                import os
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception:
            QMessageBox.information(self, "提示", f"請手動打開文件：{path}")
