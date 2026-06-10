"""
投票窗口
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.backend.database import Database
from src.backend.utils import normalize_vote


class VotingWindow(QWidget):
    """投票窗口"""
    
    def __init__(self, parent=None):
        """初始化投票窗口"""
        super().__init__(parent)
        self.db = Database()
        
        self.current_voter = None
        self.voting_items = []
        
        self.init_ui()
        self.load_voting_items()
    
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
        
        # 條碼掃描輸入
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("掃描條碼:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描條碼開始投票...")
        self.barcode_input.returnPressed.connect(self.process_voter_barcode)
        scan_layout.addWidget(self.barcode_input)
        
        main_layout.addLayout(scan_layout)
        
        # 投票項目表
        self.voting_table = QTableWidget()
        self.voting_table.setColumnCount(3)
        self.voting_table.setHorizontalHeaderLabels(
            ["項目", "投票", "操作"]
        )
        self.voting_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        main_layout.addWidget(self.voting_table)
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.load_voting_items)
        button_layout.addWidget(refresh_button)
        
        export_button = QPushButton("導出投票數據")
        export_button.clicked.connect(self.export_voting_data)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def process_voter_barcode(self):
        """處理投票者條碼"""
        barcode = self.barcode_input.text().strip()
        
        if not barcode:
            QMessageBox.warning(self, "警告", "請輸入條碼")
            return
        
        # 查找投票者
        voter = self.db.get_voter(barcode)
        if not voter:
            QMessageBox.critical(self, "錯誤", f"條碼 {barcode} 不存在")
            self.barcode_input.clear()
            return
        
        # 檢查是否報到
        if voter['status'] != 'checked_in':
            QMessageBox.warning(self, "警告", "請先報到")
            self.barcode_input.clear()
            return
        
        self.current_voter = voter
        self.barcode_input.clear()
        self.refresh_voting_items()
        QMessageBox.information(self, "提示", f"投票者: {voter['voter_id']} 準備投票")
    
    def load_voting_items(self):
        """加載投票項目"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, description FROM voting_items")
        self.voting_items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        self.refresh_voting_items()
    
    def refresh_voting_items(self):
        """刷新投票項目表"""
        self.voting_table.setRowCount(0)
        
        for idx, item in enumerate(self.voting_items):
            self.voting_table.insertRow(idx)
            
            # 項目名稱
            self.voting_table.setItem(idx, 0, QTableWidgetItem(item['name']))
            
            # 投票選項
            vote_combo = QComboBox()
            vote_combo.addItems(["-- 選擇投票 --", "贊成", "反對"])
            self.voting_table.setCellWidget(idx, 1, vote_combo)
            
            # 操作按鈕
            vote_button = QPushButton("投票")
            vote_button.clicked.connect(
                lambda checked, item_id=item['id'], row=idx: self.submit_vote(item_id, row)
            )
            self.voting_table.setCellWidget(idx, 2, vote_button)
    
    def submit_vote(self, item_id: int, row: int):
        """提交投票"""
        if not self.current_voter:
            QMessageBox.warning(self, "警告", "請先掃描條碼")
            return
        
        vote_combo = self.voting_table.cellWidget(row, 1)
        vote_text = vote_combo.currentText()
        
        if vote_text == "-- 選擇投票 --":
            QMessageBox.warning(self, "警告", "請選擇投票選項")
            return
        
        vote = normalize_vote(vote_text)
        
        if self.db.record_vote(self.current_voter['voter_id'], item_id, vote):
            QMessageBox.information(self, "成功", "投票已記錄")
            vote_combo.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, "錯誤", "投票記錄失敗")
    
    def export_voting_data(self):
        """導出投票數據"""
        if self.db.export_data():
            QMessageBox.information(self, "成功", "投票數據已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "數據導出失敗")
