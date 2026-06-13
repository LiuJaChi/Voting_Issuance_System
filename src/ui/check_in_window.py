"""
報到窗口 UI 類
"""
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QProgressBar,
    QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager
import matplotlib.pyplot as plt
import sqlite3

from src.backend.database import Database

# 模組級別儲存已偵測到的中文字體路徑
_chinese_font_path = None


def setup_chinese_font():
    """設置中文字體支持，依平台自動偵測可用字體並向 matplotlib 註冊。"""
    global _chinese_font_path

    plt.rcParams['axes.unicode_minus'] = False

    # 依平台列出候選字體路徑
    if sys.platform == 'win32':
        font_paths = [
            'C:\\Windows\\Fonts\\msjh.ttc',    # 微軟正黑體
            'C:\\Windows\\Fonts\\msjhbd.ttc',
            'C:\\Windows\\Fonts\\msyh.ttc',    # 微軟雅黑
            'C:\\Windows\\Fonts\\msyh.ttf',
            'C:\\Windows\\Fonts\\kaiu.ttf',    # 標楷體
            'C:\\Windows\\Fonts\\simhei.ttf',  # 黑體
            'C:\\Windows\\Fonts\\simsun.ttc',  # 新宋體
        ]
    elif sys.platform == 'darwin':
        font_paths = [
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Arial Unicode MS.ttf',
        ]
    else:  # Linux 及其他
        font_paths = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/arphic/uming.ttc',
            '/usr/share/fonts/truetype/arphic/ukai.ttc',
        ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                fontManager.addfont(font_path)
                prop = FontProperties(fname=font_path)
                font_name = prop.get_name()
                current = plt.rcParams.get('font.sans-serif', [])
                plt.rcParams['font.sans-serif'] = [font_name] + [f for f in current if f != font_name]
                _chinese_font_path = font_path
                return
            except Exception as e:
                print(f"字體載入失敗 {font_path}: {e}")
                continue

    # 找不到字體檔案時使用字體名稱備選清單
    plt.rcParams['font.sans-serif'] = [
        'Microsoft JhengHei', 'Microsoft YaHei', 'SimHei',
        'STHeiti', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei',
        'DejaVu Sans',
    ]
    print("未找到中文字體檔案，已設定系統字體備選清單")


# 初始化中文字體
setup_chinese_font()


