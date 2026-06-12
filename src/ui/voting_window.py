"""
投票窗口 - 支持投票項目管理和投票刷票

功能：
1. 投票項目管理（項次、案名、投票種類、通過百分比）
2. 投票結果統計（右側即時顯示）
3. 投票刷票（選擇選項 + 掃描條碼）
4. 分類統計（按投票選項分類顯示）
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
        
        new_item_button = QPushButton("新增投票項目")
        new_item_button.clicked.connect(self.add_voting_item)
        button_layout.addWidget(new_item_button)
        
        edit_item_button = QPushButton("編輯投票項目")
        edit_item_button.clicked.connect(self.edit_voting_item)
        button_layout.addWidget(edit_item_button)
        
        delete_item_button = QPushButton("刪除投票項目")
        delete_item_button.clicked.connect(self.delete_voting_item)
        button_layout.addWidget(delete_item_button)
        
        button_layout.addStretch()
        
        # 開始投票按鈕
        start_voting_button = QPushButton("🗳️ 開始投票")
        start_voting_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        start_voting_button.clicked.connect(self.start_voting_session)
        button_layout.addWidget(start_voting_button)
        
        main_layout.addLayout(button_layout)
        
        # 投票項目表
        self.voting_table = QTableWidget()
        self.voting_table.setColumnCount(4)
        self.voting_table.setHorizontalHeaderLabels(
            ["項次", "案名", "投票種類", "通過百分比(%)"]
        )
        self.voting_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.voting_table.setMaximumHeight(200)
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
            
            # 項次
            case_number_item = QTableWidgetItem(item['case_number'])
            
            # 案名
            name_item = QTableWidgetItem(item['name'])
            
            # 投票種類（暫時使用固定值，可後續擴展）
            vote_type_item = QTableWidgetItem("三項（同意/反對/棄權）")
            
            # 通過百分比（使用系統配置或默認值）
            pass_percentage = self.config_manager.get_config('pass_percentage', 66.7)
            pass_percentage_item = QTableWidgetItem(f"{pass_percentage:.1f}")
            
            self.voting_table.setItem(row_idx, 0, case_number_item)
            self.voting_table.setItem(row_idx, 1, name_item)
            self.voting_table.setItem(row_idx, 2, vote_type_item)
            self.voting_table.setItem(row_idx, 3, pass_percentage_item)
        
        # 刷新投票結果
        self.refresh_voting_results()
    
    def refresh_voting_results(self):
        """刷新投票結果統計"""
        self.result_table.setRowCount(0)
        
        items = self.db.get_all_voting_items()
        stats = self.db.get_check_in_stats()
        total_attendees = stats['checked_in']
        pass_percentage = self.config_manager.get_config('pass_percentage', 66.7)
        pass_condition = int(total_attendees * pass_percentage / 100)
        
        for row_idx, item in enumerate(items):
            self.result_table.insertRow(row_idx)
            
            # 獲取投票結果
            result = self.db.get_voting_results(item['case_number'])
            agree_votes = result['votes'].get('同意', 0)
            disagree_votes = result['votes'].get('不同意', 0)
            abstain_votes = result['votes'].get('棄權', 0)
            
            # 項次
            case_number_item = QTableWidgetItem(item['case_number'])
            
            # 案名
            name_item = QTableWidgetItem(item['name'])
            
            # 同意票
            agree_item = QTableWidgetItem(str(agree_votes))
            agree_item.setBackground(QColor(144, 238, 144))  # 淡綠色
            
            # 反對票
            disagree_item = QTableWidgetItem(str(disagree_votes))
            disagree_item.setBackground(QColor(255, 160, 122))  # 淡紅色
            
            # 棄權票
            abstain_item = QTableWidgetItem(str(abstain_votes))
            abstain_item.setBackground(QColor(255, 255, 200))  # 淡黃色
            
            # 通過/不通過判定
            if agree_votes >= pass_condition:
                result_text = "✅ 通過"
                result_item = QTableWidgetItem(result_text)
                result_item.setBackground(QColor(144, 238, 144))  # 綠色背景
            else:
                result_text = "❌ 不通過"
                result_item = QTableWidgetItem(result_text)
                result_item.setBackground(QColor(255, 160, 122))  # 紅色背景
            
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
            case_number, name, description = dialog.get_values()
            
            if self.db.add_voting_item(case_number, name, description):
                QMessageBox.information(self, "成功", "投票項目已添加")
                self.load_voting_items()
            else:
                QMessageBox.critical(self, "錯誤", "投票項目已存在或添加失敗")
    
    def edit_voting_item(self):
        """編輯投票項目"""
        current_row = self.voting_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "請選擇要編輯的投票項目")
            return
        
        case_number = self.voting_table.item(current_row, 0).text()
        name = self.voting_table.item(current_row, 1).text()
        
        item = self.db.get_voting_item(case_number)
        description = item.get('description', '') if item else ''
        
        dialog = VotingItemEditDialog(self, mode='edit', case_number=case_number, name=name, description=description)
        if dialog.exec():
            new_name, new_description = dialog.get_edit_values()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE voting_items SET name = ?, description = ?
                WHERE case_number = ?
            """, (new_name, new_description, case_number))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "成功", "投票項目已更新")
            self.load_voting_items()
    
    def delete_voting_item(self):
        """刪除投票項目"""
        current_row = self.voting_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "請選擇要刪除的投票項目")
            return
        
        case_number = self.voting_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, "確認",
            f"確定要刪除第 {case_number} 案嗎？",
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
    """投票項目編輯對話框"""
    
    def __init__(self, parent=None, mode='new', case_number='', name='', description=''):
        """初始化"""
        super().__init__(parent)
        self.mode = mode
        self.case_number = case_number
        
        if mode == 'new':
            self.setWindowTitle("新增投票項目")
        else:
            self.setWindowTitle("編輯投票項目")
        
        self.setGeometry(100, 100, 400, 300)
        
        layout = QFormLayout()
        
        # 案號（新增時編輯，編輯時不可編輯）
        self.case_number_input = QLineEdit()
        self.case_number_input.setText(case_number)
        self.case_number_input.setEnabled(mode == 'new')
        layout.addRow("案號:", self.case_number_input)
        
        # 案名
        self.name_input = QLineEdit()
        self.name_input.setText(name)
        layout.addRow("案名:", self.name_input)
        
        # 描述
        self.description_input = QLineEdit()
        self.description_input.setText(description)
        layout.addRow("描述:", self.description_input)
        
        # 按鈕
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addRow("", button_layout)
        
        self.setLayout(layout)
    
    def get_values(self):
        """獲取表單值（新增模式）"""
        return (
            self.case_number_input.text(),
            self.name_input.text(),
            self.description_input.text()
        )
    
    def get_edit_values(self):
        """獲取表單值（編輯模式）"""
        return (
            self.name_input.text(),
            self.description_input.text()
        )
