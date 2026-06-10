"""
投票項目管理對話框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt

from src.backend.database import Database


class VotingItemDialog(QDialog):
    """投票項目管理對話框"""

    def __init__(self, parent=None):
        """初始化投票項目管理對話框"""
        super().__init__(parent)
        self.setWindowTitle("投票項目管理")
        self.setGeometry(100, 100, 650, 400)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()

        # 新增項目
        add_layout = QHBoxLayout()

        add_layout.addWidget(QLabel("案號:"))
        self.case_number_input = QLineEdit()
        self.case_number_input.setPlaceholderText("例如: 001")
        self.case_number_input.setMaximumWidth(80)
        add_layout.addWidget(self.case_number_input)

        add_layout.addWidget(QLabel("項目名稱:"))
        self.item_name_input = QLineEdit()
        self.item_name_input.setPlaceholderText("例如: 社區費用調整案")
        add_layout.addWidget(self.item_name_input)

        add_layout.addWidget(QLabel("描述:"))
        self.item_desc_input = QLineEdit()
        add_layout.addWidget(self.item_desc_input)

        add_button = QPushButton("新增")
        add_button.clicked.connect(self.add_voting_item)
        add_layout.addWidget(add_button)

        main_layout.addLayout(add_layout)

        # 項目列表表
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(
            ["案號", "項目名稱", "描述", "操作"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        main_layout.addWidget(self.items_table)

        # 按鈕佈局
        button_layout = QHBoxLayout()

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_items)
        button_layout.addWidget(refresh_button)

        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.refresh_items()

    def add_voting_item(self):
        """添加投票項目"""
        case_number = self.case_number_input.text().strip()
        name = self.item_name_input.text().strip()
        description = self.item_desc_input.text().strip()

        if not case_number:
            QMessageBox.warning(self, "警告", "請輸入案號")
            return
        if not name:
            QMessageBox.warning(self, "警告", "請輸入項目名稱")
            return

        if self.db.add_voting_item(case_number, name, description or None):
            QMessageBox.information(self, "成功", f"案號 {case_number} 已添加")
            self.case_number_input.clear()
            self.item_name_input.clear()
            self.item_desc_input.clear()
            self.refresh_items()
        else:
            QMessageBox.critical(self, "錯誤", f"案號 {case_number} 已存在或添加失敗")

    def refresh_items(self):
        """刷新項目列表"""
        self.items_table.setRowCount(0)
        items = self.db.get_all_voting_items()

        for row_idx, item in enumerate(items):
            self.items_table.insertRow(row_idx)
            self.items_table.setItem(row_idx, 0, QTableWidgetItem(item['case_number']))
            self.items_table.setItem(row_idx, 1, QTableWidgetItem(item['name']))
            self.items_table.setItem(row_idx, 2, QTableWidgetItem(item.get('description') or ""))

            delete_button = QPushButton("刪除")
            delete_button.clicked.connect(
                lambda checked, cn=item['case_number']: self.delete_item(cn)
            )
            self.items_table.setCellWidget(row_idx, 3, delete_button)

    def delete_item(self, case_number: str):
        """刪除項目"""
        reply = QMessageBox.question(
            self, "確認", f"確定要刪除案號 {case_number} 嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_voting_item(case_number):
                self.refresh_items()
                QMessageBox.information(self, "成功", "項目已刪除")
            else:
                QMessageBox.critical(self, "錯誤", "刪除失敗")
