"""
條碼打印對話框
"""
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from src.backend.barcode_generator import BarcodeGenerator
from src.backend.database import Database


class BarcodePrintDialog(QDialog):
    """條碼打印對話框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("生成和打印條碼")
        self.setGeometry(100, 100, 420, 220)

        self.db = Database()
        self.barcode_generator = BarcodeGenerator()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.count_label = QLabel()
        main_layout.addWidget(self.count_label)

        info_label = QLabel(
            "將依資料庫中的戶號生成 Code39 條碼圖片\n"
            "條碼內容會直接使用戶號，例如：06-02F"
        )
        main_layout.addWidget(info_label)
        main_layout.addStretch()

        button_layout = QHBoxLayout()
        generate_button = QPushButton("生成全部戶號條碼")
        generate_button.clicked.connect(self.generate_barcodes)
        button_layout.addWidget(generate_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.refresh_count()

    def refresh_count(self):
        voter_count = len(self.db.get_voters())
        self.count_label.setText(f"目前已匯入戶號數量：{voter_count}")

    def generate_barcodes(self):
        household_ids = [voter['household_id'] for voter in self.db.get_voters()]
        if not household_ids:
            QMessageBox.warning(self, "警告", "目前沒有戶號資料，請先匯入投票者 CSV")
            return

        barcodes = self.barcode_generator.generate_voter_barcodes(household_ids)
        try:
            self.barcode_generator.generate_batch_barcodes(barcodes)
            QMessageBox.information(
                self,
                "成功",
                f"已生成 {len(barcodes)} 個 Code39 條碼\n條碼圖片已保存到: exports/barcodes/",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"條碼生成失敗: {e}")
