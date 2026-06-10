"""
結果統計窗口
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.backend.database import Database
from src.backend.data_merger import DataMerger
import json


class ResultsWindow(QWidget):
    """結果統計窗口"""
    
    def __init__(self, parent=None):
        """初始化結果統計窗口"""
        super().__init__(parent)
        self.db = Database()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("投票結果統計")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 結果表
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(
            ["項目", "贊成", "反對", "總計", "贊成率(%)", "是否通過"]
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        main_layout.addWidget(self.results_table)
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_results)
        button_layout.addWidget(refresh_button)
        
        merge_button = QPushButton("合併多設備數據")
        merge_button.clicked.connect(self.merge_device_data)
        button_layout.addWidget(merge_button)
        
        export_button = QPushButton("導出結果報告")
        export_button.clicked.connect(self.export_results)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 初始化數據
        self.refresh_results()
    
    def refresh_results(self):
        """刷新投票結果"""
        self.results_table.setRowCount(0)
        
        config = self.db.get_config()
        if not config:
            QMessageBox.warning(self, "警告", "請先進行系統設置")
            return
        
        pass_percentage = config['pass_percentage']
        
        # 獲取所有投票項目
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM voting_items")
        voting_items = cursor.fetchall()
        conn.close()
        
        row_idx = 0
        for item in voting_items:
            item_id = item[0]
            item_name = item[1]
            
            # 獲取投票結果
            results = self.db.get_voting_results(item_id)
            
            yes_count = results.get('votes', {}).get('yes', 0)
            no_count = results.get('votes', {}).get('no', 0)
            total = yes_count + no_count
            
            yes_percentage = (yes_count / total * 100) if total > 0 else 0
            passed = "通過" if yes_percentage >= pass_percentage else "未通過"
            
            self.results_table.insertRow(row_idx)
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(item_name))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(str(yes_count)))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(str(no_count)))
            self.results_table.setItem(row_idx, 3, QTableWidgetItem(str(total)))
            self.results_table.setItem(row_idx, 4, QTableWidgetItem(f"{yes_percentage:.2f}"))
            self.results_table.setItem(row_idx, 5, QTableWidgetItem(passed))
            
            row_idx += 1
    
    def merge_device_data(self):
        """合併多設備數據"""
        # 選擇要合併的文件
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "選擇要合併的數據文件", "", "JSON Files (*.json)"
        )
        
        if not file_paths:
            return
        
        # 合併數據
        if DataMerger.merge_export_files(file_paths):
            # 加載合併後的數據
            try:
                with open("exports/merged_data.json", 'r', encoding='utf-8') as f:
                    merged_data = json.load(f)
                
                config = self.db.get_config()
                pass_percentage = config['pass_percentage'] if config else 66.7
                
                # 計算結果
                results = DataMerger.calculate_voting_results(merged_data, pass_percentage)
                
                # 導出報告
                DataMerger.export_voting_report(results)
                
                QMessageBox.information(
                    self, "成功",
                    "數據已合併\n結果已保存到 exports/merged_data.json 和 exports/voting_report.json"
                )
                
                self.refresh_results()
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"處理數據失敗: {e}")
        else:
            QMessageBox.critical(self, "錯誤", "數據合併失敗")
    
    def export_results(self):
        """導出結果"""
        if self.db.export_data():
            QMessageBox.information(self, "成功", "結果已導出到 exports/data.json")
        else:
            QMessageBox.critical(self, "錯誤", "導出失敗")
