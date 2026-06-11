"""
報到單 PDF 生成模塊 + 報到條碼 Excel 導出 - 使用 Code39 條碼

報到單規格：
- Code39 內容：原始條碼（例如 虐乙）
- 每張大小：BARCODE 標籤尺寸（90mm × 35mm）
- 每頁 A4：2 欄 × 8 列 = 最多 16 張
- 內容：戶號 + 姓名 + Code39 條碼
"""
import io
from pathlib import Path
from typing import List, Tuple, Dict

import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Image as RLImage

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# 報到單（標籤）尺寸
LABEL_WIDTH = 90 * mm
LABEL_HEIGHT = 35 * mm

# 每頁欄數與列數
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 8


class CheckInPrinter:
    """報到單 PDF 生成器 + 報到條碼 Excel 導出"""

    def __init__(self, output_dir: str = "exports/check_in_ballots"):
        """初始化"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_code39_image(content: str) -> io.BytesIO:
        """
        生成 Code39 條碼圖片，返回 BytesIO 流
        
        Args:
            content: Code39 內容（原始條碼）
            
        Returns:
            BytesIO 流
        """
        buf = io.BytesIO()
        
        try:
            # 生成 Code39 條碼
            code39_class = barcode.get_barcode_class('code39')
            writer = ImageWriter()
            bar = code39_class(content, writer=writer, add_checksum=False)
            
            options = {
                'module_width': 0.5,      # 條碼寬度
                'module_height': 12.0,    # 條碼高度
                'font_size': 10,          # 文字大小
                'text_distance': 3,       # 文字與條碼距離
            }
            
            bar.write(buf, options=options)
            buf.seek(0)
            
            return buf
        except Exception as e:
            print(f"Code39 條碼生成失敗 {content}: {e}")
            raise

    def generate_pdf(
        self,
        households: List[Dict],
        filename: str = "check_in_ballots.pdf"
    ) -> str:
        """
        生成報到單 PDF
        
        Args:
            households: [{'household_id': 'A106-02', 'name': '王先生', 'barcode': '虐乙'}, ...]
            filename: 輸出文件名
            
        Returns:
            輸出文件路徑
        """
        output_path = str(Path(self.output_dir) / filename)

        page_w, page_h = A4
        margin = 10 * mm

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )

        styles = getSampleStyleSheet()
        center_style = ParagraphStyle(
            'Center',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=9,
            leading=11,
        )
        id_style = ParagraphStyle(
            'ID',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#333333'),
        )

        # 每個標籤的寬度
        available_w = page_w - 2 * margin
        cell_w = available_w / COLS_PER_PAGE

        # 每個標籤的高度
        cell_h = LABEL_HEIGHT

        table_data = []
        row_cells = []

        for household in households:
            household_id = household['household_id']
            name = household['name']
            barcode_str = household.get('barcode', household_id)  # 優先用原始條碼，沒有則用戶號
            
            # 生成 Code39 條碼圖片（使用原始條碼）
            try:
                code39_buf = self._generate_code39_image(barcode_str)
                code39_img = RLImage(code39_buf, width=cell_w * 0.8, height=18 * mm)
            except Exception as e:
                print(f"Code39 生成失敗 {barcode_str}: {e}")
                code39_img = Paragraph(f"[條碼: {barcode_str}]", center_style)

            cell_content = [
                Paragraph(f"<b>{household_id}</b>", center_style),
                Paragraph(name, id_style),
                code39_img,
            ]

            row_cells.append(cell_content)

            if len(row_cells) == COLS_PER_PAGE:
                table_data.append(row_cells)
                row_cells = []

        # 補齊最後一行
        if row_cells:
            while len(row_cells) < COLS_PER_PAGE:
                row_cells.append("")
            table_data.append(row_cells)

        if not table_data:
            return output_path

        col_widths = [cell_w] * COLS_PER_PAGE
        row_heights = [cell_h] * len(table_data)

        table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        doc.build([table])
        return output_path

    def export_check_in_xlsx(
        self,
        households: List[Dict],
        filename: str = "報到.xlsx"
    ) -> str:
        """
        導出報到條碼到 Excel 文件
        
        Args:
            households: [{'household_id': 'A106-02', 'name': '王先生', 'barcode': '虐乙'}, ...]
            filename: 輸出文件名（默認為 報到.xlsx）
            
        Returns:
            輸出文件路徑
        """
        output_path = str(Path(self.output_dir) / filename)
        
        if OPENPYXL_AVAILABLE:
            # 使用 openpyxl
            from openpyxl import Workbook
            
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = '報到'
            
            # 設置列寬
            worksheet.column_dimensions['A'].width = 15
            worksheet.column_dimensions['B'].width = 20
            worksheet.column_dimensions['C'].width = 25
            
            # 寫入標題
            headers = ['戶號', '姓名', '原始條碼']
            for col_idx, header in enumerate(headers, start=1):
                cell = worksheet.cell(row=1, column=col_idx, value=header)
                # 標題樣式
                cell.font = Font(bold=True, size=11, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 寫入數據
            for row_idx, household in enumerate(households, start=2):
                worksheet.cell(row=row_idx, column=1, value=household['household_id'])
                worksheet.cell(row=row_idx, column=2, value=household['name'])
                worksheet.cell(row=row_idx, column=3, value=household.get('barcode', ''))
                
                # 數據行樣式
                for col_idx in range(1, 4):
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
            
            # 凍結標題行
            worksheet.freeze_panes = 'A2'
            
            workbook.save(output_path)
            
        elif PANDAS_AVAILABLE:
            # 使用 pandas
            import pandas as pd
            
            # 構建 DataFrame
            data = {
                '戶號': [h['household_id'] for h in households],
                '姓名': [h['name'] for h in households],
                '原始條碼': [h.get('barcode', '') for h in households]
            }
            df = pd.DataFrame(data)
            
            # 使用 ExcelWriter 設置樣式
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='報到', index=False)
                
                # 設置列寬
                worksheet = writer.sheets['報到']
                worksheet.column_dimensions['A'].width = 15
                worksheet.column_dimensions['B'].width = 20
                worksheet.column_dimensions['C'].width = 25
        else:
            # 降級方案：使用 CSV
            import csv
            csv_path = output_path.replace('.xlsx', '.csv')
            
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['戶號', '姓名', '原始條碼'])
                writer.writeheader()
                
                for household in households:
                    writer.writerow({
                        '戶號': household['household_id'],
                        '姓名': household['name'],
                        '原始條碼': household.get('barcode', '')
                    })
            
            output_path = csv_path
        
        return output_path
