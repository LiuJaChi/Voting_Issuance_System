"""
投票項目管理對話框 - 支持編輯投票種類和通過百分比
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QDoubleSpinBox, QComboBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.backend.database import Database


class VotingItemDialog(QDialog):
    """投票項目管理對話框 - 支持完整的新增/編輯/刪除"""
    
    def __init__(self, parent=None):
        """初始化投票項目管理對話框"""
        super().__init__(parent)
        self.setWindowTitle("投票項目管理")
        self.setGeometry(100, 100, 800, 600)
        
        self.db = Database()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # 新增項目區域
        add_title = QLabel("新增投票項目")
        add_title_font = add_title.font()
        add_title_font.setBold(True)
        add_title.setFont(add_title_font)
        main_layout.addWidget(add_title)
        
        # 新增項目表單
        add_form_layout = QFormLayout()
        
        self.case_number_input = QLineEdit()
        self.case_number_input.setPlaceholderText("例：1、2、3 或 A、B、C")
        add_form_layout.addRow("案號:", self.case_number_input)
        
        self.item_name_input = QLineEdit()
        self.item_name_input.setPlaceholderText("例：物業費調整")
        add_form_layout.addRow("案名:", self.item_name_input)
        
        self.item_desc_input = QLineEdit()
        self.item_desc_input.setPlaceholderText("例：擬調整2026年度費用")
        add_form_layout.addRow("描述:", self.item_desc_input)
        
        self.vote_type_combo = QComboBox()
        self.vote_type_combo.addItems(["重大議案", "一般議案"])
        add_form_layout.addRow("投票種類:", self.vote_type_combo)
        
        self.pass_percentage_spinbox = QDoubleSpinBox()
        self.pass_percentage_spinbox.setMinimum(50)
        self.pass_percentage_spinbox.setMaximum(100)
        self.pass_percentage_spinbox.setSingleStep(0.1)
        self.pass_percentage_spinbox.setValue(66.7)
        self.pass_percentage_spinbox.setSuffix(" %")
        add_form_layout.addRow("通過百分比:", self.pass_percentage_spinbox)
        
        main_layout.addLayout(add_form_layout)
        
        # 新增按鈕
        add_button_layout = QHBoxLayout()
        add_button = QPushButton("+ 新增項目")
        add_button.setStyleSheet("background-color: #4CAF50; color: white;")
        add_button.clicked.connect(self.add_voting_item)
        add_button_layout.addWidget(add_button)
        add_button_layout.addStretch()
        main_layout.addLayout(add_button_layout)
        
        main_layout.addSpacing(10)
        
        # 項目列表區域
        list_title = QLabel("投票項目列表")
        list_title_font = list_title.font()
        list_title_font.setBold(True)
        list_title.setFont(list_title_font)
        main_layout.addWidget(list_title)
        
        # 項目列表表
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(
            ["案號", "案名", "投票種類", "通過百分比(%)", "描述", "編輯", "刪除"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        main_layout.addWidget(self.items_table)
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.refresh_items)
        button_layout.addWidget(refresh_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("✕ 關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        self.refresh_items()
    
    def add_voting_item(self):
        """添加投票項目"""
        case_number = self.case_number_input.text().strip()
        name = self.item_name_input.text().strip()
        description = self.item_desc_input.text().strip()
        vote_type = self.vote_type_combo.currentText()
        pass_percentage = self.pass_percentage_spinbox.value()
        
        if not case_number:
            QMessageBox.warning(self, "警告", "請輸入案號")
            return
        
        if not name:
            QMessageBox.warning(self, "警告", "請輸入案名")
            return
        
        if self.db.add_voting_item(case_number, name, description, vote_type, pass_percentage):
            QMessageBox.information(self, "成功", "投票項目已添加")
            self.case_number_input.clear()
            self.item_name_input.clear()
            self.item_desc_input.clear()
            self.vote_type_combo.setCurrentIndex(0)
            self.pass_percentage_spinbox.setValue(66.7)
            self.refresh_items()
        else:
            QMessageBox.critical(self, "錯誤", "投票項目已存在或添加失敗")
    
    def refresh_items(self):
        """刷新項目列表"""
        self.items_table.setRowCount(0)
        
        items = self.db.get_all_voting_items()
        
        for row_idx, item in enumerate(items):
            self.items_table.insertRow(row_idx)
            
            # 案號
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
            edit_button.clicked.connect(
                lambda checked, case_num=item['case_number']: self.edit_item(case_num)
            )
            
            # 刪除按鈕
            delete_button = QPushButton("🗑️ 刪除")
            delete_button.clicked.connect(
                lambda checked, case_num=item['case_number']: self.delete_item(case_num)
            )
            
            self.items_table.setItem(row_idx, 0, case_number_item)
            self.items_table.setItem(row_idx, 1, name_item)
            self.items_table.setItem(row_idx, 2, vote_type_item)
            self.items_table.setItem(row_idx, 3, pass_percentage_item)
            self.items_table.setItem(row_idx, 4, description_item)
            self.items_table.setCellWidget(row_idx, 5, edit_button)
            self.items_table.setCellWidget(row_idx, 6, delete_button)
    
    def edit_item(self, case_number: str):
        """編輯項目"""
        item = self.db.get_voting_item(case_number)
        
        if not item:
            QMessageBox.critical(self, "錯誤", "找不到投票項目")
            return
        
        # 打開編輯對話框
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
            new_name, new_description, new_vote_type, new_pass_percentage = dialog.get_values()
            
            if self.db.update_voting_item(case_number, new_name, new_description, new_vote_type, new_pass_percentage):
                QMessageBox.information(self, "成功", "投票項目已更新")
                self.refresh_items()
            else:
                QMessageBox.critical(self, "錯誤", "更新失敗")
    
    def delete_item(self, case_number: str):
        """刪除項目"""
        reply = QMessageBox.question(
            self, "確認",
            f"確定要刪除第 {case_number} 案嗎？\n\n此操作將同時刪除所有相關的投票記錄。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_voting_item(case_number):
                QMessageBox.information(self, "成功", "投票項目已刪除")
                self.refresh_items()
            else:
                QMessageBox.critical(self, "錯誤", "刪除失敗")


class VotingItemEditDialog(QDialog):
    """投票項目編輯對話框"""
    
    def __init__(self, parent=None, mode='edit', case_number='', name='', description='',
                 vote_type='一般議案', pass_percentage=66.7):
        """初始化"""
        super().__init__(parent)
        self.setWindowTitle("編輯投票項目")
        self.setGeometry(100, 100, 500, 400)
        
        self.mode = mode
        self.case_number = case_number
        
        layout = QFormLayout()
        
        # 案號（只讀）
        case_number_label = QLabel(case_number)
        layout.addRow("案號:", case_number_label)
        
        # 案名
        self.name_input = QLineEdit()
        self.name_input.setText(name)
        layout.addRow("案名:", self.name_input)
        
        # 描述
        self.description_input = QLineEdit()
        self.description_input.setText(description)
        layout.addRow("描述:", self.description_input)
        
        layout.addRow("", QLabel(""))  # 空行
        
        # 投票設定標籤
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
        
        # 提示信息
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
        """獲取表單值"""
        return (
            self.name_input.text().strip(),
            self.description_input.text().strip(),
            self.vote_type_combo.currentText(),
            self.pass_percentage_spinbox.value()
        )
