"""
住戶管理對話框 - 支持 .xlsx 格式
"""
import csv
from pathlib import Path
from typing import List, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.backend.database import Database

try:
    import openpyxl
    from openpyxl.utils.dataframe import dataframe_to_rows
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False
    # 嘗試用 pandas 作為備選
    try:
        import pandas as pd
        PANDAS_AVAILABLE = True
    except ImportError:
        PANDAS_AVAILABLE = False


class HouseholdManagerDialog(QDialog):
    """住戶管理對話框"""
    
    def __init__(self, parent=None):
        """初始化住戶管理對話框"""
        super().__init__(parent)
        self.setWindowTitle("住戶管理")
        self.setGeometry(100, 100, 900, 600)
        
        self.db = Database()
        
        self.init_ui()
        self.load_households()
    
    def init_ui(self):
        """初始化用戶界面"""
        main_layout = QVBoxLayout()
        
        # 標題
        title = QLabel("住戶管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 搜索和過濾區域
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜尋戶號:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("輸入戶號進行搜尋...")
        self.search_input.textChanged.connect(self.filter_households)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        main_layout.addLayout(search_layout)
        
        # 住戶表格 - 新增 3 列：戶號、原始條碼
        self.household_table = QTableWidget()
        self.household_table.setColumnCount(2)
        self.household_table.setHorizontalHeaderLabels(["戶號", "原始條碼"])
        self.household_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.household_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.household_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.household_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        main_layout.addWidget(self.household_table)
        
        # 按鈕區域
        button_layout = QHBoxLayout()
        
        # 導入按鈕
        import_button = QPushButton("導入住戶（.xlsx）")
        import_button.clicked.connect(self.import_households_xlsx)
        button_layout.addWidget(import_button)
        
        # 導出按鈕
        export_button = QPushButton("導出住戶（.xlsx）")
        export_button.clicked.connect(self.export_households_xlsx)
        button_layout.addWidget(export_button)
        
        button_layout.addSpacing(20)
        
        # 刷新按鈕
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.load_households)
        button_layout.addWidget(refresh_button)
        
        button_layout.addStretch()
        
        # 關閉按鈕
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 保存所有住戶數據以供搜尋
        self.all_households = []
    
    def load_households(self):
        """加載所有住戶"""
        # 從數據庫和條碼映射表讀取
        self.all_households = []
        
        households = self.db.get_all_households()
        for household in households:
            household_id = household['household_id']
            # 查詢原始條碼
            barcode = self.db.get_barcode_by_household_id(household_id)
            
            self.all_households.append({
                'household_id': household_id,
                'barcode': barcode or ''
            })
        
        self.refresh_table(self.all_households)
    
    def refresh_table(self, households: List[Dict]):
        """刷新表格顯示"""
        self.household_table.setRowCount(0)
        
        for household in households:
            row_position = self.household_table.rowCount()
            self.household_table.insertRow(row_position)
            
            # 戶號
            self.household_table.setItem(
                row_position, 0,
                QTableWidgetItem(household['household_id'])
            )
            # 原始條碼
            self.household_table.setItem(
                row_position, 1,
                QTableWidgetItem(household.get('barcode', ''))
            )
    
    def filter_households(self):
        """根據搜尋條件過濾住戶"""
        search_text = self.search_input.text().strip().lower()
        
        if not search_text:
            self.refresh_table(self.all_households)
            return
        
        filtered = [
            h for h in self.all_households
            if search_text in h['household_id'].lower() or
               search_text in h.get('barcode', '').lower()
        ]
        
        self.refresh_table(filtered)
    
    def import_households_xlsx(self):
        """從 .xlsx 文件導入住戶"""
        if not XLSX_AVAILABLE and not PANDAS_AVAILABLE:
            QMessageBox.critical(
                self, "錯誤",
                "需要安裝 openpyxl 或 pandas 來支持 .xlsx 文件\n\n"
                "請運行: pip install openpyxl pandas"
            )
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇住戶 .xlsx 文件",
            "",
            "Excel 文件 (*.xlsx);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            households = self._read_xlsx_file(file_path)
            
            if not households:
                QMessageBox.warning(self, "警告", ".xlsx 文件中沒有有效的住戶數據")
                return
            
            # 導入住戶和條碼映射
            success = 0
            failed = 0
            
            for household in households:
                household_id = household['household_id'].strip()
                barcode = household.get('barcode', '').strip()
                
                if not household_id:
                    failed += 1
                    continue
                
                # 先檢查是否已存在
                if self.db.get_household(household_id):
                    failed += 1
                    continue
                
                # 添加住戶（使用戶號作為名稱）
                if self.db.add_household(household_id, household_id):
                    success += 1
                    
                    # 如果有原始條碼，添加映射
                    if barcode:
                        self.db.add_barcode_mapping(household_id, barcode)
                else:
                    failed += 1
            
            QMessageBox.information(
                self, "導入完成",
                f"成功導入 {success} 個住戶\n"
                f"失敗 {failed} 個（可能是戶號重複或格式錯誤）\n\n"
                f"條碼映射已自動建立"
            )
            
            self.load_households()
            self.search_input.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"導入失敗: {str(e)}")
    
    def _read_xlsx_file(self, file_path: str) -> List[Dict]:
        """
        讀取 .xlsx 文件
        
        期望的列：戶號 | 原始條碼
        """
        households = []
        
        if XLSX_AVAILABLE:
            # 使用 openpyxl
            from openpyxl import load_workbook
            
            workbook = load_workbook(file_path)
            worksheet = workbook.active
            
            # 讀取標題行
            headers = []
            for cell in worksheet[1]:
                headers.append(cell.value)
            
            # 查找列索引
            household_id_col = None
            barcode_col = None
            
            for idx, header in enumerate(headers):
                if header and '戶號' in str(header):
                    household_id_col = idx
                elif header and '條碼' in str(header):
                    barcode_col = idx
            
            if household_id_col is None:
                raise ValueError("找不到 '戶號' 列")
            
            # 讀取數據行
            for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row[household_id_col]:
                    continue
                
                household_id = str(row[household_id_col]).strip()
                barcode = str(row[barcode_col]).strip() if barcode_col is not None and row[barcode_col] else ''
                
                if household_id:
                    households.append({
                        'household_id': household_id,
                        'barcode': barcode
                    })
        
        elif PANDAS_AVAILABLE:
            # 使用 pandas
            import pandas as pd
            
            df = pd.read_excel(file_path)
            
            # 查找列名
            household_id_col = None
            barcode_col = None
            
            for col in df.columns:
                if '戶號' in str(col):
                    household_id_col = col
                elif '條碼' in str(col):
                    barcode_col = col
            
            if household_id_col is None:
                raise ValueError("找不到 '戶號' 列")
            
            # 讀取數據
            for idx, row in df.iterrows():
                household_id = str(row[household_id_col]).strip()
                barcode = str(row[barcode_col]).strip() if barcode_col and pd.notna(row[barcode_col]) else ''
                
                if household_id and household_id != 'nan':
                    households.append({
                        'household_id': household_id,
                        'barcode': barcode
                    })
        
        return households
    
    def export_households_xlsx(self):
        """導出住戶到 .xlsx 文件"""
        if not XLSX_AVAILABLE and not PANDAS_AVAILABLE:
            QMessageBox.critical(
                self, "錯誤",
                "需要安裝 openpyxl 或 pandas 來支持 .xlsx 文件\n\n"
                "請運行: pip install openpyxl pandas"
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存住戶 .xlsx 文件",
            "households.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            households_data = []
            
            for household in self.all_households:
                households_data.append({
                    '戶號': household['household_id'],
                    '原始條碼': household.get('barcode', '')
                })
            
            if not households_data:
                QMessageBox.warning(self, "警告", "沒有住戶數據可導出")
                return
            
            if PANDAS_AVAILABLE:
                # 使用 pandas 導出
                import pandas as pd
                
                df = pd.DataFrame(households_data)
                df.to_excel(file_path, index=False, sheet_name='住戶')
            
            elif XLSX_AVAILABLE:
                # 使用 openpyxl 導出
                from openpyxl import Workbook
                
                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = '住戶'
                
                # 寫入標題
                worksheet['A1'] = '戶號'
                worksheet['B1'] = '原始條碼'
                
                # 寫入數據
                for row_idx, household in enumerate(households_data, start=2):
                    worksheet[f'A{row_idx}'] = household['戶號']
                    worksheet[f'B{row_idx}'] = household['原始條碼']
                
                workbook.save(file_path)
            
            QMessageBox.information(
                self, "成功",
                f"已導出 {len(households_data)} 個住戶到 {Path(file_path).name}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"導出失敗: {str(e)}")
