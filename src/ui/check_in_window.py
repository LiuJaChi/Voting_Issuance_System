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
from src.backend.barcode_generator import BarcodeGenerator
from src.backend.utils import format_datetime


class CheckInWindow(QWidget):
    """報到窗口"""
    
    def __init__(self, parent=None):
        """初始化報到窗口"""
        super().__init__(parent)
        self.db = Database()
        self.barcode_gen = BarcodeGenerator()
        # 構建 EAN-13 到戶號的反向映射
        self.ean13_to_household_map = self._build_ean13_map()
        
        self.init_ui()
    
    def _build_ean13_map(self) -> dict:
        """
        構建 EAN-13 編碼到戶號的映射表
        
        Returns:
            {ean13_code: household_id, ...}
        """
        mapping = {}
        
        # 獲取所有戶號
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT household_id FROM voters WHERE household_id IS NOT NULL")
            households = cursor.fetchall()
            conn.close()
            
            # 為每個戶號生成 EAN-13 編碼
            for (household_id,) in households:
                ean13 = self.barcode_gen._convert_to_ean13(household_id)
                mapping[ean13] = household_id
                
        except Exception as e:
            print(f"構建映射表失敗: {e}")
        
        return mapping
    
    def _convert_ean13_to_household_id(self, ean13_code: str) -> str:
        """
        將 EAN-13 編碼轉換回戶號
        
        Args:
            ean13_code: EAN-13 編碼（例如：0600266100010）
        
        Returns:
            戶號（例如：06-02F），如果找不到則返回原值
        """
        return self.ean13_to_household_map.get(ean13_code, ean13_code)
    
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
        scan_layout.addWidget(QLabel("掃描條碼:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描條碼...")
        self.barcode_input.returnPressed.connect(self.process_check_in)
        scan_layout.addWidget(self.barcode_input)
        
        main_layout.addLayout(scan_layout)
        
        # 報到記錄表
        self.check_in_table = QTableWidget()
        self.check_in_table.setColumnCount(4)
        self.check_in_table.setHorizontalHeaderLabels(
            ["投票者ID", "條碼", "報到時間", "狀態"]
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
            QMessageBox.warning(self, "警告", "請輸入條碼")
            return
        
        # 嘗試轉換 EAN-13 編碼到戶號
        # 如果掃碼結果是 13 位數字，說明是 EAN-13 編碼，需要轉換
        household_id = self._convert_ean13_to_household_id(scanned_code)
        
        # 查找投票者（使用戶號或原始掃碼值）
        voter = self.db.get_voter(household_id)
        if not voter:
            # 如果用轉換後的戶號找不到，嘗試用原始掃碼值
            voter = self.db.get_voter(scanned_code)
            if not voter:
                QMessageBox.critical(
                    self, "錯誤", 
                    f"條碼 {scanned_code} 不存在\n"
                    f"轉換後: {household_id}"
                )
                self.barcode_input.clear()
                return
            household_id = scanned_code
        
        # 執行報到
        if self.db.check_in_voter(voter['voter_id'], household_id):
            QMessageBox.information(
                self, "成功", 
                f"投票者 {voter['voter_id']} (戶號: {household_id}) 報到成功"
            )
            self.barcode_input.clear()
            self.refresh_check_in_list()
        else:
            QMessageBox.critical(self, "錯誤", "報到失敗，此投票者已報到或發生錯誤")
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
        
        cursor.execute("""
            SELECT v.voter_id, v.barcode, c.checked_in_at, v.status
            FROM voters v
            LEFT JOIN check_in_records c ON v.voter_id = c.voter_id
            ORDER BY c.checked_in_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            row_position = self.check_in_table.rowCount()
            self.check_in_table.insertRow(row_position)
            
            self.check_in_table.setItem(row_position, 0, QTableWidgetItem(row[0]))
            self.check_in_table.setItem(row_position, 1, QTableWidgetItem(row[1]))
            
            checked_in_at = format_datetime(row[2]) if row[2] else "未報到"
            self.check_in_table.setItem(row_position, 2, QTableWidgetItem(checked_in_at))
            self.check_in_table.setItem(row_position, 3, QTableWidgetItem(row[3]))
    
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
