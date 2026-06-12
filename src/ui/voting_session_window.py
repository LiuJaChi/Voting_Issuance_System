"""
投票刷票窗口 - 支持多案號投票，實時統計

功能：
1. 選擇投票選項（贊成/反對/棄權）
2. 掃描條碼投票
3. 實時統計投票結果
4. 分類顯示投票明細
5. 多案號投票切換
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QRadioButton, QButtonGroup, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime

from src.backend.database import Database


class VotingSessionWindow(QWidget):
    """投票刷票窗口 - 支持實時統計和分類投票"""
    
    def __init__(self, parent=None):
        """初始化投票刷票窗口"""
        super().__init__(parent)
        self.db = Database()
        
        # 狀態變數
        self.current_case_idx = 0  # 當前投票案號索引
        self.voting_cases = []  # 所有投票案號
        self.selected_vote = None  # 選中的投票選項
        self.voted_households = {}  # 已投票戶號集合
        
        self.init_ui()
        self.load_voting_cases()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QHBoxLayout()
        
        # ========== 左側：投票操作面板 ==========
        left_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("投票管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        left_layout.addWidget(title)
        
        # 當前案號信息
        self.case_info_label = QLabel("案號信息")
        self.case_info_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        left_layout.addWidget(self.case_info_label)
        
        # 投票選項選擇
        option_label = QLabel("選擇投票選項:")
        option_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        left_layout.addWidget(option_label)
        
        # 單選按鈕組
        self.vote_group = QButtonGroup()
        
        self.radio_agree = QRadioButton("✓ 贊成")
        self.radio_disagree = QRadioButton("✗ 反對")
        self.radio_abstain = QRadioButton("~ 棄權")
        
        self.vote_group.addButton(self.radio_agree, 0)
        self.vote_group.addButton(self.radio_disagree, 1)
        self.vote_group.addButton(self.radio_abstain, 2)
        
        self.radio_agree.setFont(QFont('Arial', 11))
        self.radio_disagree.setFont(QFont('Arial', 11))
        self.radio_abstain.setFont(QFont('Arial', 11))
        
        self.radio_agree.clicked.connect(lambda: self.set_vote_option('同意'))
        self.radio_disagree.clicked.connect(lambda: self.set_vote_option('不同意'))
        self.radio_abstain.clicked.connect(lambda: self.set_vote_option('棄權'))
        
        # 設置投票選項文字為白色 - 使用 QPalette + StyleSheet 組合
        for radio in [self.radio_agree, self.radio_disagree, self.radio_abstain]:
            # 方法1：使用調色板設置文字顏色（優先級高）
            palette = radio.palette()
            palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("white"))
            radio.setPalette(palette)
            
            # 方法2：使用樣式表進行微調
            radio.setStyleSheet("""
                QRadioButton {
                    color: white;
                    font-weight: bold;
                    background-color: transparent;
                }
                QRadioButton:hover {
                    color: white;
                }
                QRadioButton:pressed {
                    color: white;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                    margin-right: 5px;
                }
            """)
        
        left_layout.addWidget(self.radio_agree)
        left_layout.addWidget(self.radio_disagree)
        left_layout.addWidget(self.radio_abstain)
        
        left_layout.addSpacing(10)
        
        # 掃描條碼輸入
        scan_label = QLabel("掃描戶號:")
        scan_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        left_layout.addWidget(scan_label)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("請掃描投票單上的條碼...")
        self.barcode_input.returnPressed.connect(self.process_vote)
        left_layout.addWidget(self.barcode_input)
        
        left_layout.addSpacing(10)
        
        # 案號切換按鈕
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("◀ 上一案")
        self.prev_button.clicked.connect(self.prev_case)
        nav_layout.addWidget(self.prev_button)
        
        nav_layout.addStretch()
        
        self.next_button = QPushButton("下一案 ▶")
        self.next_button.clicked.connect(self.next_case)
        nav_layout.addWidget(self.next_button)
        
        left_layout.addLayout(nav_layout)
        
        left_layout.addSpacing(15)
        
        # 已投戶號列表標題
        voted_label = QLabel("已投戶號列表:")
        voted_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        left_layout.addWidget(voted_label)
        
        # 已投戶號表格
        self.voted_table = QTableWidget()
        self.voted_table.setColumnCount(3)
        self.voted_table.setHorizontalHeaderLabels(["戶號", "選項", "時間"])
        self.voted_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.voted_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.voted_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        left_layout.addWidget(self.voted_table)
        
        # ========== 右側：投票統計面板 ==========
        right_layout = QVBoxLayout()
        
        # 統計標題
        stats_title = QLabel("投票統計")
        stats_title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        right_layout.addWidget(stats_title)
        
        # 統計信息
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont('Arial', 10))
        right_layout.addWidget(self.stats_label)
        
        right_layout.addSpacing(10)
        
        # 投票結果統計表
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["選項", "票數", "百分比"])
        self.result_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.setMaximumHeight(150)
        right_layout.addWidget(self.result_table)
        
        right_layout.addSpacing(10)
        
        # 通過條件和結果
        self.pass_condition_label = QLabel("")
        self.pass_condition_label.setFont(QFont('Arial', 9))
        right_layout.addWidget(self.pass_condition_label)
        
        self.pass_result_label = QLabel("")
        pass_result_font = QFont('Arial', 12, QFont.Weight.Bold)
        self.pass_result_label.setFont(pass_result_font)
        right_layout.addWidget(self.pass_result_label)
        
        right_layout.addSpacing(15)
        
        # 進度條
        progress_label = QLabel("投票進度:")
        progress_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        right_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)
        
        right_layout.addSpacing(10)
        
        # 投票進度標籤
        self.progress_label = QLabel("已投: 0 / 0")
        self.progress_label.setFont(QFont('Arial', 10))
        right_layout.addWidget(self.progress_label)
        
        right_layout.addStretch()
        
        # 清空本案投票按鈕
        clear_case_button = QPushButton("清空本案投票記錄")
        clear_case_button.clicked.connect(self.clear_case_votes)
        right_layout.addWidget(clear_case_button)
        
        # ========== 組合左右布局 ==========
        main_layout.addLayout(left_layout, 1)  # 左側佔 1 份
        main_layout.addLayout(right_layout, 1)  # 右側佔 1 份
        
        self.setLayout(main_layout)
    
    def load_voting_cases(self):
        """載入所有投票案號"""
        self.voting_cases = self.db.get_all_voting_items()
        self.voted_households = {}
        
        if self.voting_cases:
            self.update_case_display()
        else:
            QMessageBox.warning(self, "警告", "沒有投票案號，請先添加投票項目")
    
    def update_case_display(self):
        """更新當前案號顯示"""
        if not self.voting_cases:
            return
        
        case = self.voting_cases[self.current_case_idx]
        
        # 更新案號信息
        case_text = f"第 {case['case_number']} 案: {case['name']}\n描述: {case.get('description', '無')}"
        self.case_info_label.setText(case_text)
        
        # 重置投票選項選擇
        self.vote_group.setExclusive(False)
        self.radio_agree.setChecked(False)
        self.radio_disagree.setChecked(False)
        self.radio_abstain.setChecked(False)
        self.vote_group.setExclusive(True)
        self.selected_vote = None
        
        # 清空條碼輸入
        self.barcode_input.clear()
        self.barcode_input.setFocus()
        
        # 更新已投戶號列表
        self.refresh_voted_list()
        
        # 更新統計信息
        self.refresh_voting_stats()
        
        # 更新按鈕狀態
        self.prev_button.setEnabled(self.current_case_idx > 0)
        self.next_button.setEnabled(self.current_case_idx < len(self.voting_cases) - 1)
    
    def set_vote_option(self, vote_option: str):
        """設置投票選項"""
        self.selected_vote = vote_option
        print(f"✓ 已選擇投票選項: {vote_option}")
    
    def process_vote(self):
        """處理投票 - 掃描條碼後投票"""
        if not self.selected_vote:
            QMessageBox.warning(self, "警告", "請先選擇投票選項（贊成/反對/棄權）")
            self.barcode_input.clear()
            return
        
        household_id = self.barcode_input.text().strip()
        
        if not household_id:
            QMessageBox.warning(self, "警告", "請掃描或輸入戶號")
            return
        
        # 檢查住戶是否存在
        household = self.db.get_household(household_id)
        if not household:
            QMessageBox.critical(self, "錯誤", f"戶號 {household_id} 不存在")
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 檢查是否已投票
        case = self.voting_cases[self.current_case_idx]
        if self.db.has_voted(household_id, case['case_number']):
            QMessageBox.warning(
                self, "重複投票",
                f"戶號 {household_id} 已投票\n\n請掃描下一筆資料"
            )
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            return
        
        # 執行投票
        if self.db.record_vote(household_id, case['case_number'], self.selected_vote):
            QMessageBox.information(
                self, "成功",
                f"戶號 {household_id} 投票成功\n\n選項: {self.selected_vote}"
            )
            
            # 清空輸入框並更新統計
            self.barcode_input.clear()
            self.barcode_input.setFocus()
            self.refresh_voted_list()
            self.refresh_voting_stats()
        else:
            QMessageBox.critical(self, "錯誤", "投票記錄失敗")
            self.barcode_input.clear()
            self.barcode_input.setFocus()
    
    def refresh_voted_list(self):
        """刷新已投戶號列表"""
        if not self.voting_cases:
            return
        
        case = self.voting_cases[self.current_case_idx]
        self.voted_table.setRowCount(0)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 查詢該案號的所有投票記錄
        cursor.execute("""
            SELECT h.household_id, h.name, v.vote, v.voted_at
            FROM votes v
            JOIN households h ON v.household_id = h.household_id
            WHERE v.case_number = ?
            ORDER BY v.voted_at DESC
        """, (case['case_number'],))
        
        rows = cursor.fetchall()
        conn.close()
        
        for row_idx, row in enumerate(rows):
            self.voted_table.insertRow(row_idx)
            
            household_id = row[0]
            vote_option = row[2]
            voted_at = row[3]
            
            # 戶號
            household_item = QTableWidgetItem(household_id)
            
            # 投票選項 - 設置顏色
            vote_item = QTableWidgetItem(vote_option)
            if vote_option == '同意':
                vote_item.setBackground(QColor(144, 238, 144))  # 淡綠色
            elif vote_option == '不同意':
                vote_item.setBackground(QColor(255, 160, 122))  # 淡紅色
            else:  # 棄權
                vote_item.setBackground(QColor(255, 255, 200))  # 淡黃色
            
            # 投票時間 - 只顯示時間部分
            try:
                time_str = voted_at.split(' ')[1] if ' ' in voted_at else voted_at
            except:
                time_str = voted_at
            time_item = QTableWidgetItem(time_str)
            
            self.voted_table.setItem(row_idx, 0, household_item)
            self.voted_table.setItem(row_idx, 1, vote_item)
            self.voted_table.setItem(row_idx, 2, time_item)
    
    def refresh_voting_stats(self):
        """刷新投票統計"""
        if not self.voting_cases:
            return
        
        case = self.voting_cases[self.current_case_idx]
        
        # 獲取出席人數
        checked_in_stats = self.db.get_check_in_stats()
        total_attendees = checked_in_stats['checked_in']
        
        # 獲取投票結果
        voting_result = self.db.get_voting_results(case['case_number'])
        
        # 統計各選項票數
        agree_votes = voting_result['votes'].get('同意', 0)
        disagree_votes = voting_result['votes'].get('不同意', 0)
        abstain_votes = voting_result['votes'].get('棄權', 0)
        total_votes = voting_result['total']
        
        # 更新結果表格
        self.result_table.setRowCount(0)
        
        vote_options = [
            ('同意', agree_votes, QColor(144, 238, 144)),
            ('不同意', disagree_votes, QColor(255, 160, 122)),
            ('棄權', abstain_votes, QColor(255, 255, 200)),
        ]
        
        for row_idx, (option, count, color) in enumerate(vote_options):
            self.result_table.insertRow(row_idx)
            
            percentage = (count / total_attendees * 100) if total_attendees > 0 else 0
            
            option_item = QTableWidgetItem(option)
            option_item.setBackground(color)
            option_item.setForeground(QColor("white"))
            
            count_item = QTableWidgetItem(str(count))
            count_item.setBackground(color)
            count_item.setForeground(QColor("white"))
            
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            percentage_item.setBackground(color)
            percentage_item.setForeground(QColor("white"))
            
            self.result_table.setItem(row_idx, 0, option_item)
            self.result_table.setItem(row_idx, 1, count_item)
            self.result_table.setItem(row_idx, 2, percentage_item)
        
        # 更新統計標籤
        pass_percentage = case.get('pass_percentage', 66.7)
        pass_condition = int(total_attendees * pass_percentage / 100)
        
        stats_text = f"總出席: {total_attendees} 人\n已投: {total_votes} 人\n未投: {total_attendees - total_votes} 人"
        self.stats_label.setText(stats_text)
        
        # 更新通過條件
        pass_text = f"通過條件: 同意票 ≥ {pass_condition} 人 ({pass_percentage}%)"
        self.pass_condition_label.setText(pass_text)
        
        # 判定通過/不通過
        if agree_votes >= pass_condition:
            result_text = f"✅ 通過 (同意票 {agree_votes} ≥ {pass_condition})"
            self.pass_result_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            result_text = f"❌ 不通過 (同意票 {agree_votes} < {pass_condition})"
            self.pass_result_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.pass_result_label.setText(result_text)
        
        # 更新進度條
        if total_attendees > 0:
            progress = int(total_votes / total_attendees * 100)
            self.progress_bar.setValue(progress)
            self.progress_label.setText(f"已投: {total_votes} / {total_attendees}")
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("已投: 0 / 0")
    
    def prev_case(self):
        """上一案"""
        if self.current_case_idx > 0:
            self.current_case_idx -= 1
            self.update_case_display()
    
    def next_case(self):
        """下一案"""
        if self.current_case_idx < len(self.voting_cases) - 1:
            self.current_case_idx += 1
            self.update_case_display()
    
    def clear_case_votes(self):
        """清空本案投票記錄"""
        reply = QMessageBox.question(
            self, "確認",
            "確定要清空本案所有投票記錄嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            case = self.voting_cases[self.current_case_idx]
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM votes WHERE case_number = ?", (case['case_number'],))
            conn.commit()
            conn.close()
            
            self.refresh_voted_list()
            self.refresh_voting_stats()
            QMessageBox.information(self, "成功", "本案投票記錄已清空")
