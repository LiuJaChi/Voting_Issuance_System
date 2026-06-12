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
from src.backend.config_manager import ConfigManager
from src.backend.data_merger import DataMerger
import json


class ResultsWindow(QWidget):
    """結果統計窗口"""
    
    def __init__(self, parent=None):
        """初始化結果統計窗口"""
        super().__init__(parent)
        self.db = Database()
        self.config_manager = ConfigManager()
        
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
        
        # 結果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "投票項目", "贊成票", "反對票", "投票人數", "贊成率(%)", "結果"
        ])
        
        self.results_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
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
        
        export_button = QPushButton("導出結果")
        export_button.clicked.connect(self.export_results)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        self.refresh_results()
    
    def refresh_results(self):
        """刷新投票結果"""
        self.results_table.setRowCount(0)
        
        # 從配置管理器獲取通過百分比
        pass_percentage = self.config_manager.get_config('pass_percentage', 66.7)
        
        # 獲取所有投票項目
        voting_items = self.db.get_all_voting_items()
        
        if not voting_items:
            QMessageBox.warning(self, "警告", "沒有投票項目資料")
            return
        
        row_idx = 0
        for item in voting_items:
            case_number = item['case_number']
            item_name = item['name']
            
            # 獲取投票結果
            results = self.db.get_voting_results(case_number)
            
            yes_count = results.get('yes', 0)
            no_count = results.get('no', 0)
            total = yes_count + no_count
            
            yes_percentage = (yes_count / total * 100) if total > 0 else 0
            passed = "✓ 通過" if yes_percentage >= pass_percentage else "✗ 未通過"
            
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
            try:
                with open("exports/merged_data.json", 'r', encoding='utf-8') as f:
                    merged_data = json.load(f)
                
                # 獲取通過百分比
                pass_percentage = self.config_manager.get_config('pass_percentage', 66.7)
                
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
            QMessageBox.critical(self, "錯誤", "結果導出失敗")
