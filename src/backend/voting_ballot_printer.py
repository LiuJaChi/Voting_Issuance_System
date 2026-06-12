"""
投票單 PDF 生成模塊 - 使用 python-barcode 生成 Code128 條碼圖像

投票單規格（精確規格）：
- 每張選票高度：80mm (8cm)
- 上邊距：5mm (0.5cm)
- 下邊距：5mm (0.5cm)
- 可用高度：70mm
- 寬度：95mm
- 條碼尺寸：54mm × 8mm
- 每頁 A4：2 欄 × 4 列 = 8 張

內容佈局：
- 第X案 + 項目名稱：20mm
- 投票種類 + 描述：15mm
- 空白間距：5mm
- 條碼 (54×8mm)：8mm
- 戶號 + 投票選項：22mm
- 總計：70mm
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime

import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# 投票單（標籤）尺寸 - 精確規格 8cm = 80mm
LABEL_WIDTH = 95 * mm
LABEL_HEIGHT = 80 * mm  # 8cm 精確規格
LABEL_TOP_MARGIN = 5 * mm  # 上邊距 0.5cm
LABEL_BOTTOM_MARGIN = 5 * mm  # 下邊距 0.5cm
USABLE_HEIGHT = 70 * mm  # 可用高度

# 條碼規格
BARCODE_WIDTH = 54 * mm
BARCODE_HEIGHT = 8 * mm

# 每頁欄數與列數 - 2 欄 × 4 列
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 4


class VotingBallotPrinter:
    """投票單 PDF 生成器"""

    def __init__(self, output_dir: str = "exports/voting_ballots"):
        """初始化"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 建立臨時條碼目錄
        self.temp_barcode_dir = os.path.join(output_dir, ".temp_barcodes")
        Path(self.temp_barcode_dir).mkdir(parents=True, exist_ok=True)
        
        self._init_chinese_fonts()

    def _init_chinese_fonts(self):
        """初始化繁體中文字體支持"""
        try:
            font_paths = [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
                "/System/Library/Fonts/STHeiti Medium.ttf",  # macOS
                "C:\\Windows\\Fonts\\kaiu.ttf",  # Windows (標楷體)
                "C:\\Windows\\Fonts\\msyh.ttf",  # Windows (微軟雅黑)
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    pdfmetrics.registerFont(TTFont('ChineseFontBold', font_path))
                    break
        except Exception as e:
            print(f"⚠ 中文字體初始化失敗: {e}，將使用默認字體")

    def _cleanup_temp_barcode_dir(self):
        """清理臨時條碼目錄"""
        try:
            if os.path.exists(self.temp_barcode_dir):
                shutil.rmtree(self.temp_barcode_dir)
        except Exception as e:
            print(f"⚠ 清理臨時文件失敗: {e}")

    def _generate_code128_image(self, content: str) -> str:
        """
        生成 Code128 條碼圖像 (54mm × 8mm)
        
        Args:
            content: 條碼內容
            
        Returns:
            條碼圖像路徑
        """
        try:
            output_path = os.path.join(self.temp_barcode_dir, f"{content}.png")
            
            # 生成 Code128 條碼
            ean = barcode.get('code128', content, writer=ImageWriter())
            ean.save(output_path.replace('.png', ''))
            
            return output_path
        except Exception as e:
            print(f"⚠ 生成條碼失敗 ({content}): {e}")
            return None

    def generate_pdf(
        self,
        voting_data: List[Dict],
        filename: str = "voting_ballots.pdf"
    ) -> str:
        """
        生成投票單 PDF
        
        Args:
            voting_data: 投票數據列表
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
        
        # 檢查中文字體是否可用
        try:
            pdfmetrics.getFont('ChineseFont')
            font_name = 'ChineseFont'
            font_bold_name = 'ChineseFontBold'
        except:
            font_name = 'Helvetica'
            font_bold_name = 'Helvetica-Bold'
        
        # 案號樣式 - 縮小以適應 20mm 空間
        case_number_style = ParagraphStyle(
            'CaseNumber',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=12,
            leading=13,
            fontName=font_bold_name,
            textColor=colors.darkblue,
        )
        
        # 項目名稱樣式
        item_name_style = ParagraphStyle(
            'ItemName',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=8,
            leading=9,
            fontName=font_name,
            textColor=colors.darkblue,
        )
        
        # 投票種類樣式
        vote_type_style = ParagraphStyle(
            'VoteType',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=6,
            leading=7,
            fontName=font_name,
            textColor=colors.darkblue,
        )
        
        # 描述樣式
        description_style = ParagraphStyle(
            'Description',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=6,
            leading=7,
            fontName=font_name,
            textColor=colors.black,
        )
        
        # 投票選項樣式 - 12pt 粗體紅色（突出顯示）
        voting_option_style = ParagraphStyle(
            'VotingOption',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=12,
            leading=13,
            fontName=font_bold_name,
            textColor=colors.darkred,
        )
        
        # 戶號樣式
        household_id_style = ParagraphStyle(
            'HouseholdID',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=7,
            leading=8,
            fontName=font_bold_name,
            textColor=colors.black,
        )

        # 每個標籤的寬度
        available_w = page_w - 2 * margin
        cell_w = available_w / COLS_PER_PAGE

        # 每個標籤的高度
        cell_h = LABEL_HEIGHT

        table_data = []
        row_cells = []

        # 遍歷每個投票案號
        for case_idx, case in enumerate(voting_data):
            case_number = case['case_number']
            case_name = case['name']
            vote_type = case.get('vote_type', '一般議案')
            description = case.get('description', '')
            households = case.get('households', [])
            
            print(f"\n📋 處理投票案號 {case_idx + 1}/{len(voting_data)}: 第{case_number}案 {case_name}")
            
            # 遍歷每個住戶
            for household_idx, household in enumerate(households):
                household_id = household['household_id']
                
                # 生成條碼
                barcode_path = self._generate_code128_image(household_id)
                
                if barcode_path and os.path.exists(barcode_path):
                    code128_img = RLImage(barcode_path, width=BARCODE_WIDTH, height=BARCODE_HEIGHT)
                else:
                    code128_img = Paragraph(f"{household_id}", household_id_style)
                
                # 構建投票單內容 - 精確按 70mm 可用高度分配
                ballot_content_data = [
                    # 上邊距 (5mm)
                    [Spacer(1, 5 * mm)],
                    
                    # 第X案 + 項目名稱區段 (20mm)
                    [Paragraph(f"第 {case_number} 案", case_number_style)],
                    [Paragraph(case_name, item_name_style)],
                    
                    # 投票種類 + 描述區段 (15mm)
                    [Paragraph(f"({vote_type})", vote_type_style)],
                    [Paragraph(description[:50] if description else "", description_style)],
                    
                    # 空白間距 (5mm)
                    [Spacer(1, 5 * mm)],
                    
                    # 條碼區段 (8mm) - 54mm × 8mm
                    [code128_img],
                    
                    # 戶號 + 投票選項區段 (22mm)
                    [Paragraph(household_id, household_id_style)],
                    [Paragraph("□ 同意  □ 不同意  □ 棄權", voting_option_style)],
                    
                    # 下邊距 (5mm)
                    [Spacer(1, 5 * mm)],
                ]
                
                ballot_content_table = Table(
                    ballot_content_data,
                    colWidths=[cell_w * 0.95],
                    # 行高分配
                    rowHeights=[
                        5 * mm,      # 上邊距
                        8 * mm,      # 案號
                        7 * mm,      # 項名
                        4 * mm,      # 種類
                        6 * mm,      # 描述
                        5 * mm,      # 空白
                        8 * mm,      # 條碼
                        5 * mm,      # 戶號
                        6 * mm,      # 選項
                        5 * mm,      # 下邊距
                    ],
                )
                ballot_content_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 1),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                    ('TOPPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                    # 邊框
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ]))

                row_cells.append(ballot_content_table)

                if len(row_cells) == COLS_PER_PAGE:
                    table_data.append(row_cells)
                    row_cells = []

        # 補齊最後一行
        if row_cells:
            while len(row_cells) < COLS_PER_PAGE:
                row_cells.append("")
            table_data.append(row_cells)

        if not table_data:
            self._cleanup_temp_barcode_dir()
            return output_path

        col_widths = [cell_w] * COLS_PER_PAGE
        row_heights = [cell_h] * len(table_data)

        table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))

        print(f"\n📄 開始生成 PDF: {output_path}")
        doc.build([table])
        print(f"✓ PDF 生成完成: {output_path}")
        print(f"\n📊 選票規格:")
        print(f"   票高度: 80mm (8cm)")
        print(f"   上邊距: 5mm (0.5cm)")
        print(f"   下邊距: 5mm (0.5cm)")
        print(f"   可用高度: 70mm")
        print(f"   條碼尺寸: 54mm × 8mm")
        print(f"   每頁配置: 2 欄 × 4 列 = 8 張")

        # 清理臨時條碼文件
        self._cleanup_temp_barcode_dir()
        
        return output_path
