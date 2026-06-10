"""
條碼打印對話框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

from src.backend.barcode_generator import BarcodeGenerator
from src.backend.config_manager import ConfigManager


class BarcodePrintDialog(QDialog):
    """條碼打印對話框"""
    
    def __init__(self, parent=None):
        """初始化條碼打印對話框"""
        super().__init__(parent)
        self.setWindowTitle("生成和打印條碼")
        self.setGeometry(100, 100, 400, 200)
        
        self.config_manager = ConfigManager()
        self.barcode_generator = BarcodeGenerator()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # 參與人數
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("生成條碼數量:"))
        
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(10000)
        self.count_input.setValue(
            self.config_manager.get_config('total_participants', 100)
        )
        count_layout.addWidget(self.count_input)
        count_layout.addStretch()
        
        main_layout.addLayout(count_layout)
        
        # 條碼前綴
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("條碼前綴:"))
        self.prefix_display = QLabel(
            self.config_manager.get_config('barcode_prefix', 'VOTER')
        )
        prefix_layout.addWidget(self.prefix_display)
        prefix_layout.addStretch()
        
        main_layout.addLayout(prefix_layout)
        
        # 說明
        info_label = QLabel(
            "條碼將以 [前綴][序號] 的格式生成\n"
            "例如: VOTER00001, VOTER00002, ..."
        )
        main_layout.addWidget(info_label)
        
        main_layout.addStretch()
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        
        generate_button = QPushButton("生成條碼")
        generate_button.clicked.connect(self.generate_barcodes)
        button_layout.addWidget(generate_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def generate_barcodes(self):
        """生成條碼"""
        count = self.count_input.value()
        prefix = self.config_manager.get_config('barcode_prefix', 'VOTER')
        
        # 生成條碼數據
        barcodes = self.barcode_generator.generate_voter_barcodes(count, prefix)
        
        try:
            # 批量生成條碼圖片
            self.barcode_generator.generate_batch_barcodes(barcodes)
            
            QMessageBox.information(
                self, "成功",
                f"已生成 {count} 個條碼\n"
                f"條碼圖片已保存到: exports/barcodes/"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"條碼生成失敗: {e}")