class CheckInWindow(QWidget):
    """報到窗口 - 支持進度顯示、圖表統計和面積(坪)統計"""
    
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
        
        # 標題和統計信息的組合
        top_layout = QHBoxLayout()
        
        # 左部分：標題（白色字）
        title = QLabel("報到管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: white;")
        top_layout.addWidget(title)
        
        top_layout.addStretch()
        
        # 右部分：面積統計信息（右上方）
        area_stats_layout = QVBoxLayout()
        area_stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.total_area_label = QLabel("總坪數: 0 坪")
        self.total_area_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #1976D2;")
        area_stats_layout.addWidget(self.total_area_label)
        
        self.checked_area_label = QLabel("已報到坪數: 0 坪")
        self.checked_area_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #4CAF50;")
        area_stats_layout.addWidget(self.checked_area_label)
        
        self.area_percentage_label = QLabel("坪數占比: 0%")
        self.area_percentage_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #FF9800;")
        area_stats_layout.addWidget(self.area_percentage_label)
        
        top_layout.addLayout(area_stats_layout)
        left_layout.addLayout(top_layout)
        
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
        
        # 報到記錄表 - 新增面積(坪)欄位
        self.check_in_table = QTableWidget()
        self.check_in_table.setColumnCount(4)
        self.check_in_table.setHorizontalHeaderLabels(
            ["戶號", "面積(坪)", "報到時間", "狀態"]
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.check_in_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
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
        chart_title.setStyleSheet("color: white;")
        right_layout.addWidget(chart_title)
        
        # 建立 Matplotlib 圖表
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
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
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 取得中文字體屬性
        chinese_font = None
        if _chinese_font_path:
            try:
                chinese_font = FontProperties(fname=_chinese_font_path)
            except Exception:
                pass
        if chinese_font is None:
            try:
                chinese_font = FontProperties(family=plt.rcParams['font.sans-serif'][0])
            except Exception:
                pass

        # 準備數據
        labels = []
        sizes = []
        colors = []
        
        if checked_in > 0:
            labels.append(f'已報到\n({checked_in}人)')
            sizes.append(checked_in)
            colors.append('#4CAF50')  # 綠色
        
        if not_checked_in > 0:
            labels.append(f'未報到\n({not_checked_in}人)')
            sizes.append(not_checked_in)
            colors.append('#F44336')  # 紅色
        
        if not sizes:
            # 沒有數據時顯示提示
            labels = ['暫無數據']
            sizes = [1]
            colors = ['#CCCCCC']
        
        # 繪製圓餅圖
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={
                'fontsize': 9,
                'weight': 'bold'
            }
        )
        
        # 套用中文字體到所有文字元素
        for text in texts:
            if chinese_font:
                text.set_fontproperties(chinese_font)
            text.set_fontsize(8)
            text.set_weight('bold')
        
        for autotext in autotexts:
            if chinese_font:
                autotext.set_fontproperties(chinese_font)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        # 設置標題
        if _chinese_font_path:
            title_font = FontProperties(fname=_chinese_font_path, size=11, weight='bold')
        elif chinese_font is not None:
            title_font = FontProperties(family=chinese_font.get_family()[0], size=11, weight='bold')
        else:
            title_font = None

        if title_font is not None:
            ax.set_title('報到狀態分佈', pad=15, fontproperties=title_font)
        else:
            ax.set_title('報到狀態分佈', fontsize=11, fontweight='bold', pad=15)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
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
        """刷新報到列表、圖表和面積統計"""
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
        
        # 計算面積統計
        area_stats = self.db.get_check_in_area_stats()
        if area_stats:
            total_area = area_stats.get('total_area', 0)
            checked_in_area = area_stats.get('checked_in_area', 0)
            area_percentage = area_stats.get('area_percentage', 0)
            
            self.total_area_label.setText(f"總坪數: {total_area:.2f} 坪")
            self.checked_area_label.setText(f"已報到坪數: {checked_in_area:.2f} 坪")
            self.area_percentage_label.setText(f"坪數占比: {area_percentage:.2f}%")
        
        # 更新表格
        self.check_in_table.setRowCount(0)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 查詢所有住戶及其報到信息和面積
        cursor.execute("""
            SELECT h.household_id, h.share_amount, c.checked_in_at
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
            share_amount = row[1] if row[1] else 0  # 面積(坪)
            
            # 戶號
            household_id_item = QTableWidgetItem(household_id)
            
            # 面積(坪)
            area_item = QTableWidgetItem(f"{share_amount:.2f}")
            area_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 報到時間 - 只顯示時間部分 (HH:MM:SS)
            if row[2]:
                try:
                    checked_in_at = row[2].split(' ')[1] if ' ' in row[2] else row[2]
                except:
                    checked_in_at = row[2]
            else:
                checked_in_at = ""
            
            time_item = QTableWidgetItem(checked_in_at)
            
            # 狀態 - 已報到 或 尚未報到
            status = "✓ 已報到" if row[2] else "⊗ 尚未報到"
            status_item = QTableWidgetItem(status)
            
            # 如果是最後一筆報到資料，設置黃色背景
            if household_id == self.last_checked_in_household_id:
                household_id_item.setBackground(yellow_brush)
                area_item.setBackground(yellow_brush)
                time_item.setBackground(yellow_brush)
                status_item.setBackground(yellow_brush)
            
            self.check_in_table.setItem(row_position, 0, household_id_item)
            self.check_in_table.setItem(row_position, 1, area_item)
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
            self, "確認", "確定要清空所有報到數據嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_check_in_data()
            self.last_checked_in_household_id = None
            self.refresh_check_in_list()
            QMessageBox.information(self, "成功", "報到數據已清空")
