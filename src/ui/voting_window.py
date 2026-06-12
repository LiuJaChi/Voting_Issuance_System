"""
投票窗口 - 完整的投票刷票流程

此窗口支持：
1. 載入已報到的住戶資料
2. 選擇投票項目與投票選項
3. 刷條碼投票
4. 投票統計與進度顯示
5. 已投票住戶列表（橫向標籤樣式）
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit,
    QComboBox, QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem, QProgressBar,
    QMessageBox, QHeaderView, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

from src.backend.database import Database
from src.backend.barcode_generator import BarcodeGenerator


class VotingWindow(QWidget):
    """投票窗口 - 完整的投票刷票流程"""
    
    def __init__(self, parent=None):
        """初始化投票窗口"""
        super().__init__(parent)
        self.db = Database()
        self.barcode_gen = BarcodeGenerator()
        
        # 投票流程狀態
        self.voting_items = []
        self.all_households = []
        self.checked_in_households = {}  # 戶號 -> 報到記錄
        self.current_case_idx = 0
        self.selected_vote_option = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # ═══════════════════════════ 1. 載入住戶資料 ═══════════════════════════
        load_group = QGroupBox("1️⃣ 載入已報到住戶資料")
        load_layout = QHBoxLayout()
        
        load_button = QPushButton("📥 載入報到住戶")
        load_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        load_button.clicked.connect(self.load_checked_in_households)
        load_layout.addWidget(load_button)
        
        self.household_count_label = QLabel("已載入: 0 戶")
        self.household_count_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        load_layout.addWidget(self.household_count_label)
        
        load_layout.addStretch()
        load_group.setLayout(load_layout)
        main_layout.addWidget(load_group)
        
        # ═══════════════════════════ 2. 選擇投票項目與投票選項 ═══════════════════════════
        vote_setup_group = QGroupBox("2️⃣ 選擇投票項目與投票選項")
        vote_setup_layout = QVBoxLayout()
        
        # 投票項目選擇
        item_layout = QHBoxLayout()
        item_layout.addWidget(QLabel("投票項目:"))
        self.case_combo = QComboBox()
        self.case_combo.currentIndexChanged.connect(self.on_case_changed)
        item_layout.addWidget(self.case_combo)
        item_layout.addStretch()
        vote_setup_layout.addLayout(item_layout)
        
        # 項目詳情顯示
        self.case_info_label = QLabel("請先載入住戶資料並選擇投票項目")
        self.case_info_label.setStyleSheet("color: #666; font-size: 9pt;")
        vote_setup_layout.addWidget(self.case_info_label)
        
        vote_setup_layout.addSpacing(10)
        
        # 投票選項選擇
        option_layout = QHBoxLayout()
        option_layout.addWidget(QLabel("投票選項:"))
        
        self.vote_button_group = QButtonGroup()
        
        agree_radio = QRadioButton("✓ 同意")
        agree_radio.setStyleSheet("QRadioButton { font-size: 11pt; color: black; }")
        self.vote_button_group.addButton(agree_radio, 0)
        agree_radio.toggled.connect(lambda checked: self.on_vote_option_selected(checked, "同意"))
        option_layout.addWidget(agree_radio)
        
        disagree_radio = QRadioButton("✗ 不同意")
        disagree_radio.setStyleSheet("QRadioButton { font-size: 11pt; color: black; }")
        self.vote_button_group.addButton(disagree_radio, 1)
        disagree_radio.toggled.connect(lambda checked: self.on_vote_option_selected(checked, "不同意"))
        option_layout.addWidget(disagree_radio)
        
        abstain_radio = QRadioButton("⊘ 棄權")
        abstain_radio.setStyleSheet("QRadioButton { font-size: 11pt; color: black; }")
        self.vote_button_group.addButton(abstain_radio, 2)
        abstain_radio.toggled.connect(lambda checked: self.on_vote_option_selected(checked, "棄權"))
        option_layout.addWidget(abstain_radio)
        
        option_layout.addStretch()
        vote_setup_layout.addLayout(option_layout)
        
        vote_setup_layout.addSpacing(5)
        
        # 投票選項狀態提示
        self.vote_status_label = QLabel("⚠ 請先選擇投票選項")
        self.vote_status_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 10pt;")
        vote_setup_layout.addWidget(self.vote_status_label)
        
        vote_setup_group.setLayout(vote_setup_layout)
        main_layout.addWidget(vote_setup_group)
        
        # ═══════════════════════════ 3. 刷條碼投票 ═══════════════════════════
        barcode_group = QGroupBox("3️⃣ 刷條碼投票")
        barcode_layout = QVBoxLayout()
        
        barcode_input_layout = QHBoxLayout()
        barcode_input_layout.addWidget(QLabel("條碼/戶號:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("掃描投票單條碼或輸入戶號")
        self.barcode_input.returnPressed.connect(self.process_vote)
        self.barcode_input.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                padding: 8px;
                border: 2px solid #2196F3;
                border-radius: 4px;
            }
        """)
        barcode_input_layout.addWidget(self.barcode_input)
        
        vote_button = QPushButton("🗳️ 投票")
        vote_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 20px;")
        vote_button.clicked.connect(self.process_vote)
        barcode_input_layout.addWidget(vote_button)
        barcode_layout.addLayout(barcode_input_layout)
        
        # 投票狀態提示
        barcode_layout.addSpacing(5)
        self.vote_message_label = QLabel("")
        self.vote_message_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        barcode_layout.addWidget(self.vote_message_label)
        
        barcode_group.setLayout(barcode_layout)
        main_layout.addWidget(barcode_group)
        
        # ═══════════════════════════ 4. 投票統計 ═══════════════════════════
        stats_group = QGroupBox("4️⃣ 投票統計")
        stats_layout = QVBoxLayout()
        
        # 投票進度
        self.progress_label = QLabel("投票進度: 0 / 0")
        self.progress_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        stats_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        stats_layout.addWidget(self.progress_bar)
        
        # 投票結果表
        self.vote_stats_table = QTableWidget()
        self.vote_stats_table.setColumnCount(6)
        self.vote_stats_table.setHorizontalHeaderLabels(
            ["案號", "項目名稱", "同意", "不同意", "棄權", "進度"]
        )
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        stats_layout.addWidget(self.vote_stats_table)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # ═══════════════════════════ 5. 已投票住戶列表（橫向標籤樣式） ═══════════════════════════
        voted_group = QGroupBox("5️⃣ 已投票住戶列表")
        voted_layout = QVBoxLayout()
        
        # 建立可滾動的容器
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: 1px solid #DDD; background-color: #F9F9F9; }")
        
        # 建立容器widget和布局
        container_widget = QWidget()
        self.voted_households_layout = QHBoxLayout()
        self.voted_households_layout.addStretch()  # 左邊空白
        self.voted_households_layout.addStretch()  # 右邊空白，保證標籤在中間
        
        container_widget.setLayout(self.voted_households_layout)
        scroll_area.setWidget(container_widget)
        scroll_area.setMaximumHeight(100)
        
        voted_layout.addWidget(scroll_area)
        
        voted_group.setLayout(voted_layout)
        main_layout.addWidget(voted_group)
        
        self.setLayout(main_layout)
        
        # 自動更新投票統計
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_vote_stats)
    
    def load_checked_in_households(self):
        """載入已報到的住戶資料"""
        try:
            # 從數據庫獲取所有住戶
            self.all_households = self.db.get_all_households()
            
            if not self.all_households:
                QMessageBox.warning(self, "警告", "沒有住戶資料\n\n請先在住戶管理中導入住戶")
                return
            
            # 獲取報到統計
            check_in_stats = self.db.get_check_in_stats()
            checked_in_count = check_in_stats['checked_in']
            total_count = check_in_stats['total_expected']
            
            # 建立報到戶號映射表（用於快速查詢）
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT household_id FROM check_in_records
            """)
            checked_in_records = cursor.fetchall()
            conn.close()
            
            self.checked_in_households = {row['household_id'] for row in checked_in_records}
            
            self.household_count_label.setText(
                f"已載入: {checked_in_count} / {total_count} 戶"
            )
            
            # 載入投票項目
            self.load_voting_items()
            
            QMessageBox.information(
                self, "成功",
                f"已載入 {total_count} 戶住戶資料\n\n"
                f"已報到: {checked_in_count} 戶\n"
                f"未報到: {total_count - checked_in_count} 戶"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"載入住戶資料失敗: {str(e)}")
    
    def load_voting_items(self):
        """載入投票項目"""
        try:
            self.voting_items = self.db.get_all_voting_items()
            
            if not self.voting_items:
                QMessageBox.warning(self, "警告", "沒有投票項目\n\n請先在投票項目管理中新增項目")
                return
            
            self.case_combo.clear()
            for item in self.voting_items:
                display_text = f"第{item['case_number']}案 - {item['name']}"
                self.case_combo.addItem(display_text)
            
            self.on_case_changed(0)
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"載入投票項目失敗: {str(e)}")
    
    def on_case_changed(self, index):
        """投票項目改變時更新信息"""
        if index >= 0 and index < len(self.voting_items):
            case = self.voting_items[index]
            self.current_case_idx = index
            
            # 更新項目信息
            info_text = f"案號: {case['case_number']} | " \
                       f"項目: {case['name']} | " \
                       f"類型: {case.get('vote_type', '一般議案')} | " \
                       f"通過: {case.get('pass_percentage', 66.7):.1f}%"
            self.case_info_label.setText(info_text)
            
            # 清空投票選項選擇
            for button in self.vote_button_group.buttons():
                button.setChecked(False)
            self.selected_vote_option = None
            self.vote_status_label.setText("⚠ 請選擇投票選項")
            self.vote_status_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 10pt;")
            
            # 清空條碼輸入
            self.barcode_input.clear()
            self.vote_message_label.setText("")
            
            # 刷新投票統計
            self.refresh_vote_stats()
            # 更新頂部進度條為當前選中案的進度
            self._update_progress_bar()
    
    def on_vote_option_selected(self, checked, option):
        """投票選項選中時的處理"""
        if checked:
            self.selected_vote_option = option
            self.vote_status_label.setText(f"✓ 已選擇: {option}")
            self.vote_status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 10pt;")
            
            # 焦點放在條碼輸入框
            self.barcode_input.setFocus()
    
    def process_vote(self):
        """處理投票"""
        # 檢查投票前置條件
        if not self.all_households:
            QMessageBox.warning(self, "警告", "請先載入已報到的住戶資料")
            return
        
        if not self.voting_items:
            QMessageBox.warning(self, "警告", "請先載入投票項目")
            return
        
        if not self.selected_vote_option:
            QMessageBox.warning(self, "警告", "請先選擇投票選項（同意/不同意/棄權）")
            return
        
        barcode_input = self.barcode_input.text().strip()
        if not barcode_input:
            QMessageBox.warning(self, "警告", "請掃描投票單或輸入戶號")
            self.barcode_input.setFocus()
            return
        
        try:
            # 獲取當前投票項目
            case = self.voting_items[self.current_case_idx]
            household_id = barcode_input
            
            # 檢查住戶是否存在
            household = self.db.get_household(household_id)
            if not household:
                self.vote_message_label.setText(f"❌ 戶號 {household_id} 不存在")
                self.vote_message_label.setStyleSheet("color: #F44336; font-weight: bold;")
                self.barcode_input.clear()
                self.barcode_input.setFocus()
                return
            
            # 檢查是否已報到
            is_checked_in = household_id in self.checked_in_households
            if not is_checked_in:
                self.vote_message_label.setText(f"⚠ 戶號 {household_id} 未報到")
                self.vote_message_label.setStyleSheet("color: #FF9800; font-weight: bold;")
                self.barcode_input.clear()
                self.barcode_input.setFocus()
                return
            
            # 檢查是否已投票
            if self.db.has_voted(household_id, case['case_number']):
                self.vote_message_label.setText(f"⚠ 戶號 {household_id} 已投票")
                self.vote_message_label.setStyleSheet("color: #FF9800; font-weight: bold;")
                self.barcode_input.clear()
                self.barcode_input.setFocus()
                return
            
            # 記錄投票
            if self.db.record_vote(household_id, case['case_number'], self.selected_vote_option):
                self.vote_message_label.setText(f"✓ 戶號 {household_id} 投票成功 ({self.selected_vote_option})")
                self.vote_message_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                
                # 更新投票統計
                self.refresh_vote_stats()
                
                # 清空輸入框，焦點回到條碼輸入
                self.barcode_input.clear()
                self.barcode_input.setFocus()
                
            else:
                self.vote_message_label.setText(f"❌ 投票記錄失敗")
                self.vote_message_label.setStyleSheet("color: #F44336; font-weight: bold;")
                
        except Exception as e:
            self.vote_message_label.setText(f"❌ 錯誤: {str(e)}")
            self.vote_message_label.setStyleSheet("color: #F44336; font-weight: bold;")
    
    def refresh_vote_stats(self):
        """刷新投票統計"""
        try:
            self.vote_stats_table.setRowCount(0)
            
            if not self.voting_items:
                return
            
            total_households = len(self.checked_in_households)
            
            for row_idx, case in enumerate(self.voting_items):
                self.vote_stats_table.insertRow(row_idx)
                
                case_number = case['case_number']
                case_name = case['name']
                
                # 獲取投票結果
                results = self.db.get_voting_results(case_number)
                
                agree_count = results.get('votes', {}).get('同意', 0)
                disagree_count = results.get('votes', {}).get('不同意', 0)
                abstain_count = results.get('votes', {}).get('棄權', 0)
                
                total_count = agree_count + disagree_count + abstain_count
                
                # 計算該案進度百分比
                if total_households > 0:
                    case_progress = int((total_count / total_households) * 100)
                    progress_text = f"{total_count}/{total_households} ({case_progress}%)"
                else:
                    case_progress = 0
                    progress_text = "0/0 (0%)"
                
                # 填充表格
                case_num_item = QTableWidgetItem(case_number)
                case_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                case_name_item = QTableWidgetItem(case_name)
                
                agree_item = QTableWidgetItem(str(agree_count))
                agree_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                agree_item.setBackground(QColor("#C8E6C9"))
                agree_item.setForeground(QColor("black"))
                
                disagree_item = QTableWidgetItem(str(disagree_count))
                disagree_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                disagree_item.setBackground(QColor("#FFCDD2"))
                disagree_item.setForeground(QColor("black"))
                
                abstain_item = QTableWidgetItem(str(abstain_count))
                abstain_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                abstain_item.setBackground(QColor("#FFF9C4"))
                abstain_item.setForeground(QColor("black"))
                
                progress_item = QTableWidgetItem(progress_text)
                progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                self.vote_stats_table.setItem(row_idx, 0, case_num_item)
                self.vote_stats_table.setItem(row_idx, 1, case_name_item)
                self.vote_stats_table.setItem(row_idx, 2, agree_item)
                self.vote_stats_table.setItem(row_idx, 3, disagree_item)
                self.vote_stats_table.setItem(row_idx, 4, abstain_item)
                self.vote_stats_table.setItem(row_idx, 5, progress_item)
            
            # 更新頂部進度條為當前選中案的進度
            self._update_progress_bar()
            
            # 刷新已投票列表
            self.refresh_voted_list()
            
        except Exception as e:
            print(f"刷新投票統計失敗: {e}")
    
    def _update_progress_bar(self):
        """更新頂部進度條為當前選中案的進度"""
        total_households = len(self.checked_in_households)
        if not self.voting_items or self.current_case_idx < 0 or self.current_case_idx >= len(self.voting_items):
            self.progress_bar.setValue(0)
            self.progress_label.setText("投票進度: 0 / 0")
            return
        
        case = self.voting_items[self.current_case_idx]
        case_number = case['case_number']
        results = self.db.get_voting_results(case_number)
        
        agree_count = results.get('votes', {}).get('同意', 0)
        disagree_count = results.get('votes', {}).get('不同意', 0)
        abstain_count = results.get('votes', {}).get('棄權', 0)
        total_voted = agree_count + disagree_count + abstain_count
        
        if total_households > 0:
            progress = int((total_voted / total_households) * 100)
            self.progress_bar.setValue(progress)
            self.progress_label.setText(
                f"第{case_number}案進度: {total_voted} / {total_households} ({progress}%)"
            )
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText(f"第{case_number}案進度: 0 / 0 (0%)")
    
    def refresh_voted_list(self):
        """刷新已投票住戶列表 - 橫向標籤樣式"""
        try:
            # 清空現有的標籤（保留兩邊的 stretch）
            while self.voted_households_layout.count() > 2:
                widget = self.voted_households_layout.takeAt(0).widget()
                if widget:
                    widget.deleteLater()
            
            if not self.voting_items or self.current_case_idx >= len(self.voting_items):
                return
            
            case = self.voting_items[self.current_case_idx]
            case_number = case['case_number']
            
            # 從數據庫獲取投票記錄
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.household_id, v.vote
                FROM votes v
                WHERE v.case_number = ?
                ORDER BY v.voted_at DESC
                LIMIT 50
            """, (case_number,))
            votes = cursor.fetchall()
            conn.close()
            
            # 投票選項顏色映射
            vote_colors = {
                '同意': QColor(144, 238, 144),      # 淡綠色
                '不同意': QColor(255, 160, 122),    # 淡紅色
                '棄權': QColor(255, 255, 200)       # 淡黃色
            }
            
            # 為每個已投票戶號創建標籤
            for vote in votes:
                household_id = vote['household_id']
                vote_option = vote['vote']
                
                # 創建戶號標籤
                label = QLabel(household_id)
                label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # 根據投票選項設置背景色
                bg_color = vote_colors.get(vote_option, QColor(200, 200, 200))
                label.setStyleSheet(f"""
                    padding: 6px 10px;
                    border-radius: 5px;
                    background-color: {bg_color.name()};
                    color: black;
                    font-weight: bold;
                    min-width: 60px;
                    border: 2px solid {bg_color.darker(150).name()};
                """)
                
                self.voted_households_layout.insertWidget(
                    self.voted_households_layout.count() - 1, label
                )
            
        except Exception as e:
            print(f"刷新已投票列表失敗: {e}")
