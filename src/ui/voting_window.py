"""
投票窗口
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.backend.database import Database
from src.backend.utils import parse_voting_ballot_barcode, normalize_vote
from src.backend.config_manager import ConfigManager


class VotingWindow(QWidget):
    """投票窗口（掃描投票單條碼，記錄投票）"""

    def __init__(self, parent=None):
        """初始化投票窗口"""
        super().__init__(parent)
        self.db = Database()
        self.config_manager = ConfigManager()
        self._current_household_id = None
        self._current_case_number = None
        self._current_household_name = None
        self.init_ui()

    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()

        # 標題
        title = QLabel("投票")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # 說明文字
        info_label = QLabel(
            "請掃描投票單條碼（格式：戶號_案號，例如 06-02F_001）\n"
            "掃描後選擇贊成或反對並提交"
        )
        info_label.setStyleSheet("color: #555; font-size: 10pt;")
        main_layout.addWidget(info_label)

        # 條碼掃描輸入
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("掃描投票單條碼:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描投票單條碼...")
        self.barcode_input.returnPressed.connect(self.process_ballot_barcode)
        scan_layout.addWidget(self.barcode_input)
        main_layout.addLayout(scan_layout)

        # 當前投票信息顯示
        info_layout = QHBoxLayout()
        self.current_info_label = QLabel("尚未掃描投票單")
        self.current_info_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        info_layout.addWidget(self.current_info_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)

        # 投票選擇按鈕
        vote_layout = QHBoxLayout()
        self.yes_button = QPushButton("✔ 贊成")
        self.yes_button.setMinimumHeight(50)
        self.yes_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-size: 14pt; }"
            "QPushButton:disabled { background-color: #ccc; color: #888; }"
        )
        self.yes_button.setEnabled(False)
        self.yes_button.clicked.connect(lambda: self.submit_vote('yes'))
        vote_layout.addWidget(self.yes_button)

        self.no_button = QPushButton("✘ 反對")
        self.no_button.setMinimumHeight(50)
        self.no_button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; font-size: 14pt; }"
            "QPushButton:disabled { background-color: #ccc; color: #888; }"
        )
        self.no_button.setEnabled(False)
        self.no_button.clicked.connect(lambda: self.submit_vote('no'))
        vote_layout.addWidget(self.no_button)

        main_layout.addLayout(vote_layout)

        # 分隔線
        main_layout.addSpacing(10)

        # 投票記錄表
        record_title = QLabel("近期投票記錄")
        record_title.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(record_title)

        self.vote_table = QTableWidget()
        self.vote_table.setColumnCount(5)
        self.vote_table.setHorizontalHeaderLabels(
            ["戶號", "姓名", "案號", "投票結果", "投票時間"]
        )
        self.vote_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.vote_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.vote_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.vote_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.vote_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        main_layout.addWidget(self.vote_table)

        # 按鈕佈局
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新記錄")
        refresh_button.clicked.connect(self.refresh_vote_records)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("導出投票數據")
        export_button.clicked.connect(self.export_voting_data)
        button_layout.addWidget(export_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.refresh_vote_records()

    def process_ballot_barcode(self):
        """處理投票單條碼掃描"""
        raw = self.barcode_input.text().strip()
        self.barcode_input.clear()

        if not raw:
            QMessageBox.warning(self, "警告", "請輸入條碼")
            return

        parsed = parse_voting_ballot_barcode(raw)
        if not parsed:
            QMessageBox.critical(
                self, "錯誤",
                f"無法解析投票單條碼：{raw}\n"
                "投票單條碼格式應為「戶號_案號」，例如：06-02F_001"
            )
            return

        household_id, case_number = parsed

        # 驗證住戶存在
        household = self.db.get_household(household_id)
        if not household:
            QMessageBox.critical(self, "錯誤", f"戶號 {household_id} 不存在")
            return

        # 驗證案號存在
        voting_item = self.db.get_voting_item(case_number)
        if not voting_item:
            QMessageBox.critical(self, "錯誤", f"案號 {case_number} 不存在")
            return

        # 檢查是否已投票
        if self.db.has_voted(household_id, case_number):
            QMessageBox.warning(
                self, "提示",
                f"戶號 {household_id} 在案號 {case_number} 已投票"
            )
            return

        # 顯示當前投票信息，啟用投票按鈕
        self._current_household_id = household_id
        self._current_case_number = case_number
        self._current_household_name = household['name']

        self.current_info_label.setText(
            f"戶號：{household_id}  姓名：{household['name']}  "
            f"案號：{case_number}（{voting_item['name']}）"
        )
        self.yes_button.setEnabled(True)
        self.no_button.setEnabled(True)

    def submit_vote(self, vote: str):
        """提交投票"""
        if not self._current_household_id or not self._current_case_number:
            QMessageBox.warning(self, "警告", "請先掃描投票單條碼")
            return

        device_id = self.config_manager.get_config('device_id', 'DEVICE_001')

        if self.db.record_vote(
            self._current_household_id,
            self._current_case_number,
            vote,
            device_id
        ):
            vote_text = "贊成" if vote == 'yes' else "反對"
            QMessageBox.information(
                self, "投票成功",
                f"戶號：{self._current_household_id}\n"
                f"案號：{self._current_case_number}\n"
                f"投票結果：{vote_text}\n投票已記錄！"
            )
            self._reset_current_vote()
            self.refresh_vote_records()
        else:
            QMessageBox.critical(self, "錯誤", "投票記錄失敗，請稍後再試")

    def _reset_current_vote(self):
        """重置當前投票狀態"""
        self._current_household_id = None
        self._current_case_number = None
        self._current_household_name = None
        self.current_info_label.setText("尚未掃描投票單")
        self.yes_button.setEnabled(False)
        self.no_button.setEnabled(False)

    def refresh_vote_records(self):
        """刷新投票記錄表"""
        self.vote_table.setRowCount(0)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.household_id, h.name, v.case_number, v.vote, v.voted_at
            FROM votes v
            LEFT JOIN households h ON v.household_id = h.household_id
            ORDER BY v.voted_at DESC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            row_position = self.vote_table.rowCount()
            self.vote_table.insertRow(row_position)
            self.vote_table.setItem(row_position, 0, QTableWidgetItem(row[0]))
            self.vote_table.setItem(row_position, 1, QTableWidgetItem(row[1] or ""))
            self.vote_table.setItem(row_position, 2, QTableWidgetItem(row[2]))
            vote_display = "贊成" if row[3] == 'yes' else "反對"
            self.vote_table.setItem(row_position, 3, QTableWidgetItem(vote_display))
            self.vote_table.setItem(row_position, 4, QTableWidgetItem(str(row[4] or "")))

    def load_voting_items(self):
        """刷新投票記錄（供外部調用）"""
        self.refresh_vote_records()

    def export_voting_data(self):
        """導出投票數據"""
        if self.db.export_data():
            QMessageBox.information(self, "成功", "投票數據已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "數據導出失敗")
