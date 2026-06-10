"""
投票窗口
"""
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
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
from src.backend.utils import normalize_vote


class VotingWindow(QWidget):
    """投票窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.current_voter = None
        self.voting_items = []
        self.init_ui()
        self.load_voting_items()

    def init_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("投票")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        self.current_voter_label = QLabel("目前投票人：尚未掃描")
        main_layout.addWidget(self.current_voter_label)

        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("掃描戶號條碼:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描戶號條碼開始投票...")
        self.barcode_input.returnPressed.connect(self.process_voter_barcode)
        scan_layout.addWidget(self.barcode_input)
        main_layout.addLayout(scan_layout)

        self.voting_table = QTableWidget()
        self.voting_table.setColumnCount(4)
        self.voting_table.setHorizontalHeaderLabels(["案號", "項目", "投票", "操作"])
        self.voting_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.voting_table)

        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.load_voting_items)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("導出投票數據")
        export_button.clicked.connect(self.export_voting_data)
        button_layout.addWidget(export_button)

        clear_button = QPushButton("清除目前投票人")
        clear_button.clicked.connect(self.clear_current_voter)
        button_layout.addWidget(clear_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def clear_current_voter(self):
        self.current_voter = None
        self.current_voter_label.setText("目前投票人：尚未掃描")
        self.refresh_voting_items()

    def process_voter_barcode(self):
        barcode = self.barcode_input.text().strip()
        if not barcode:
            QMessageBox.warning(self, "警告", "請輸入戶號條碼")
            return

        voter = self.db.get_voter(barcode)
        if not voter:
            QMessageBox.critical(self, "錯誤", f"條碼 {barcode} 不存在")
            self.barcode_input.clear()
            return

        if voter['status'] != 'checked_in':
            QMessageBox.warning(self, "警告", "請先完成報到")
            self.barcode_input.clear()
            return

        self.current_voter = voter
        self.current_voter_label.setText(f"目前投票人：{voter['household_id']}（{voter['name']}）")
        self.barcode_input.clear()
        self.refresh_voting_items()
        QMessageBox.information(self, "提示", f"戶號 {voter['household_id']}（{voter['name']}）可開始投票")

    def load_voting_items(self):
        self.voting_items = self.db.get_voting_items()
        self.refresh_voting_items()

    def refresh_voting_items(self):
        self.voting_table.setRowCount(0)
        voted_item_ids = set()
        if self.current_voter:
            voted_item_ids = set(self.db.get_voted_item_ids(self.current_voter['household_id']))

        for idx, item in enumerate(self.voting_items):
            self.voting_table.insertRow(idx)
            self.voting_table.setItem(idx, 0, QTableWidgetItem(item['case_number']))
            self.voting_table.setItem(idx, 1, QTableWidgetItem(item['name']))

            vote_combo = QComboBox()
            vote_combo.addItems(["-- 選擇投票 --", "贊成", "反對"])
            already_voted = item['id'] in voted_item_ids
            vote_combo.setEnabled(self.current_voter is not None and not already_voted)
            self.voting_table.setCellWidget(idx, 2, vote_combo)

            vote_button = QPushButton("已投票" if already_voted else "投票")
            vote_button.setEnabled(self.current_voter is not None and not already_voted)
            vote_button.clicked.connect(lambda checked, item_id=item['id'], row=idx: self.submit_vote(item_id, row))
            self.voting_table.setCellWidget(idx, 3, vote_button)

    def submit_vote(self, item_id: int, row: int):
        if not self.current_voter:
            QMessageBox.warning(self, "警告", "請先掃描戶號條碼")
            return

        voted_item_ids = set(self.db.get_voted_item_ids(self.current_voter['household_id']))
        if item_id in voted_item_ids:
            QMessageBox.warning(self, "警告", "此戶號對該案號已投過票")
            self.refresh_voting_items()
            return

        vote_combo = self.voting_table.cellWidget(row, 2)
        vote_text = vote_combo.currentText()
        if vote_text == "-- 選擇投票 --":
            QMessageBox.warning(self, "警告", "請選擇投票選項")
            return

        vote = normalize_vote(vote_text)
        if self.db.record_vote(self.current_voter['household_id'], item_id, vote):
            QMessageBox.information(self, "成功", "投票已記錄")
            self.refresh_voting_items()
        else:
            QMessageBox.critical(self, "錯誤", "投票記錄失敗，可能是重複投票")
            self.refresh_voting_items()

    def export_voting_data(self):
        if self.db.export_data():
            QMessageBox.information(self, "成功", "投票數據已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "數據導出失敗")
