"""
主應用程序入口
"""
import sys
from pathlib import Path

# 設置項目路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """應用入口點"""
    app = QApplication(sys.argv)
    
    # 設置應用程序信息
    app.setApplicationName("投票系統")
    app.setApplicationVersion("1.0.0")
    
    # 創建並顯示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()