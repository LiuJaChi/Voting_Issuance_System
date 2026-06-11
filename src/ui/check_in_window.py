"""
報到窗口
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from src.backend.database import Database
from src.backend.check_in_printer import CheckInPrinter
from src.backend.utils import format_datetime


class CheckInWindow(QWidget):
    """報到窗口"""
    
    def __init__(self, parent=None):
        """初始化報到窗口"""
        super().__init__(parent)
        self.db = Database()
        self.last_checked_in_household_id = None  # 記錄最後一筆報到的戶號
        
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
    
    def extract_household_id(self, barcode_text: str) -> str:
        """
        從掃描的條碼中提取戶號
        
        條碼可能包含額外的字符，需要提取有效的戶號格式
        戶號格式：數字-數字字母 (例如：06-02F, 06-03A)
        
        Args:
            barcode_text: 掃描的原始條碼文本
            
        Returns:
            提取的戶號，或原始文本（如果無法提取）
        """
        import re
        
        # 戶號格式：2位數字-2位數字+1個字母或2位數字
        # 例如：06-02F, 06-03A
        pattern = r'(\d{1,2}-\d{1,2}[A-Z]?)'
        
        match = re.search(pattern, barcode_text)
        if match:
            return match.group(1)
        
        # 如果找不到標準格式，返回原始文本
        return barcode_text
    
    def is_household_checked_in(self, household_id: str) -> bool:
        """
        檢查住戶是否已報到
        
        Args:
            household_id: 戶號
            
        Returns:
            True 如果已報到，False 如果尚未報到
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT checked_in_at FROM check_in_records 
            WHERE household_id = ?
        """, (household_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def process_check_in(self):
        """處理報到"""
        scanned_code = self.barcode_input.text().strip()
        
        if not scanned_code:
            QMessageBox.warning(self, "警告", "請輸入條碼或戶號")
            return
        
        # 從條碼中提取戶號
        household_id = self.extract_household_id(scanned_code)
        
        # 查找住戶（使用戶號）
        household = self.db.get_household(household_id)
        if not household:
            QMessageBox.critical(
                self, "錯誤", 
                f"戶號 {household_id} 不存在\n\n掃描結果: {scanned_code}"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 檢查是否已報到
        if self.is_household_checked_in(household_id):
            # 重複報到 - 提醒但不執行
            QMessageBox.warning(
                self, "重複報到", 
                f"住戶 {household['name']} (戶號: {household_id}) 已報到\n\n請掃描下一筆資料"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 執行報到
        if self.db.check_in_household(household_id):
            # 正常報到 - 不顯示對話框，立即返回掃描區
            self.last_checked_in_household_id = household_id
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            self.refresh_check_in_list()
        else:
            # 報到失敗
            QMessageBox.critical(self, "錯誤", "報到失敗，請聯繫管理員")
            self.barcode_input.clear()
            self.barcode_input.setFocus()
    
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
            SELECT h.household_id, h.name, c.checked_in_at
            FROM households h
            LEFT JOIN check_in_records c ON h.household_id = c.household_id
            ORDER BY h.household_id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # 黃色背景色
        yellow_brush = QColor(255, 255, 0)  # 黃色
        
        for row in rows:
            row_position = self.check_in_table.rowCount()
            self.check_in_table.insertRow(row_position)
            
            # 戶號
            household_id_item = QTableWidgetItem(row[0])
            # 住戶姓名
            name_item = QTableWidgetItem(row[1])
            
            # 報到時間 - 只顯示時間部分 (HH:MM:SS)
            if row[2]:
                # 如果有報到時間，只提取時間部分
                try:
                    checked_in_at = row[2].split(' ')[1] if ' ' in row[2] else row[2]
                except:
                    checked_in_at = row[2]
            else:
                checked_in_at = ""
            
            time_item = QTableWidgetItem(checked_in_at)
            
            # 狀態 - 已報到 或 尚未報到
            status = "已報到" if row[2] else "尚未報到"
            status_item = QTableWidgetItem(status)
            
            # 如果是最後一筆報到資料，設置黃色背景
            if row[0] == self.last_checked_in_household_id:
                household_id_item.setBackground(yellow_brush)
                name_item.setBackground(yellow_brush)
                time_item.setBackground(yellow_brush)
                status_item.setBackground(yellow_brush)
            
            self.check_in_table.setItem(row_position, 0, household_id_item)
            self.check_in_table.setItem(row_position, 1, name_item)
            self.check_in_table.setItem(row_position, 2, time_item)
            self.check_in_table.setItem(row_position, 3, status_item)
    
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
            self.last_checked_in_household_id = None
            self.refresh_check_in_list()
            QMessageBox.information(self, "成功", "數據已清空")
