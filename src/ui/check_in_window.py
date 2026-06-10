"""
報到窗口
"""
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.backend.database import Database
from src.backend.utils import format_datetime


class CheckInWindow(QWidget):
    """報到窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("報到管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        stats_layout = QHBoxLayout()
        self.total_label = QLabel("預期出席: 0")
        self.checked_label = QLabel("已報到: 0")
        self.percentage_label = QLabel("出席率: 0%")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.checked_label)
        stats_layout.addWidget(self.percentage_label)
        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("掃描戶號條碼:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描戶號條碼...")
        self.barcode_input.returnPressed.connect(self.process_check_in)
        scan_layout.addWidget(self.barcode_input)
        main_layout.addLayout(scan_layout)

        self.check_in_table = QTableWidget()
        self.check_in_table.setColumnCount(5)
        self.check_in_table.setHorizontalHeaderLabels(["戶號", "姓名", "條碼", "報到時間", "狀態"])
        self.check_in_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.check_in_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.check_in_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.check_in_table)

        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_check_in_list)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("導出報到記錄")
        export_button.clicked.connect(self.export_check_in_data)
        button_layout.addWidget(export_button)

        clear_button = QPushButton("清空數據")
        clear_button.clicked.connect(self.clear_check_in_data)
        button_layout.addWidget(clear_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        self.refresh_check_in_list()

    def process_check_in(self):
        barcode = self.barcode_input.text().strip()
        if not barcode:
            QMessageBox.warning(self, "警告", "請輸入戶號條碼")
            return

        voter = self.db.get_voter(barcode)
        if not voter:
            QMessageBox.critical(self, "錯誤", f"條碼 {barcode} 不存在")
            self.barcode_input.clear()
            return

        if self.db.check_in_voter(voter['household_id'], voter['barcode']):
            QMessageBox.information(self, "成功", f"戶號 {voter['household_id']}（{voter['name']}）報到成功")
            self.barcode_input.clear()
            self.refresh_check_in_list()
        else:
            QMessageBox.critical(self, "錯誤", "報到失敗，此戶號已報到或發生錯誤")
            self.barcode_input.clear()

    def refresh_check_in_list(self):
        stats = self.db.get_check_in_stats()
        if stats:
            self.total_label.setText(f"預期出席: {stats.get('total_expected', 0)}")
            self.checked_label.setText(f"已報到: {stats.get('checked_in', 0)}")
            self.percentage_label.setText(f"出席率: {stats.get('percentage', 0)}%")

        self.check_in_table.setRowCount(0)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.household_id, v.name, v.barcode, c.checked_in_at, v.status
            FROM voters v
            LEFT JOIN check_in_records c ON v.household_id = c.household_id
            ORDER BY c.checked_in_at DESC, v.household_id ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            row_position = self.check_in_table.rowCount()
            self.check_in_table.insertRow(row_position)
            self.check_in_table.setItem(row_position, 0, QTableWidgetItem(row[0]))
            self.check_in_table.setItem(row_position, 1, QTableWidgetItem(row[1]))
            self.check_in_table.setItem(row_position, 2, QTableWidgetItem(row[2]))
            self.check_in_table.setItem(row_position, 3, QTableWidgetItem(format_datetime(row[3]) if row[3] else "未報到"))
            self.check_in_table.setItem(row_position, 4, QTableWidgetItem(row[4]))

    def export_check_in_data(self):
        if self.db.export_data():
            QMessageBox.information(self, "成功", "數據已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "數據導出失敗")

    def clear_check_in_data(self):
        reply = QMessageBox.question(
            self,
            "確認",
            "確定要清空所有數據嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all_data()
            self.refresh_check_in_list()
            QMessageBox.information(self, "成功", "數據已清空")
