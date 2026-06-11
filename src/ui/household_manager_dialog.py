"""
住戶管理對話框
"""
import csv
from pathlib import Path
from typing import List, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.backend.database import Database


class HouseholdManagerDialog(QDialog):
    """住戶管理對話框"""
    
    def __init__(self, parent=None):
        """初始化住戶管理對話框"""
        super().__init__(parent)
        self.setWindowTitle("住戶管理")
        self.setGeometry(100, 100, 900, 600)
        
        self.db = Database()
        
        self.init_ui()
        self.load_households()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("住戶管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 搜索和過濾區域
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜尋戶號:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("輸入戶號進行搜尋...")
        self.search_input.textChanged.connect(self.filter_households)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        main_layout.addLayout(search_layout)
        
        # 住戶表格
        self.household_table = QTableWidget()
        self.household_table.setColumnCount(2)
        self.household_table.setHorizontalHeaderLabels(["戶號", "姓名"])
        self.household_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.household_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.household_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.household_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        main_layout.addWidget(self.household_table)
        
        # 按鈕區域
        button_layout = QHBoxLayout()
        
        # 添加按鈕
        add_button = QPushButton("新增住戶")
        add_button.clicked.connect(self.add_household)
        button_layout.addWidget(add_button)
        
        # 編輯按鈕
        edit_button = QPushButton("編輯住戶")
        edit_button.clicked.connect(self.edit_household)
        button_layout.addWidget(edit_button)
        
        # 刪除按鈕
        delete_button = QPushButton("刪除住戶")
        delete_button.clicked.connect(self.delete_household)
        button_layout.addWidget(delete_button)
        
        # 添加分隔空間
        button_layout.addSpacing(20)
        
        # 導入按鈕
        import_button = QPushButton("導入住戶（CSV）")
        import_button.clicked.connect(self.import_households)
        button_layout.addWidget(import_button)
        
        # 導出按鈕
        export_button = QPushButton("導出住戶（CSV）")
        export_button.clicked.connect(self.export_households)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        
        # 關閉按鈕
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 保存所有住戶數據以供搜尋
        self.all_households = []
    
    def load_households(self):
        """加載所有住戶"""
        self.all_households = self.db.get_all_households()
        self.refresh_table(self.all_households)
    
    def refresh_table(self, households: List[Dict]):
        """刷新表格顯示"""
        self.household_table.setRowCount(0)
        
        for household in households:
            row_position = self.household_table.rowCount()
            self.household_table.insertRow(row_position)
            
            # 戶號
            self.household_table.setItem(
                row_position, 0,
                QTableWidgetItem(household['household_id'])
            )
            # 姓名
            self.household_table.setItem(
                row_position, 1,
                QTableWidgetItem(household['name'])
            )
    
    def filter_households(self):
        """根據搜尋條件過濾住戶"""
        search_text = self.search_input.text().strip().lower()
        
        if not search_text:
            self.refresh_table(self.all_households)
            return
        
        filtered = [
            h for h in self.all_households
            if search_text in h['household_id'].lower() or
               search_text in h['name'].lower()
        ]
        
        self.refresh_table(filtered)
    
    def add_household(self):
        """添加新住戶"""
        # 輸入戶號
        household_id, ok = QInputDialog.getText(
            self, "新增住戶", "請輸入戶號:"
        )
        
        if not ok or not household_id.strip():
            return
        
        household_id = household_id.strip()
        
        # 檢查戶號是否已存在
        if self.db.get_household(household_id):
            QMessageBox.warning(self, "警告", f"戶號 {household_id} 已存在")
            return
        
        # 輸入姓名
        name, ok = QInputDialog.getText(
            self, "新增住戶", "請輸入住戶姓名:"
        )
        
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        # 添加到數據庫
        if self.db.add_household(household_id, name):
            QMessageBox.information(self, "成功", f"住戶 {household_id} ({name}) 已新增")
            self.load_households()
            self.search_input.clear()
        else:
            QMessageBox.critical(self, "錯誤", "添加住戶失敗")
    
    def edit_household(self):
        """編輯選中的住戶"""
        selected_rows = self.household_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "請選擇要編輯的住戶")
            return
        
        row = selected_rows[0].row()
        household_id = self.household_table.item(row, 0).text()
        current_name = self.household_table.item(row, 1).text()
        
        # 編輯姓名
        new_name, ok = QInputDialog.getText(
            self, "編輯住戶", "請輸入新的住戶姓名:",
            text=current_name
        )
        
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # 更新數據庫
        if self.db.update_household(household_id, new_name):
            QMessageBox.information(self, "成功", f"住戶 {household_id} 姓名已更新為 {new_name}")
            self.load_households()
            self.search_input.clear()
        else:
            QMessageBox.critical(self, "錯誤", "編輯住戶失敗")
    
    def delete_household(self):
        """刪除選中的住戶"""
        selected_rows = self.household_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "請選擇要刪除的住戶")
            return
        
        row = selected_rows[0].row()
        household_id = self.household_table.item(row, 0).text()
        name = self.household_table.item(row, 1).text()
        
        # 確認刪除
        reply = QMessageBox.question(
            self, "確認刪除",
            f"確定要刪除住戶 {household_id} ({name}) 嗎？\n\n"
            f"此操作將同時刪除該住戶的所有報到和投票記錄。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 從數據庫刪除
        if self.db.delete_household(household_id):
            QMessageBox.information(self, "成功", f"住戶 {household_id} 已刪除")
            self.load_households()
            self.search_input.clear()
        else:
            QMessageBox.critical(self, "錯誤", "刪除住戶失敗")
    
    def import_households(self):
        """從 CSV 文件導入住戶"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇住戶 CSV 文件",
            "",
            "CSV 文件 (*.csv);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            households = []
            
            # 讀取 CSV 文件
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # 檢查必要的列
                if not reader.fieldnames or 'household_id' not in reader.fieldnames or 'name' not in reader.fieldnames:
                    QMessageBox.critical(
                        self, "錯誤",
                        "CSV 文件必須包含 'household_id' 和 'name' 列"
                    )
                    return
                
                for row in reader:
                    household_id = row['household_id'].strip()
                    name = row['name'].strip()
                    
                    if household_id and name:
                        households.append({
                            'household_id': household_id,
                            'name': name
                        })
            
            if not households:
                QMessageBox.warning(self, "警告", "CSV 文件中沒有有效的住戶數據")
                return
            
            # 導入住戶
            success, failed = self.db.import_households(households)
            
            QMessageBox.information(
                self, "導入完成",
                f"成功導入 {success} 個住戶\n"
                f"失敗 {failed} 個（可能是戶號重複）"
            )
            
            self.load_households()
            self.search_input.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"導入失敗: {str(e)}")
    
    def export_households(self):
        """導出住戶到 CSV 文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存住戶 CSV 文件",
            "households.csv",
            "CSV 文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            households = self.db.get_all_households()
            
            if not households:
                QMessageBox.warning(self, "警告", "沒有住戶數據可導出")
                return
            
            # 寫入 CSV 文件
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['household_id', 'name', 'status', 'created_at'])
                writer.writeheader()
                
                for household in households:
                    writer.writerow({
                        'household_id': household['household_id'],
                        'name': household['name'],
                        'status': household.get('status', ''),
                        'created_at': household.get('created_at', '')
                    })
            
            QMessageBox.information(
                self, "成功",
                f"已導出 {len(households)} 個住戶到 {file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"導出失敗: {str(e)}")
