"""
報到單打印對話框

功能：
- 選擇要打印報到單的住戶
- 生成報到單 PDF（條碼 + 戶號 + 姓名）
- 打印或保存 PDF
"""
import subprocess
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QCheckBox, QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt

from src.backend.database import Database
from src.backend.check_in_printer import CheckInPrinter


class CheckInPrinterDialog(QDialog):
    """報到單打印對話框"""

    def __init__(self, parent=None):
        """初始化報到單打印對話框"""
        super().__init__(parent)
        self.setWindowTitle("報到單打印")
        self.setGeometry(100, 100, 650, 550)
        self.db = Database()
        self.printer = CheckInPrinter()
        self.init_ui()

    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()

        # 說明
        info_label = QLabel(
            "選擇要生成報到單的住戶，每張報到單包含戶號、姓名和 Code128 條碼。\n"
            "輸出格式：PDF（每頁 A4，2 欄排列）"
        )
        info_label.setStyleSheet("color: #555;")
        main_layout.addWidget(info_label)

        # 搜尋與全選
        ctrl_layout = QHBoxLayout()

        self.select_all_cb = QCheckBox("全選")
        self.select_all_cb.clicked.connect(self.toggle_select_all)
        ctrl_layout.addWidget(self.select_all_cb)

        ctrl_layout.addWidget(QLabel("搜尋:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("輸入戶號或姓名...")
        self.search_input.textChanged.connect(self.filter_households)
        ctrl_layout.addWidget(self.search_input)

        ctrl_layout.addStretch()
        main_layout.addLayout(ctrl_layout)

        # 住戶列表（可勾選）
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
        main_layout.addWidget(self.households_table)

        # 輸出文件名
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("輸出文件名:"))
        self.output_filename = QLineEdit()
        self.output_filename.setText("check_in_ballots.pdf")
        output_layout.addWidget(self.output_filename)
        main_layout.addLayout(output_layout)

        # 按鈕佈局
        button_layout = QHBoxLayout()

        generate_button = QPushButton("生成報到單 PDF")
        generate_button.setMinimumHeight(40)
        generate_button.setStyleSheet("background-color: #2196F3; color: white; font-size: 11pt;")
        generate_button.clicked.connect(self.generate_pdf)
        button_layout.addWidget(generate_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self._all_households = []
        self.load_households()

    def load_households(self):
        """載入住戶列表"""
        self._all_households = self.db.get_all_households()
        self._display_households(self._all_households)

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

    def toggle_select_all(self):
        """切換全選/全不選"""
        checked = self.select_all_cb.isChecked()
        for row in range(self.households_table.rowCount()):
            cb = self.households_table.cellWidget(row, 0)
            if cb:
                cb.setChecked(checked)

    def filter_households(self, text: str):
        """根據搜尋文字過濾住戶"""
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
        """獲取已勾選的住戶列表"""
        selected = []
        for row in range(self.households_table.rowCount()):
            cb = self.households_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                household_id = self.households_table.item(row, 1).text()
                name = self.households_table.item(row, 2).text()
                selected.append((household_id, name))
        return selected

    def generate_pdf(self):
        """生成報到單 PDF"""
        selected = self.get_selected_households()
        if not selected:
            QMessageBox.warning(self, "警告", "請至少勾選一個住戶")
            return

        filename = self.output_filename.text().strip()
        if not filename:
            filename = "check_in_ballots.pdf"
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        try:
            output_path = self.printer.generate_pdf(selected, filename)
            abs_path = str(Path(output_path).resolve())

            reply = QMessageBox.information(
                self, "成功",
                f"報到單 PDF 已生成！\n\n"
                f"共 {len(selected)} 張報到單\n"
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
        except Exception as e:
            QMessageBox.information(self, "提示", f"請手動打開文件：{path}")
