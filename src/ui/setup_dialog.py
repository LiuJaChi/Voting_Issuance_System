"""
系統設置對話框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QPushButton, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.backend.config_manager import ConfigManager


class SetupDialog(QDialog):
    """系統設置對話框"""
    
    # 設置變更信號
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化系統設置對話框"""
        super().__init__(parent)
        self.setWindowTitle("系統設置")
        self.setGeometry(100, 100, 500, 400)
        
        self.config_manager = ConfigManager()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用戶界面"""
        layout = QVBoxLayout()
        
        # 創建表單佈局
        form_layout = QFormLayout()
        
        # 系統名稱
        self.system_name_input = QLineEdit()
        self.system_name_input.setText(
            self.config_manager.get_config('system_name', '投票系統')
        )
        form_layout.addRow("系統名稱:", self.system_name_input)
        
        # 參與人數
        self.total_participants_input = QSpinBox()
        self.total_participants_input.setMinimum(1)
        self.total_participants_input.setMaximum(10000)
        self.total_participants_input.setValue(
            self.config_manager.get_config('total_participants', 100)
        )
        form_layout.addRow("預期參與人數:", self.total_participants_input)
        
        # 投票通過百分比
        self.pass_percentage_input = QDoubleSpinBox()
        self.pass_percentage_input.setMinimum(0)
        self.pass_percentage_input.setMaximum(100)
        self.pass_percentage_input.setSingleStep(0.1)
        self.pass_percentage_input.setValue(
            self.config_manager.get_config('pass_percentage', 66.7)
        )
        form_layout.addRow("通過百分比(%):", self.pass_percentage_input)
        
        # 條碼前綴
        self.barcode_prefix_input = QLineEdit()
        self.barcode_prefix_input.setText(
            self.config_manager.get_config('barcode_prefix', 'VOTER')
        )
        form_layout.addRow("條碼前綴:", self.barcode_prefix_input)
        
        # 設備 ID
        self.device_id_input = QLineEdit()
        self.device_id_input.setText(
            self.config_manager.get_config('device_id', 'DEVICE_001')
        )
        form_layout.addRow("設備 ID:", self.device_id_input)
        
        layout.addLayout(form_layout)
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_config(self):
        """保存配置"""
        config = {
            'system_name': self.system_name_input.text(),
            'total_participants': self.total_participants_input.value(),
            'pass_percentage': self.pass_percentage_input.value(),
            'barcode_prefix': self.barcode_prefix_input.text(),
            'device_id': self.device_id_input.text(),
            'theme': self.config_manager.get_config('theme', 'light'),
            'language': self.config_manager.get_config('language', 'zh_TW')
        }
        
        try:
            if self.config_manager.save_config(config):
                QMessageBox.information(self, "成功", "配置已保存")
                
                # 發出設置變更信號
                self.settings_changed.emit()
                print("✓ 設置變更信號已發送")
                
                self.accept()
            else:
                QMessageBox.critical(self, "錯誤", "配置保存失敗")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"配置保存失敗: {e}")
