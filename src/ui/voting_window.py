from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox, 
    QLineEdit, QPushButton, QRadioButton, QButtonGroup, QTableWidget, 
    QTableWidgetItem, QProgressBar, QMessageBox, QHeaderView, QAbstractItemView,
    QDialog, QFileDialog, QTextEdit, QDialogButtonBox
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime
from src.backend.database import Database
from src.backend.barcode_generator import BarcodeGenerator

_MAX_DISPLAYED_ERRORS = 20


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
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        
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
        left_layout.addWidget(load_group)
        
        # ═══════════════════════════ 2. 選擇投票項目與投票選項 ═════════════════════════
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
        self.case_info_label.setStyleSheet("color: #FFF; font-size: 9pt;")
        vote_setup_layout.addWidget(self.case_info_label)
        
        vote_setup_layout.addSpacing(10)
        
        # 投票選項選擇
        option_layout = QHBoxLayout()
        option_layout.addWidget(QLabel("投票選項:"))
        
        self.vote_button_group = QButtonGroup()
        
        agree_radio = QRadioButton("✓ 贊成")
        agree_radio.setStyleSheet("QRadioButton { font-size: 11pt; color: white; }")
        self.vote_button_group.addButton(agree_radio, 0)
        agree_radio.toggled.connect(lambda checked: self.on_vote_option_selected(checked, "同意"))
        option_layout.addWidget(agree_radio)
        
        disagree_radio = QRadioButton("✗ 反對")
        disagree_radio.setStyleSheet("QRadioButton { font-size: 11pt; color:white; }")
        self.vote_button_group.addButton(disagree_radio, 1)
        disagree_radio.toggled.connect(lambda checked: self.on_vote_option_selected(checked, "不同意"))
        option_layout.addWidget(disagree_radio)
        
        abstain_radio = QRadioButton("⊘ 棄權")
        abstain_radio.setStyleSheet("QRadioButton { font-size: 11pt; color: white; }")
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
        left_layout.addWidget(vote_setup_group)
        
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
        left_layout.addWidget(barcode_group)
        
        # ═══════════════════════════ 4. 投票統計 ═══════════════════════════
        stats_group = QGroupBox("4️⃣ 投票統計（出席坪數百分比）")
        stats_layout = QVBoxLayout()
        
        # 投票進度
        self.progress_label = QLabel("投票進度: 0 / 0")
        self.progress_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        stats_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        stats_layout.addWidget(self.progress_bar)

        # 實時統計資訊（投票數/總數/百分比/面積）
        summary_layout = QHBoxLayout()
        self.voted_count_label = QLabel("投票數: 0")
        self.total_count_label = QLabel("總數: 0")
        self.voted_percent_label = QLabel("百分比: 0.00%")
        self.voted_area_label = QLabel("面積: 0.00 坪")
        for label in (
            self.voted_count_label,
            self.total_count_label,
            self.voted_percent_label,
            self.voted_area_label,
        ):
            label.setStyleSheet("font-size: 9pt; font-weight: bold;")
            summary_layout.addWidget(label)
        summary_layout.addStretch()
        stats_layout.addLayout(summary_layout)
        
        # 投票結果表 - 坪數百分比顯示（分母為出席住戶總坪數）
        self.vote_stats_table = QTableWidget()
        self.vote_stats_table.setColumnCount(9)
        self.vote_stats_table.setHorizontalHeaderLabels(
            ["案號", "項目名稱", "同意", "不同意", "棄權", 
             "同意%", "不同意%", "棄權%", "進度"]
        )
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.vote_stats_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        stats_layout.addWidget(self.vote_stats_table)
        
        # 匯出 / 匯入按鈕列
        io_layout = QHBoxLayout()

        export_xlsx_btn = QPushButton("📤 匯出 XLSX")
        export_xlsx_btn.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 6px 14px;")
        export_xlsx_btn.clicked.connect(self.export_votes_xlsx)
        io_layout.addWidget(export_xlsx_btn)

        export_json_btn = QPushButton("📤 匯出 JSON")
        export_json_btn.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 6px 14px;")
        export_json_btn.clicked.connect(self.export_votes_json)
        io_layout.addWidget(export_json_btn)

        import_btn = QPushButton("📥 匯入數據")
        import_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold; padding: 6px 14px;")
        import_btn.clicked.connect(self.open_import_dialog)
        io_layout.addWidget(import_btn)

        io_layout.addStretch()
        stats_layout.addLayout(io_layout)

        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)

        # ═══════════════════════════ 右側：已投票戶號列表 ═════════════════════════
        right_layout = QVBoxLayout()
        voted_group = QGroupBox("已投票戶號列表")
        voted_layout = QVBoxLayout()

        self.voted_table = QTableWidget()
        self.voted_table.setColumnCount(4)
        self.voted_table.setHorizontalHeaderLabels(["戶號", "投票選項", "面積(坪)", "投票時間"])
        self.voted_table.setAlternatingRowColors(True)
        self.voted_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.voted_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.voted_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.voted_table.verticalHeader().setVisible(False)
        self.voted_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.voted_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.voted_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.voted_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.voted_table.setFont(QFont("Arial", 9))
        self.voted_table.horizontalHeader().setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.voted_table.verticalHeader().setDefaultSectionSize(20)

        voted_layout.addWidget(self.voted_table)
        voted_group.setLayout(voted_layout)
        right_layout.addWidget(voted_group)
        
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 2)
        
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
            
            # 刷新投票統計並更新進度條
            self.refresh_vote_stats()
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
            QMessageBox.warning(self, "警告", "請先選擇投票選項（贊成/反對/棄權）")
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
    
    def get_checked_in_total_area(self):
        """獲取出席住戶的總坪數"""
        try:
            if not self.checked_in_households:
                return 0.0
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 計算出席住戶的總坪數
            placeholders = ','.join(['?' for _ in self.checked_in_households])
            query = f"SELECT COALESCE(SUM(share_amount), 0) as total_area FROM households WHERE household_id IN ({placeholders})"
            cursor.execute(query, list(self.checked_in_households))
            result = cursor.fetchone()
            conn.close()
            
            return result['total_area'] if result else 0.0
        except Exception as e:
            print(f"獲取出席住戶總坪數失敗: {e}")
            return 0.0
    
    def refresh_vote_stats(self):
        """刷新投票統計 - 顯示坪數百分比（分母為出席住戶總坪數）"""
        try:
            self.vote_stats_table.setRowCount(0)
            
            if not self.voting_items:
                return
            
            # 獲取出席住戶的總坪數
            checked_in_total_area = self.get_checked_in_total_area()
            
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
                
                # 獲取各選項的面積(坪)數據
                agree_area = self.db.get_voting_area_by_vote(case_number, '同意')
                disagree_area = self.db.get_voting_area_by_vote(case_number, '不同意')
                abstain_area = self.db.get_voting_area_by_vote(case_number, '棄權')
                
                # 計算坪數百分比 - 分母為出席住戶總坪數
                agree_area_pct = (agree_area / checked_in_total_area * 100) if checked_in_total_area > 0 else 0
                disagree_area_pct = (disagree_area / checked_in_total_area * 100) if checked_in_total_area > 0 else 0
                abstain_area_pct = (abstain_area / checked_in_total_area * 100) if checked_in_total_area > 0 else 0
                
                # 計算該案件的進度百分比（按人數）
                case_progress = int((total_count / total_households) * 100) if total_households > 0 else 0
                
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
                
                # 面積坪數百分比列（分母為出席住戶總坪數）
                agree_area_pct_item = QTableWidgetItem(f"{agree_area_pct:.2f}%")
                agree_area_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                agree_area_pct_item.setBackground(QColor("#C8E6C9"))
                agree_area_pct_item.setForeground(QColor("black"))
                
                disagree_area_pct_item = QTableWidgetItem(f"{disagree_area_pct:.2f}%")
                disagree_area_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                disagree_area_pct_item.setBackground(QColor("#FFCDD2"))
                disagree_area_pct_item.setForeground(QColor("black"))
                
                abstain_area_pct_item = QTableWidgetItem(f"{abstain_area_pct:.2f}%")
                abstain_area_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                abstain_area_pct_item.setBackground(QColor("#FFF9C4"))
                abstain_area_pct_item.setForeground(QColor("black"))
                
                # 進度列
                progress_item = QTableWidgetItem(f"{case_progress}%")
                progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                progress_item.setForeground(QColor("black"))
                if case_progress >= 75:
                    progress_item.setBackground(QColor("#C8E6C9"))
                elif case_progress >= 50:
                    progress_item.setBackground(QColor("#FFE082"))
                else:
                    progress_item.setBackground(QColor("#FFCDD2"))
                
                self.vote_stats_table.setItem(row_idx, 0, case_num_item)
                self.vote_stats_table.setItem(row_idx, 1, case_name_item)
                self.vote_stats_table.setItem(row_idx, 2, agree_item)
                self.vote_stats_table.setItem(row_idx, 3, disagree_item)
                self.vote_stats_table.setItem(row_idx, 4, abstain_item)
                self.vote_stats_table.setItem(row_idx, 5, agree_area_pct_item)
                self.vote_stats_table.setItem(row_idx, 6, disagree_area_pct_item)
                self.vote_stats_table.setItem(row_idx, 7, abstain_area_pct_item)
                self.vote_stats_table.setItem(row_idx, 8, progress_item)
            
            # 刷新已投票列表
            self.refresh_voted_list()
            self._update_progress_bar()
            
        except Exception as e:
            print(f"刷新投票統計失敗: {e}")
    
    def _update_progress_bar(self):
        """更新進度條 - 顯示當前案件的進度"""
        try:
            if not self.voting_items or self.current_case_idx >= len(self.voting_items):
                self.progress_bar.setValue(0)
                self.progress_label.setText("投票進度: 0 / 0")
                self.voted_count_label.setText("投票數: 0")
                self.total_count_label.setText("總數: 0")
                self.voted_percent_label.setText("百分比: 0.00%")
                self.voted_area_label.setText("面積: 0.00 坪")
                return
            
            case = self.voting_items[self.current_case_idx]
            case_number = case['case_number']
            
            # 獲取該案件的投票結果
            results = self.db.get_voting_results(case_number)
            agree_count = results.get('votes', {}).get('同意', 0)
            disagree_count = results.get('votes', {}).get('不同意', 0)
            abstain_count = results.get('votes', {}).get('棄權', 0)
            total_count = agree_count + disagree_count + abstain_count
            
            total_households = len(self.checked_in_households)
            agree_area = self.db.get_voting_area_by_vote(case_number, '同意')
            disagree_area = self.db.get_voting_area_by_vote(case_number, '不同意')
            abstain_area = self.db.get_voting_area_by_vote(case_number, '棄權')
            total_voted_area = agree_area + disagree_area + abstain_area
            
            # 更新進度
            if total_households > 0:
                progress = int((total_count / total_households) * 100)
                self.progress_bar.setValue(progress)
                self.progress_label.setText(f"投票進度: {total_count} / {total_households} ({progress}%)")
                self.voted_count_label.setText(f"投票數: {total_count}")
                self.total_count_label.setText(f"總數: {total_households}")
                self.voted_percent_label.setText(f"百分比: {(total_count / total_households) * 100:.2f}%")
                self.voted_area_label.setText(f"面積: {total_voted_area:.2f} 坪")
            else:
                self.progress_bar.setValue(0)
                self.progress_label.setText("投票進度: 0 / 0")
                self.voted_count_label.setText("投票數: 0")
                self.total_count_label.setText("總數: 0")
                self.voted_percent_label.setText("百分比: 0.00%")
                self.voted_area_label.setText(f"面積: {total_voted_area:.2f} 坪")
                
        except Exception as e:
            print(f"更新進度條失敗: {e}")
    
    def refresh_voted_list(self):
        """刷新已投票住戶列表（戶號/選項/面積/投票時間）"""
        try:
            self.voted_table.setRowCount(0)
            
            # 獲取當前案件已投票的住戶
            if not self.voting_items or self.current_case_idx >= len(self.voting_items):
                return
            
            case = self.voting_items[self.current_case_idx]
            case_number = case['case_number']
            
            # 獲取該案件的所有投票記錄
            votes = self.db.get_all_votes_for_case(case_number)
            self.voted_table.setRowCount(len(votes))

            household_area_map = {
                household['household_id']: float(household.get('share_amount', 0) or 0)
                for household in self.all_households
            }
            vote_text_map = {"同意": "贊成", "不同意": "反對", "棄權": "棄權"}

            for row_idx, vote in enumerate(votes):
                household_id = vote.get('household_id', '')
                vote_option = vote.get('vote', '')
                voted_at = vote.get('voted_at', '')
                area = household_area_map.get(household_id, 0.0)

                household_item = QTableWidgetItem(household_id)
                vote_item = QTableWidgetItem(vote_text_map.get(vote_option, vote_option))
                area_item = QTableWidgetItem(f"{area:.2f}")
                time_item = QTableWidgetItem(str(voted_at))

                household_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                vote_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                area_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.voted_table.setItem(row_idx, 0, household_item)
                self.voted_table.setItem(row_idx, 1, vote_item)
                self.voted_table.setItem(row_idx, 2, area_item)
                self.voted_table.setItem(row_idx, 3, time_item)
            
        except Exception as e:
            print(f"刷新已投票列表失敗: {e}")
    
    def export_votes_xlsx(self):
        """匯出投票數據為 XLSX"""
        try:
            export_path = self.db.export_voting_data()
            if export_path:
                QMessageBox.information(self, "成功", f"投票數據已匯出:\n{export_path}")
            else:
                QMessageBox.critical(self, "錯誤", "投票數據匯出失敗")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯出失敗: {str(e)}")
    
    def export_votes_json(self):
        """匯出投票數據為 JSON"""
        try:
            if self.db.export_data():
                QMessageBox.information(self, "成功", "投票數據已匯出到 exports/data.json")
            else:
                QMessageBox.critical(self, "錯誤", "投票數據匯出失敗")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯出失敗: {str(e)}")
    
    def open_import_dialog(self):
        """打開匯入數據對話框"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "選擇要匯入的投票數據文件",
                "",
                "Excel Files (*.xlsx);;JSON Files (*.json)"
            )
            
            if not file_path:
                return
            
            if file_path.endswith('.xlsx'):
                result = self.db.import_voting_data(file_path, mode='merge')
                if result['errors']:
                    error_msg = "匯入完成，但有以下錯誤:\n\n"
                    error_msg += "\n".join(result['errors'][:10])
                    if len(result['errors']) > 10:
                        error_msg += f"\n... 還有 {len(result['errors']) - 10} 個錯誤"
                    QMessageBox.warning(self, "匯入提示", error_msg)
                else:
                    QMessageBox.information(self, "成功", "\n".join(result['messages']))
                
                # 刷新統計
                self.refresh_vote_stats()
                
            else:
                QMessageBox.warning(self, "提示", "暫不支持 JSON 匯入")
                
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯入失敗: {str(e)}")
