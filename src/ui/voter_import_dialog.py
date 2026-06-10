"""
投票者匯入對話框
"""
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.backend.database import Database


class VoterImportDialog(QDialog):
    """投票者 CSV 匯入對話框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("匯入投票者 CSV")
        self.setGeometry(100, 100, 520, 200)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("CSV 欄位需包含 household_id/戶號 與 name/姓名。"))

        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("請選擇 CSV 檔案")
        file_layout.addWidget(self.file_input)

        browse_button = QPushButton("瀏覽")
        browse_button.clicked.connect(self.select_file)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)

        button_layout = QHBoxLayout()
        import_button = QPushButton("匯入")
        import_button.clicked.connect(self.import_voters)
        button_layout.addWidget(import_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇投票者 CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.file_input.setText(file_path)

    def import_voters(self):
        file_path = self.file_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "請先選擇 CSV 檔案")
            return

        try:
            inserted, skipped = self.db.import_voters_from_csv(file_path)
            QMessageBox.information(self, "成功", f"匯入完成\n新增：{inserted} 筆\n略過：{skipped} 筆")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯入失敗: {e}")
