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
    """結果統計窗口（按戶號和案號統計）"""

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

        # 統計摘要
        summary_layout = QHBoxLayout()
        self.total_households_label = QLabel("總住戶數: 0")
        self.checked_in_label = QLabel("已報到: 0")
        self.total_votes_label = QLabel("總投票數: 0")
        summary_layout.addWidget(self.total_households_label)
        summary_layout.addWidget(self.checked_in_label)
        summary_layout.addWidget(self.total_votes_label)
        summary_layout.addStretch()
        main_layout.addLayout(summary_layout)

        # 結果表（按案號統計）
        result_title = QLabel("各案號投票結果")
        result_title.setStyleSheet("font-weight: bold; margin-top: 8px;")
        main_layout.addWidget(result_title)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(
            ["案號", "項目名稱", "贊成", "反對", "總計", "贊成率(%)", "是否通過"]
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for col in [0, 2, 3, 4, 5, 6]:
            self.results_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents
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
        self.refresh_results()

    def refresh_results(self):
        """刷新投票結果"""
        self.results_table.setRowCount(0)

        # 更新摘要
        stats = self.db.get_check_in_stats()
        self.total_households_label.setText(f"總住戶數: {stats.get('total_expected', 0)}")
        self.checked_in_label.setText(f"已報到: {stats.get('checked_in', 0)}")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM votes")
        total_votes = cursor.fetchone()['count']
        conn.close()
        self.total_votes_label.setText(f"總投票數: {total_votes}")

        # 取通過百分比設定
        config = self.db.get_config()
        pass_percentage = config['pass_percentage'] if config else 66.7

        # 獲取所有投票項目的結果
        all_results = self.db.get_all_voting_results()

        row_idx = 0
        for result in all_results:
            if not result:
                continue

            case_number = result.get('case_number', '')
            item_name = result.get('item_name', '')
            yes_count = result.get('votes', {}).get('yes', 0)
            no_count = result.get('votes', {}).get('no', 0)
            total = yes_count + no_count
            yes_percentage = (yes_count / total * 100) if total > 0 else 0
            passed = "通過" if yes_percentage >= pass_percentage else "未通過"

            self.results_table.insertRow(row_idx)
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(case_number))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(item_name))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(str(yes_count)))
            self.results_table.setItem(row_idx, 3, QTableWidgetItem(str(no_count)))
            self.results_table.setItem(row_idx, 4, QTableWidgetItem(str(total)))
            self.results_table.setItem(row_idx, 5, QTableWidgetItem(f"{yes_percentage:.2f}"))
            self.results_table.setItem(row_idx, 6, QTableWidgetItem(passed))

            row_idx += 1

    def merge_device_data(self):
        """合併多設備數據"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "選擇要合併的數據文件", "", "JSON Files (*.json)"
        )

        if not file_paths:
            return

        if DataMerger.merge_export_files(file_paths):
            try:
                with open("exports/merged_data.json", 'r', encoding='utf-8') as f:
                    merged_data = json.load(f)

                config = self.db.get_config()
                pass_percentage = config['pass_percentage'] if config else 66.7

                results = DataMerger.calculate_voting_results(merged_data, pass_percentage)
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
