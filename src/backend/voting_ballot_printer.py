"""
投票單 PDF 生成模塊

投票單規格：
- 紙張：A4
- 每頁數量：8 張（2 欄 × 4 列）
- 每張內容：
  - 戶號（文字）
  - 案號（文字）
  - 投票單條碼（戶號_案號）
  - 投票選項：□ 贊成  □ 反對
"""
import io
from pathlib import Path
from typing import List, Tuple

import barcode as bc
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Image as RLImage

from src.backend.barcode_generator import BarcodeGenerator

# 每頁投票單數量
BALLOTS_PER_PAGE = 8
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 4


class VotingBallotPrinter:
    """投票單 PDF 生成器"""

    def __init__(self, output_dir: str = "exports/voting_ballots"):
        """初始化"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _generate_barcode_image(self, content: str, width: float, height: float) -> RLImage:
        """生成條碼圖片"""
        buf = io.BytesIO()
        code128_cls = bc.get_barcode_class('code128')
        writer = ImageWriter()
        bar = code128_cls(content, writer=writer)
        options = {
            'module_height': 7.0,
            'module_width': 0.28,
            'quiet_zone': 2.0,
            'font_size': 5,
            'text_distance': 1.5,
            'write_text': True,
        }
        bar.write(buf, options=options)
        buf.seek(0)
        return RLImage(buf, width=width, height=height)

    def generate_pdf(
        self,
        household_id: str,
        household_name: str,
        case_numbers: List[Tuple[str, str]],
        filename: str = None,
    ) -> str:
        """
        為單一住戶生成投票單 PDF

        Args:
            household_id: 戶號
            household_name: 姓名
            case_numbers: [(case_number, case_name), ...]
            filename: 輸出文件名

        Returns:
            輸出文件路徑
        """
        if not filename:
            safe_id = household_id.replace("/", "_").replace("\\", "_")
            filename = f"ballot_{safe_id}.pdf"

        return self._generate_pdf_for_ballots(
            [(household_id, household_name, cn, cname) for cn, cname in case_numbers],
            filename,
        )

    def generate_pdf_for_all(
        self,
        households: List[Tuple[str, str]],
        case_numbers: List[Tuple[str, str]],
        filename: str = "voting_ballots_all.pdf",
    ) -> str:
        """
        為所有住戶批量生成投票單 PDF

        Args:
            households: [(household_id, name), ...]
            case_numbers: [(case_number, case_name), ...]
            filename: 輸出文件名

        Returns:
            輸出文件路徑
        """
        ballots = []
        for household_id, household_name in households:
            for case_number, case_name in case_numbers:
                ballots.append((household_id, household_name, case_number, case_name))

        return self._generate_pdf_for_ballots(ballots, filename)

    def _generate_pdf_for_ballots(
        self,
        ballots: List[Tuple[str, str, str, str]],
        filename: str,
    ) -> str:
        """
        內部方法：生成投票單 PDF

        Args:
            ballots: [(household_id, household_name, case_number, case_name), ...]
            filename: 輸出文件名

        Returns:
            輸出文件路徑
        """
        output_path = str(Path(self.output_dir) / filename)

        page_w, page_h = A4
        margin = 8 * mm

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )

        styles = getSampleStyleSheet()

        center_bold = ParagraphStyle(
            'CenterBold',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10,
            leading=12,
            fontName='Helvetica-Bold',
        )
        center_normal = ParagraphStyle(
            'CenterNormal',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=9,
            leading=11,
        )
        option_style = ParagraphStyle(
            'Option',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=11,
            leading=14,
            spaceBefore=2,
        )

        available_w = page_w - 2 * margin
        cell_w = available_w / COLS_PER_PAGE
        # 每個投票單高度：A4可用高度 / 每頁列數
        available_h = page_h - 2 * margin
        cell_h = available_h / ROWS_PER_PAGE

        barcode_w = cell_w * 0.85
        barcode_h = 14 * mm

        all_story = []

        # 分頁處理：每頁 BALLOTS_PER_PAGE 張
        for page_start in range(0, len(ballots), BALLOTS_PER_PAGE):
            page_ballots = ballots[page_start: page_start + BALLOTS_PER_PAGE]

            table_data = []
            row_cells = []

            for idx, (household_id, household_name, case_number, case_name) in enumerate(
                page_ballots
            ):
                barcode_content = BarcodeGenerator.make_ballot_barcode_content(
                    household_id, case_number
                )

                try:
                    barcode_img = self._generate_barcode_image(
                        barcode_content, barcode_w, barcode_h
                    )
                except Exception as e:
                    print(f"條碼生成失敗 {barcode_content}: {e}")
                    barcode_img = Paragraph(f"[{barcode_content}]", center_normal)

                cell_content = [
                    Paragraph(f"<b>戶號：{household_id}</b>", center_bold),
                    Paragraph(f"姓名：{household_name}", center_normal),
                    Paragraph(f"案號：{case_number}　{case_name}", center_normal),
                    barcode_img,
                    Paragraph("□ 贊成　　□ 反對", option_style),
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

            col_widths = [cell_w] * COLS_PER_PAGE
            row_heights = [cell_h] * len(table_data)

            table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
            table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))

            all_story.append(table)

            # 在頁面之間添加分頁（最後一頁不加）
            if page_start + BALLOTS_PER_PAGE < len(ballots):
                from reportlab.platypus import PageBreak
                all_story.append(PageBreak())

        if all_story:
            doc.build(all_story)

        return output_path
