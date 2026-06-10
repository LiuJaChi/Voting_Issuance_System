"""
系統設置對話框
"""
from PyQt6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.backend.config_manager import ConfigManager
from src.backend.database import Database


class SetupDialog(QDialog):
    """系統設置對話框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系統設置")
        self.setGeometry(100, 100, 500, 320)
        self.config_manager = ConfigManager()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.system_name_input = QLineEdit()
        self.system_name_input.setText(self.config_manager.get_config('system_name', '投票系統'))
        form_layout.addRow("系統名稱:", self.system_name_input)

        self.total_participants_input = QSpinBox()
        self.total_participants_input.setMinimum(1)
        self.total_participants_input.setMaximum(10000)
        self.total_participants_input.setValue(self.config_manager.get_config('total_participants', 100))
        form_layout.addRow("預期參與人數:", self.total_participants_input)

        self.pass_percentage_input = QDoubleSpinBox()
        self.pass_percentage_input.setMinimum(0)
        self.pass_percentage_input.setMaximum(100)
        self.pass_percentage_input.setSingleStep(0.1)
        self.pass_percentage_input.setValue(self.config_manager.get_config('pass_percentage', 66.7))
        form_layout.addRow("通過百分比(%):", self.pass_percentage_input)

        self.device_id_input = QLineEdit()
        self.device_id_input.setText(self.config_manager.get_config('device_id', 'DEVICE_001'))
        form_layout.addRow("設備 ID:", self.device_id_input)

        layout.addLayout(form_layout)

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
        config = {
            'system_name': self.system_name_input.text(),
            'total_participants': self.total_participants_input.value(),
            'pass_percentage': self.pass_percentage_input.value(),
            'barcode_prefix': self.config_manager.get_config('barcode_prefix', 'VOTER'),
            'device_id': self.device_id_input.text(),
            'theme': self.config_manager.get_config('theme', 'light'),
            'language': self.config_manager.get_config('language', 'zh_TW'),
        }

        if self.config_manager.save_config(config):
            self.db.save_config(config['system_name'], config['total_participants'], config['pass_percentage'])
            QMessageBox.information(self, "成功", "配置已保存")
            self.accept()
        else:
            QMessageBox.critical(self, "錯誤", "配置保存失敗")
