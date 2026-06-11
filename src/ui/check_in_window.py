"""
報到窗口 - 支持條碼映射比對
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from src.backend.database import Database
from src.backend.check_in_printer import CheckInPrinter
from src.backend.utils import format_datetime
from src.backend.input_sanitizer import clean_barcode_input, print_debug_info


class BarcodeSettingDialog(QDialog):
    """條碼對應設置對話框"""
    
    def __init__(self, parent=None, household_id: str = None, existing_barcode: str = None):
        """
        初始化對話框
        
        Args:
            parent: 父窗口
            household_id: 戶號
            existing_barcode: 已存在的條碼
        """
        super().__init__(parent)
        self.household_id = household_id
        self.existing_barcode = existing_barcode
        self.barcode_result = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("設置條碼對應")
        self.setGeometry(100, 100, 400, 150)
        
        layout = QVBoxLayout()
        
        # 戶號標籤
        layout.addWidget(QLabel(f"戶號: {self.household_id}"))
        
        # 條碼輸入
        layout.addWidget(QLabel("請掃描條碼或輸入條碼數據:"))
        self.barcode_input = QLineEdit()
        if self.existing_barcode:
            self.barcode_input.setText(self.existing_barcode)
        self.barcode_input.setPlaceholderText("掃描或輸入條碼...")
        layout.addWidget(self.barcode_input)
        
        # 按鈕
        button_layout = QHBoxLayout()
        
        confirm_btn = QPushButton("確認")
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_barcode(self) -> str:
        """獲取條碼 - 自動清理隱藏字符"""
        raw_input = self.barcode_input.text()
        cleaned = clean_barcode_input(raw_input)
        
        # 調試輸出
        if raw_input != cleaned:
            print_debug_info(raw_input, cleaned)
        
        return cleaned


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
        scan_layout.addWidget(QLabel("掃描條碼:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描條碼進行報到...")
        self.barcode_input.returnPressed.connect(self.process_check_in)
        scan_layout.addWidget(self.barcode_input)
        
        main_layout.addLayout(scan_layout)
        
        # 報到記錄表
        self.check_in_table = QTableWidget()
        self.check_in_table.setColumnCount(4)
        self.check_in_table.setHorizontalHeaderLabels(
            ["戶號", "原始條碼", "報到時間", "狀態"]
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
        """
        處理報到 - 掃描結果與原始條碼做比對
        
        流程：
        1. 清理掃描輸入（移除隱藏字符）
        2. 與 .xlsx 原始條碼列做比對
        3. 如果匹配 → 顯示對應戶號並報到
        4. 如果不匹配 → 顯示錯誤
        """
        # 【關鍵】清理掃描輸入 - 移除所有隱藏字符
        raw_input = self.barcode_input.text()
        scanned_barcode = clean_barcode_input(raw_input)
        
        # 調試輸出
        if raw_input != scanned_barcode:
            print_debug_info(raw_input, scanned_barcode)
        
        if not scanned_barcode:
            QMessageBox.warning(self, "警告", "請掃描條碼")
            return
        
        # 【關鍵】通過原始條碼查詢戶號
        household_id = self.db.get_household_id_by_barcode(scanned_barcode)
        
        if not household_id:
            QMessageBox.critical(
                self, "錯誤", 
                f"條碼 '{scanned_barcode}' 未找到對應戶號\n\n"
                f"請檢查 .xlsx 文件中的原始條碼"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 查找住戶
        household = self.db.get_household(household_id)
        if not household:
            QMessageBox.critical(
                self, "錯誤", 
                f"戶號 {household_id} 不存在"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 檢查是否已報到
        if self.is_household_checked_in(household_id):
            # 重複報到 - 提醒但不執行
            QMessageBox.warning(
                self, "重複報到", 
                f"戶號 {household_id} 已報到\n\n請掃描下一筆資料"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 執行報到
        if self.db.check_in_household(household_id):
            # 正常報到 - 立即返回掃描區
            self.last_checked_in_household_id = household_id
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            self.refresh_check_in_list()
        else:
            # 報到失敗
            QMessageBox.critical(self, "錯誤", "報到失敗，請聯繫管理員")
            self.barcode_input.clear()
            self.barcode_input.setFocus()
    
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
            SELECT h.household_id, c.checked_in_at
            FROM households h
            LEFT JOIN check_in_records c ON h.household_id = c.household_id
            ORDER BY h.household_id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # 黃色背景色
        yellow_brush = QColor(255, 255, 0)
        
        for row in rows:
            row_position = self.check_in_table.rowCount()
            self.check_in_table.insertRow(row_position)
            
            household_id = row[0]
            
            # 戶號
            household_id_item = QTableWidgetItem(household_id)
            
            # 原始條碼
            barcode = self.db.get_barcode_by_household_id(household_id)
            barcode_item = QTableWidgetItem(barcode or "")
            
            # 報到時間 - 只顯示時間部分 (HH:MM:SS)
            if row[1]:
                try:
                    checked_in_at = row[1].split(' ')[1] if ' ' in row[1] else row[1]
                except:
                    checked_in_at = row[1]
            else:
                checked_in_at = ""
            
            time_item = QTableWidgetItem(checked_in_at)
            
            # 狀態 - 已報到 或 尚未報到
            status = "已報到" if row[1] else "尚未報到"
            status_item = QTableWidgetItem(status)
            
            # 如果是最後一筆報到資料，設置黃色背景
            if household_id == self.last_checked_in_household_id:
                household_id_item.setBackground(yellow_brush)
                barcode_item.setBackground(yellow_brush)
                time_item.setBackground(yellow_brush)
                status_item.setBackground(yellow_brush)
            
            self.check_in_table.setItem(row_position, 0, household_id_item)
            self.check_in_table.setItem(row_position, 1, barcode_item)
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
