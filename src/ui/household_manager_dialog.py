"""
住戶管理對話框

功能：
- 新增住戶（戶號 + 姓名）
- 刪除住戶
- 批量匯入住戶（CSV 格式）
- 查看住戶列表
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt

from src.backend.database import Database


class HouseholdManagerDialog(QDialog):
    """住戶管理對話框"""

    def __init__(self, parent=None):
        """初始化住戶管理對話框"""
        super().__init__(parent)
        self.setWindowTitle("住戶管理")
        self.setGeometry(100, 100, 700, 500)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()

        # 新增住戶
        add_group_label = QLabel("新增住戶")
        add_group_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        main_layout.addWidget(add_group_label)

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("戶號:"))
        self.household_id_input = QLineEdit()
        self.household_id_input.setPlaceholderText("例如: 06-02F")
        self.household_id_input.setMaximumWidth(120)
        add_layout.addWidget(self.household_id_input)

        add_layout.addWidget(QLabel("姓名:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: 李某某")
        add_layout.addWidget(self.name_input)

        add_button = QPushButton("新增")
        add_button.clicked.connect(self.add_household)
        add_layout.addWidget(add_button)
        main_layout.addLayout(add_layout)

        # 批量匯入說明
        batch_label = QLabel("批量匯入（每行格式：戶號,姓名）")
        batch_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 8px;")
        main_layout.addWidget(batch_label)

        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText(
            "06-01A,李明\n"
            "06-02F,王美\n"
            "20-02F,張三"
        )
        self.batch_input.setMaximumHeight(80)
        main_layout.addWidget(self.batch_input)

        batch_btn_layout = QHBoxLayout()
        batch_import_button = QPushButton("批量匯入")
        batch_import_button.clicked.connect(self.batch_import)
        batch_btn_layout.addWidget(batch_import_button)

        import_csv_button = QPushButton("從 CSV 文件匯入")
        import_csv_button.clicked.connect(self.import_from_csv)
        batch_btn_layout.addWidget(import_csv_button)

        batch_btn_layout.addStretch()
        main_layout.addLayout(batch_btn_layout)

        # 住戶列表
        list_label = QLabel("住戶列表")
        list_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 8px;")
        main_layout.addWidget(list_label)

        self.households_table = QTableWidget()
        self.households_table.setColumnCount(4)
        self.households_table.setHorizontalHeaderLabels(
            ["戶號", "姓名", "狀態", "操作"]
        )
        self.households_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.households_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.households_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.households_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        main_layout.addWidget(self.households_table)

        # 按鈕佈局
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_households)
        button_layout.addWidget(refresh_button)

        clear_button = QPushButton("清空所有住戶")
        clear_button.setStyleSheet("color: red;")
        clear_button.clicked.connect(self.clear_all_households)
        button_layout.addWidget(clear_button)

        button_layout.addStretch()

        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.refresh_households()

    def add_household(self):
        """新增單個住戶"""
        household_id = self.household_id_input.text().strip().upper()
        name = self.name_input.text().strip()

        if not household_id:
            QMessageBox.warning(self, "警告", "請輸入戶號")
            return
        if not name:
            QMessageBox.warning(self, "警告", "請輸入姓名")
            return

        if self.db.add_household(household_id, name):
            self.household_id_input.clear()
            self.name_input.clear()
            self.refresh_households()
            QMessageBox.information(self, "成功", f"住戶 {household_id}（{name}）已新增")
        else:
            QMessageBox.warning(self, "警告", f"戶號 {household_id} 已存在")

    def batch_import(self):
        """批量匯入住戶"""
        text = self.batch_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "請輸入住戶資料")
            return

        households = []
        errors = []
        for line_num, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 2:
                errors.append(f"第 {line_num} 行格式錯誤：{line}")
                continue
            household_id = parts[0].strip().upper()
            name = parts[1].strip()
            if not household_id or not name:
                errors.append(f"第 {line_num} 行資料不完整：{line}")
                continue
            households.append({'household_id': household_id, 'name': name})

        if errors:
            QMessageBox.warning(self, "格式錯誤", "\n".join(errors))
            return

        success, failed = self.db.import_households(households)
        self.batch_input.clear()
        self.refresh_households()
        QMessageBox.information(
            self, "匯入完成",
            f"成功匯入：{success} 筆\n"
            f"失敗（重複戶號）：{failed} 筆"
        )

    def import_from_csv(self):
        """從 CSV 文件匯入住戶"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇 CSV 文件", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return

        try:
            households = []
            errors = []
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or (line_num == 1 and '戶號' in line):
                        continue  # 跳過空行和標題行
                    parts = line.split(",")
                    if len(parts) < 2:
                        errors.append(f"第 {line_num} 行格式錯誤：{line}")
                        continue
                    household_id = parts[0].strip().upper()
                    name = parts[1].strip()
                    if household_id and name:
                        households.append({'household_id': household_id, 'name': name})

            if errors:
                QMessageBox.warning(self, "格式錯誤", "\n".join(errors[:10]))

            success, failed = self.db.import_households(households)
            self.refresh_households()
            QMessageBox.information(
                self, "匯入完成",
                f"成功匯入：{success} 筆\n"
                f"失敗（重複戶號）：{failed} 筆"
            )
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"文件讀取失敗：{e}")

    def refresh_households(self):
        """刷新住戶列表"""
        self.households_table.setRowCount(0)
        households = self.db.get_all_households()

        status_map = {'pending': '待報到', 'checked_in': '已報到', 'voted': '已投票'}

        for row_idx, h in enumerate(households):
            self.households_table.insertRow(row_idx)
            self.households_table.setItem(row_idx, 0, QTableWidgetItem(h['household_id']))
            self.households_table.setItem(row_idx, 1, QTableWidgetItem(h['name']))
            self.households_table.setItem(
                row_idx, 2,
                QTableWidgetItem(status_map.get(h['status'], h['status']))
            )

            delete_button = QPushButton("刪除")
            delete_button.clicked.connect(
                lambda checked, hid=h['household_id']: self.delete_household(hid)
            )
            self.households_table.setCellWidget(row_idx, 3, delete_button)

    def delete_household(self, household_id: str):
        """刪除住戶"""
        reply = QMessageBox.question(
            self, "確認", f"確定要刪除戶號 {household_id} 嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_household(household_id):
                self.refresh_households()
            else:
                QMessageBox.critical(self, "錯誤", "刪除失敗")

    def clear_all_households(self):
        """清空所有住戶"""
        reply = QMessageBox.question(
            self, "確認", "確定要清空所有住戶資料嗎？此操作不可恢復！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM check_in_records")
            cursor.execute("DELETE FROM votes")
            cursor.execute("DELETE FROM households")
            conn.commit()
            conn.close()
            self.refresh_households()
            QMessageBox.information(self, "成功", "所有住戶資料已清空")
