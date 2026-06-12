"""
報到窗口 - 移除原始條碼欄位，添加進度條和統計圖表
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt6.QtGui import QPainter

from src.backend.database import Database
from src.backend.check_in_printer import CheckInPrinter
from src.backend.utils import format_datetime
from src.backend.input_sanitizer import clean_barcode_input, print_debug_info


class CheckInWindow(QWidget):
    """報到窗口 - 支持進度顯示和圖表統計"""
    
    def __init__(self, parent=None):
        """初始化報到窗口"""
        super().__init__(parent)
        self.db = Database()
        self.last_checked_in_household_id = None  # 記錄最後一筆報到的戶號
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QHBoxLayout()
        
        # ========== 左側布局 ==========
        left_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("報到管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        left_layout.addWidget(title)
        
        # 統計信息
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("預期出席: 0")
        self.checked_label = QLabel("已報到: 0")
        self.percentage_label = QLabel("出席率: 0%")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.checked_label)
        stats_layout.addWidget(self.percentage_label)
        stats_layout.addStretch()
        
        left_layout.addLayout(stats_layout)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        left_layout.addWidget(self.progress_bar)
        
        # 條碼掃描輸入
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("掃描戶號:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描條碼進行報到...")
        self.barcode_input.returnPressed.connect(self.process_check_in)
        scan_layout.addWidget(self.barcode_input)
        
        left_layout.addLayout(scan_layout)
        
        # 報到記錄表 - 移除原始條碼欄位
        self.check_in_table = QTableWidget()
        self.check_in_table.setColumnCount(3)
        self.check_in_table.setHorizontalHeaderLabels(
            ["戶號", "報到時間", "狀態"]
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        left_layout.addWidget(self.check_in_table)
        
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
        left_layout.addLayout(button_layout)
        
        # ========== 右側圖表佈局 ==========
        right_layout = QVBoxLayout()
        
        chart_title = QLabel("報到統計")
        chart_title_font = QFont()
        chart_title_font.setPointSize(12)
        chart_title_font.setBold(True)
        chart_title.setFont(chart_title_font)
        right_layout.addWidget(chart_title)
        
        # 建立圓餅圖
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        right_layout.addWidget(self.chart_view)
        
        # ========== 組合左右布局 ==========
        main_layout.addLayout(left_layout, 2)  # 左側佔 2 份
        main_layout.addLayout(right_layout, 1)  # 右側佔 1 份
        
        self.setLayout(main_layout)
        
        # 初始化數據
        self.refresh_check_in_list()
    
    def create_pie_chart(self, checked_in: int, not_checked_in: int):
        """
        建立圓餅圖表
        
        Args:
            checked_in: 已報到人數
            not_checked_in: 未報到人數
        """
        # 建立圖表
        chart = QChart()
        chart.setTitle("報到狀態分佈")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # 建立圓餅圖數據
        series = QPieSeries()
        
        if checked_in > 0:
            slice_checked = QPieSlice("已報到", checked_in)
            slice_checked.setColor(QColor(76, 175, 80))  # 綠色
            slice_checked.setLabelVisible(True)
            series.append(slice_checked)
        
        if not_checked_in > 0:
            slice_not_checked = QPieSlice("未報到", not_checked_in)
            slice_not_checked.setColor(QColor(244, 67, 54))  # 紅色
            slice_not_checked.setLabelVisible(True)
            series.append(slice_not_checked)
        
        if checked_in == 0 and not_checked_in == 0:
            # 沒有數據時顯示提示
            slice_empty = QPieSlice("暫無數據", 1)
            slice_empty.setColor(QColor(200, 200, 200))  # 灰色
            slice_empty.setLabelVisible(True)
            series.append(slice_empty)
        
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        self.chart_view.setChart(chart)
    
    def process_check_in(self):
        """
        處理報到 - 掃描戶號進行報到
        
        流程：
        1. 清理掃描輸入
        2. 查詢戶號
        3. 執行報到
        """
        raw_input = self.barcode_input.text().strip()
        
        if not raw_input:
            QMessageBox.warning(self, "警告", "請掃描或輸入戶號")
            return
        
        # 查找住戶
        household = self.db.get_household(raw_input)
        if not household:
            QMessageBox.critical(
                self, "錯誤", 
                f"戶號 {raw_input} 不存在"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 檢查是否已報到
        if self.is_household_checked_in(raw_input):
            QMessageBox.warning(
                self, "重複報到", 
                f"戶號 {raw_input} 已報到\n\n請掃描下一筆資料"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 執行報到
        if self.db.check_in_household(raw_input):
            self.last_checked_in_household_id = raw_input
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            self.refresh_check_in_list()
        else:
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
        """刷新報到列表和圖表"""
        # 更新統計信息
        stats = self.db.get_check_in_stats()
        if stats:
            total = stats.get('total_expected', 0)
            checked_in = stats.get('checked_in', 0)
            percentage = stats.get('percentage', 0)
            
            self.total_label.setText(f"預期出席: {total}")
            self.checked_label.setText(f"已報到: {checked_in}")
            self.percentage_label.setText(f"出席率: {percentage}%")
            
            # 更新進度條
            if total > 0:
                self.progress_bar.setValue(int(percentage))
            else:
                self.progress_bar.setValue(0)
            
            # 更新圖表
            not_checked_in = total - checked_in
            self.create_pie_chart(checked_in, not_checked_in)
        
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
            status = "✓ 已報到" if row[1] else "⊗ 尚未報到"
            status_item = QTableWidgetItem(status)
            
            # 如果是最後一筆報到資料，設置黃色背景
            if household_id == self.last_checked_in_household_id:
                household_id_item.setBackground(yellow_brush)
                time_item.setBackground(yellow_brush)
                status_item.setBackground(yellow_brush)
            
            self.check_in_table.setItem(row_position, 0, household_id_item)
            self.check_in_table.setItem(row_position, 1, time_item)
            self.check_in_table.setItem(row_position, 2, status_item)
    
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
