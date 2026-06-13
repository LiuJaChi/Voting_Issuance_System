"""
報到記錄匯入對話框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QLineEdit, QComboBox, QTextEdit
)

from src.backend.database import Database


class ImportCheckInDialog(QDialog):
    """報到記錄匯入對話框"""

    def __init__(self, db: Database = None, parent=None):
        super().__init__(parent)
        self.db = db or Database()

        self.setWindowTitle("導入報到記錄")
        self.resize(640, 420)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("匯入文件:"))
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        file_layout.addWidget(self.file_path_input)

        browse_button = QPushButton("選擇文件")
        browse_button.clicked.connect(self.select_file)
        file_layout.addWidget(browse_button)
        main_layout.addLayout(file_layout)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("匯入模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("合併（略過已存在報到記錄）", "merge")
        self.mode_combo.addItem("替換（清空後重建報到記錄）", "replace")
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        self.imported_label = QLabel("已導入記錄數：0")
        self.stats_label = QLabel("成功：0　失敗：0　重複：0")
        main_layout.addWidget(self.imported_label)
        main_layout.addWidget(self.stats_label)

        main_layout.addWidget(QLabel("詳細錯誤信息："))
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setPlaceholderText("暫無錯誤")
        main_layout.addWidget(self.error_text)

        button_layout = QHBoxLayout()
        self.import_button = QPushButton("開始導入")
        self.import_button.clicked.connect(self.import_data)
        button_layout.addWidget(self.import_button)
        button_layout.addStretch()

        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇報到記錄文件",
            "",
            "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)"
        )

        if file_path:
            self.file_path_input.setText(file_path)

    def import_data(self):
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "請先選擇要導入的文件")
            return

        mode = self.mode_combo.currentData()
        result = self.db.import_check_in_data(file_path, mode)

        self.imported_label.setText(f"已導入記錄數：{result.get('success_count', 0)}")
        self.stats_label.setText(
            f"成功：{result.get('success_count', 0)}　"
            f"失敗：{result.get('failed_count', 0)}　"
            f"重複：{result.get('duplicate_count', 0)}"
        )

        errors = result.get('errors', [])
        if errors:
            self.error_text.setPlainText("\n".join(errors))
        else:
            self.error_text.setPlainText("無錯誤")

        if errors:
            QMessageBox.warning(self, "導入完成（含錯誤）", "\n".join(result.get('messages', [])))
        else:
            QMessageBox.information(self, "成功", "\n".join(result.get('messages', ["導入完成"]))
            )
