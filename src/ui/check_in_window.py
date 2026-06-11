"""
報到窗口
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.backend.database import Database
from src.backend.check_in_printer import CheckInPrinter
from src.backend.utils import format_datetime


class CheckInWindow(QWidget):
    """報到窗口"""
    
    def __init__(self, parent=None):
        """初始化報到窗口"""
        super().__init__(parent)
        self.db = Database()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("報到管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 統計信息
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("預期出席: 0")
        self.checked_label = QLabel("已報到: 0")
        self.percentage_label = QLabel("出席率: 0%")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.checked_label)
        stats_layout.addWidget(self.percentage_label)
        stats_layout.addStretch()
        
        main_layout.addLayout(stats_layout)
        
        # 條碼掃描輸入
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("掃描條碼 (戶號):"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描條碼或輸入戶號...")
        self.barcode_input.returnPressed.connect(self.process_check_in)
        scan_layout.addWidget(self.barcode_input)
        
        main_layout.addLayout(scan_layout)
        
        # 報到記錄表
        self.check_in_table = QTableWidget()
        self.check_in_table.setColumnCount(4)
        self.check_in_table.setHorizontalHeaderLabels(
            ["戶號", "住戶姓名", "報到時間", "狀態"]
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        main_layout.addWidget(self.check_in_table)
        
        # 按鈕佈局
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
        
        # 初始化數據
        self.refresh_check_in_list()
    
    def process_check_in(self):
        """處理報到"""
        scanned_code = self.barcode_input.text().strip()
        
        if not scanned_code:
            QMessageBox.warning(self, "警告", "請輸入條碼或戶號")
            return
        
        # 查找住戶（使用戶號）
        household = self.db.get_household(scanned_code)
        if not household:
            QMessageBox.critical(
                self, "錯誤", 
                f"戶號 {scanned_code} 不存在"
            )
            self.barcode_input.clear()
            return
        
        # 執行報到
        if self.db.check_in_household(scanned_code):
            QMessageBox.information(
                self, "成功", 
                f"住戶 {household['name']} (戶號: {scanned_code}) 報到成功"
            )
            self.barcode_input.clear()
            self.refresh_check_in_list()
        else:
            QMessageBox.critical(self, "錯誤", "報到失敗，此住戶已報到或發生錯誤")
            self.barcode_input.clear()
    
    def refresh_check_in_list(self):
        """刷新報到列表"""
        # 更新統計信息
        stats = self.db.get_check_in_stats()
        if stats:
            self.total_label.setText(f"預期出席: {stats.get('total_expected', 0)}")
            self.checked_label.setText(f"已報到: {stats.get('checked_in', 0)}")
            self.percentage_label.setText(f"出席率: {stats.get('percentage', 0)}%")
        
        # 更新表格
        self.check_in_table.setRowCount(0)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 查詢所有住戶及其報到信息
        cursor.execute("""
            SELECT h.household_id, h.name, c.checked_in_at, h.status
            FROM households h
            LEFT JOIN check_in_records c ON h.household_id = c.household_id
            ORDER BY h.household_id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            row_position = self.check_in_table.rowCount()
            self.check_in_table.insertRow(row_position)
            
            # 戶號
            self.check_in_table.setItem(row_position, 0, QTableWidgetItem(row[0]))
            # 住戶姓名
            self.check_in_table.setItem(row_position, 1, QTableWidgetItem(row[1]))
            
            # 報到時間
            checked_in_at = format_datetime(row[2]) if row[2] else "未報到"
            self.check_in_table.setItem(row_position, 2, QTableWidgetItem(checked_in_at))
            # 狀態
            self.check_in_table.setItem(row_position, 3, QTableWidgetItem(row[3] or "pending"))
    
    def export_check_in_data(self):
        """導出報到數據"""
        if self.db.export_data():
            QMessageBox.information(self, "成功", "數據已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "數據導出失敗")
    
    def clear_check_in_data(self):
        """清空報到數據"""
        reply = QMessageBox.question(
            self, "確認", "確定要清空所有數據嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all_data()
            self.refresh_check_in_list()
            QMessageBox.information(self, "成功", "數據已清空")
