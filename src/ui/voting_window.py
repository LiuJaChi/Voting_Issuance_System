"""
投票窗口 - 支持投票項目完整管理

功能：
1. 新增/編輯/刪除投票項目
2. 編輯投票種類（重大議案 / 一般議案）
3. 編輯通過百分比（50% ~ 100%）
4. 投票結果統計和分類
5. 投票刷票會話
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QTabWidget, QDialog, QSpinBox, QDoubleSpinBox,
    QComboBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from src.backend.database import Database
from src.backend.config_manager import ConfigManager
from src.ui.voting_session_window import VotingSessionWindow


class VotingWindow(QWidget):
    """投票窗口 - 支持項目管理和投票刷票"""
    
    def __init__(self, parent=None):
        """初始化投票窗口"""
        super().__init__(parent)
        self.db = Database()
        self.config_manager = ConfigManager()
        self.voting_session = None
        
        self.init_ui()
        self.load_voting_items()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("投票管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        
        new_item_button = QPushButton("+ 新增投票項目")
        new_item_button.clicked.connect(self.add_voting_item)
        button_layout.addWidget(new_item_button)
        
        button_layout.addStretch()
        
        # 開始投票按鈕
        start_voting_button = QPushButton("🗳️ 開始投票")
        start_voting_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        start_voting_button.clicked.connect(self.start_voting_session)
        button_layout.addWidget(start_voting_button)
        
        main_layout.addLayout(button_layout)
        
        # 投票項目表
        self.voting_table = QTableWidget()
        self.voting_table.setColumnCount(7)
        self.voting_table.setHorizontalHeaderLabels(
            ["項次", "案名", "投票種類", "通過百分比(%)", "描述", "編輯", "刪除"]
        )
        self.voting_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.voting_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.voting_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.voting_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.voting_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.voting_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.voting_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.voting_table.setMaximumHeight(250)
        main_layout.addWidget(self.voting_table)
        
        # 分隔線
        main_layout.addSpacing(10)
        
        # 投票結果標籤
        result_title = QLabel("投票結果統計")
        result_title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        main_layout.addWidget(result_title)
        
        # 投票結果表
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels(
            ["項次", "案名", "同意", "反對", "棄權", "結果"]
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        main_layout.addWidget(self.result_table)
        
        # 刷新按鈕
        refresh_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新結果")
        refresh_button.clicked.connect(self.refresh_voting_results)
        refresh_layout.addWidget(refresh_button)
        refresh_layout.addStretch()
        main_layout.addLayout(refresh_layout)
        
        self.setLayout(main_layout)
    
    def load_voting_items(self):
        """加載投票項目"""
        self.voting_table.setRowCount(0)
        
        items = self.db.get_all_voting_items()
        
        for row_idx, item in enumerate(items):
            self.voting_table.insertRow(row_idx)
            
            # 項次（案號）
            case_number_item = QTableWidgetItem(item['case_number'])
            case_number_item.setFlags(case_number_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 案名
            name_item = QTableWidgetItem(item['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 投票種類
            vote_type = item.get('vote_type', '一般議案')
            vote_type_item = QTableWidgetItem(vote_type)
            vote_type_item.setFlags(vote_type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 通過百分比
            pass_percentage = item.get('pass_percentage', 66.7)
            pass_percentage_item = QTableWidgetItem(f"{pass_percentage:.1f}")
            pass_percentage_item.setFlags(pass_percentage_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 描述
            description = item.get('description', '')
            description_item = QTableWidgetItem(description[:30] if description else '無')
            description_item.setFlags(description_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 編輯按鈕
            edit_button = QPushButton("✏️ 編輯")
            edit_button.clicked.connect(lambda checked, case_num=item['case_number']: self.edit_voting_item(case_num))
            
            # 刪除按鈕
            delete_button = QPushButton("🗑️ 刪除")
            delete_button.clicked.connect(lambda checked, case_num=item['case_number']: self.delete_voting_item(case_num))
            
            self.voting_table.setItem(row_idx, 0, case_number_item)
            self.voting_table.setItem(row_idx, 1, name_item)
            self.voting_table.setItem(row_idx, 2, vote_type_item)
            self.voting_table.setItem(row_idx, 3, pass_percentage_item)
            self.voting_table.setItem(row_idx, 4, description_item)
            self.voting_table.setCellWidget(row_idx, 5, edit_button)
            self.voting_table.setCellWidget(row_idx, 6, delete_button)
        
        # 刷新投票結果
        self.refresh_voting_results()
    
    def refresh_voting_results(self):
        """刷新投票結果統計"""
        self.result_table.setRowCount(0)
        
        items = self.db.get_all_voting_items()
        stats = self.db.get_check_in_stats()
        total_attendees = stats['checked_in']
        
        for row_idx, item in enumerate(items):
            self.result_table.insertRow(row_idx)
            
            # 獲取投票結果
            result = self.db.get_voting_results(item['case_number'])
            agree_votes = result['votes'].get('同意', 0)
            disagree_votes = result['votes'].get('不同意', 0)
            abstain_votes = result['votes'].get('棄權', 0)
            
            # 獲取該項目的通過百分比
            pass_percentage = item.get('pass_percentage', 66.7)
            pass_condition = int(total_attendees * pass_percentage / 100)
            
            # 項次
            case_number_item = QTableWidgetItem(item['case_number'])
            case_number_item.setFlags(case_number_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 案名
            name_item = QTableWidgetItem(item['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 同意票
            agree_item = QTableWidgetItem(str(agree_votes))
            agree_item.setBackground(QColor(144, 238, 144))  # 淡綠色
            agree_item.setFlags(agree_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 反對票
            disagree_item = QTableWidgetItem(str(disagree_votes))
            disagree_item.setBackground(QColor(255, 160, 122))  # 淡紅色
            disagree_item.setFlags(disagree_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 棄權票
            abstain_item = QTableWidgetItem(str(abstain_votes))
            abstain_item.setBackground(QColor(255, 255, 200))  # 淡黃色
            abstain_item.setFlags(abstain_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 通過/不通過判定
            if agree_votes >= pass_condition:
                result_text = "✅ 通過"
                result_item = QTableWidgetItem(result_text)
                result_item.setBackground(QColor(144, 238, 144))  # 綠色背景
            else:
                result_text = "❌ 不通過"
                result_item = QTableWidgetItem(result_text)
                result_item.setBackground(QColor(255, 160, 122))  # 紅色背景
            
            result_item.setFlags(result_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.result_table.setItem(row_idx, 0, case_number_item)
            self.result_table.setItem(row_idx, 1, name_item)
            self.result_table.setItem(row_idx, 2, agree_item)
            self.result_table.setItem(row_idx, 3, disagree_item)
            self.result_table.setItem(row_idx, 4, abstain_item)
            self.result_table.setItem(row_idx, 5, result_item)
    
    def add_voting_item(self):
        """新增投票項目"""
        dialog = VotingItemEditDialog(self, mode='new')
        if dialog.exec():
            case_number, name, description, vote_type, pass_percentage = dialog.get_values()
            
            # 驗證案號不為空
            if not case_number.strip():
                QMessageBox.warning(self, "警告", "案號不能為空")
                return
            
            if self.db.add_voting_item(case_number, name, description, vote_type, pass_percentage):
                QMessageBox.information(self, "成功", "投票項目已添加")
                self.load_voting_items()
            else:
                QMessageBox.critical(self, "錯誤", "投票項目已存在或添加失敗")
    
    def edit_voting_item(self, case_number):
        """編輯投票項目"""
        item = self.db.get_voting_item(case_number)
        
        if not item:
            QMessageBox.critical(self, "錯誤", "找不到投票項目")
            return
        
        dialog = VotingItemEditDialog(
            self, 
            mode='edit',
            case_number=case_number,
            name=item.get('name', ''),
            description=item.get('description', ''),
            vote_type=item.get('vote_type', '一般議案'),
            pass_percentage=item.get('pass_percentage', 66.7)
        )
        
        if dialog.exec():
            new_name, new_description, new_vote_type, new_pass_percentage = dialog.get_edit_values()
            
            if self.db.update_voting_item(case_number, new_name, new_description, new_vote_type, new_pass_percentage):
                QMessageBox.information(self, "成功", "投票項目已更新")
                self.load_voting_items()
            else:
                QMessageBox.critical(self, "錯誤", "更新失敗")
    
    def delete_voting_item(self, case_number):
        """刪除投票項目"""
        reply = QMessageBox.question(
            self, "確認",
            f"確定要刪除第 {case_number} 案嗎？\n\n此操作將同時刪除所有相關的投票記錄。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_voting_item(case_number):
                QMessageBox.information(self, "成功", "投票項目已刪除")
                self.load_voting_items()
            else:
                QMessageBox.critical(self, "錯誤", "刪除失敗")
    
    def start_voting_session(self):
        """開始投票刷票"""
        items = self.db.get_all_voting_items()
        
        if not items:
            QMessageBox.warning(self, "警告", "沒有投票項目，請先添加投票項目")
            return
        
        # 打開投票刷票窗口
        self.voting_session = VotingSessionWindow(self)
        self.voting_session.setWindowTitle("投票刷票系統")
        self.voting_session.show()


class VotingItemEditDialog(QDialog):
    """投票項目編輯對話框 - 支持編輯投票種類和通過百分比"""
    
    def __init__(self, parent=None, mode='new', case_number='', name='', description='',
                 vote_type='一般議案', pass_percentage=66.7):
        """初始化"""
        super().__init__(parent)
        self.mode = mode
        self.case_number = case_number
        
        if mode == 'new':
            self.setWindowTitle("新增投票項目")
        else:
            self.setWindowTitle("編輯投票項目")
        
        self.setGeometry(100, 100, 500, 500)
        
        layout = QFormLayout()
        
        # 案號（新增時編輯，編輯時不可編輯）
        self.case_number_input = QLineEdit()
        self.case_number_input.setText(case_number)
        self.case_number_input.setEnabled(mode == 'new')
        self.case_number_input.setPlaceholderText("例：1、2、3 或 A、B、C")
        layout.addRow("案號:", self.case_number_input)
        
        # 案名
        self.name_input = QLineEdit()
        self.name_input.setText(name)
        self.name_input.setPlaceholderText("例：物業費調整")
        layout.addRow("案名:", self.name_input)
        
        # 描述
        self.description_input = QLineEdit()
        self.description_input.setText(description)
        self.description_input.setPlaceholderText("例：擬調整2026年度費用")
        layout.addRow("描述:", self.description_input)
        
        layout.addRow("", QLabel(""))  # 空行
        
        # 投票種類標籤
        layout.addRow("投票設定:", QLabel(""))
        
        # 投票種類
        self.vote_type_combo = QComboBox()
        self.vote_type_combo.addItems(["重大議案", "一般議案"])
        self.vote_type_combo.setCurrentText(vote_type)
        layout.addRow("  投票種類:", self.vote_type_combo)
        
        # 通過百分比
        pass_percentage_layout = QHBoxLayout()
        self.pass_percentage_spinbox = QDoubleSpinBox()
        self.pass_percentage_spinbox.setMinimum(50)
        self.pass_percentage_spinbox.setMaximum(100)
        self.pass_percentage_spinbox.setSingleStep(0.1)
        self.pass_percentage_spinbox.setValue(pass_percentage)
        self.pass_percentage_spinbox.setSuffix(" %")
        pass_percentage_layout.addWidget(self.pass_percentage_spinbox)
        pass_percentage_layout.addWidget(QLabel("(50 ~ 100)"))
        pass_percentage_layout.addStretch()
        layout.addRow("  通過百分比:", pass_percentage_layout)
        
        layout.addRow("", QLabel(""))  # 空行
        
        # 說明文字
        if mode == 'edit':
            info_label = QLabel("💡 提示：編輯此項目將不會影響已投票的記錄")
            info_label.setStyleSheet("color: blue; font-size: 9pt;")
            layout.addRow("", info_label)
        
        layout.addRow("", QLabel(""))  # 空行
        
        # 按鈕
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("✓ 保存")
        save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("✕ 取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addRow("", button_layout)
        
        self.setLayout(layout)
    
    def get_values(self):
        """獲取表單值（新增模式）"""
        return (
            self.case_number_input.text().strip(),
            self.name_input.text().strip(),
            self.description_input.text().strip(),
            self.vote_type_combo.currentText(),
            self.pass_percentage_spinbox.value()
        )
    
    def get_edit_values(self):
        """獲取表單值（編輯模式）"""
        return (
            self.name_input.text().strip(),
            self.description_input.text().strip(),
            self.vote_type_combo.currentText(),
            self.pass_percentage_spinbox.value()
        )
