"""
投票項目管理對話框
"""
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.backend.database import Database


class VotingItemDialog(QDialog):
    """投票項目管理對話框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("投票項目管理")
        self.setGeometry(100, 100, 720, 420)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("案號:"))
        self.case_number_input = QLineEdit()
        add_layout.addWidget(self.case_number_input)

        add_layout.addWidget(QLabel("項目名稱:"))
        self.item_name_input = QLineEdit()
        add_layout.addWidget(self.item_name_input)

        add_layout.addWidget(QLabel("描述:"))
        self.item_desc_input = QLineEdit()
        add_layout.addWidget(self.item_desc_input)

        add_button = QPushButton("新增")
        add_button.clicked.connect(self.add_voting_item)
        add_layout.addWidget(add_button)
        main_layout.addLayout(add_layout)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["案號", "項目名稱", "描述", "操作"])
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.items_table)

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
        case_number = self.case_number_input.text().strip()
        name = self.item_name_input.text().strip()
        description = self.item_desc_input.text().strip()

        if not case_number or not name:
            QMessageBox.warning(self, "警告", "請輸入案號與項目名稱")
            return

        item_id = self.db.add_voting_item(case_number, name, description)
        if item_id:
            QMessageBox.information(self, "成功", "項目已添加")
            self.case_number_input.clear()
            self.item_name_input.clear()
            self.item_desc_input.clear()
            self.refresh_items()
        else:
            QMessageBox.critical(self, "錯誤", "項目添加失敗，案號可能重複")

    def refresh_items(self):
        self.items_table.setRowCount(0)
        items = self.db.get_voting_items()
        for row_idx, item in enumerate(items):
            self.items_table.insertRow(row_idx)
            self.items_table.setItem(row_idx, 0, QTableWidgetItem(item['case_number']))
            self.items_table.setItem(row_idx, 1, QTableWidgetItem(item['name']))
            self.items_table.setItem(row_idx, 2, QTableWidgetItem(item['description'] or ""))

            delete_button = QPushButton("刪除")
            delete_button.clicked.connect(lambda checked, item_id=item['id']: self.delete_item(item_id))
            self.items_table.setCellWidget(row_idx, 3, delete_button)

    def delete_item(self, item_id: int):
        reply = QMessageBox.question(
            self,
            "確認",
            "確定要刪除此項目嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM voting_items WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            self.refresh_items()
            QMessageBox.information(self, "成功", "項目已刪除")
