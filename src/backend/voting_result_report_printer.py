"""
投票結果報表 PDF 生成器
- 每案顯示：案號、名稱、同意、不同意、棄權、同意率、門檻、是否通過
- 判斷：同意率 >= 門檻 => 通過
"""

import os
from pathlib import Path
from typing import List, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class VotingResultReportPrinter:
    def __init__(self, output_dir: str = "exports/voting_reports"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self._init_chinese_fonts()

    def _init_chinese_fonts(self):
        try:
            font_paths = [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
                "/System/Library/Fonts/STHeiti Medium.ttc",                # macOS
                "/System/Library/Fonts/STHeiti Medium.ttf",                # macOS
                "C:\\Windows\\Fonts\\kaiu.ttf",                            # Windows
                "C:\\Windows\\Fonts\\msyh.ttf",                            # Windows
            ]
            for fp in font_paths:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont("ChineseFont", fp))
                    pdfmetrics.registerFont(TTFont("ChineseFontBold", fp))
                    return
        except Exception as e:
            print(f"⚠ 字體初始化失敗: {e}")

    @staticmethod
    def _to_float(v, default=0.0) -> float:
        try:
            return float(v)
        except Exception:
            return float(default)

    def _extract_counts(self, case: Dict):
        result_obj = case.get("result") or case.get("results") or {}
        agree = case.get("agree_count", result_obj.get("agree", result_obj.get("yes", case.get("yes", 0))))
        disagree = case.get("disagree_count", result_obj.get("disagree", result_obj.get("no", case.get("no", 0))))
        abstain = case.get("abstain_count", result_obj.get("abstain", case.get("abstain", 0)))
        return self._to_float(agree, 0), self._to_float(disagree, 0), self._to_float(abstain, 0)

    def generate_pdf(
        self,
        voting_data: List[Dict],
        filename: str = "voting_result_report.pdf",
        default_pass_percentage: float = 50.0
    ) -> str:
        output_path = str(Path(self.output_dir) / filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )

        styles = getSampleStyleSheet()
        try:
            pdfmetrics.getFont("ChineseFont")
            font_name = "ChineseFont"
            font_bold = "ChineseFontBold"
        except Exception:
            font_name = "Helvetica"
            font_bold = "Helvetica-Bold"

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontName=font_bold,
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1f2937"),
        )

        story = [Paragraph("投票結果報表", title_style), Spacer(1, 6 * mm)]

        table_data = [[
            "案號", "議案名稱", "同意", "不同意", "棄權", "同意率(%)", "門檻(%)", "是否通過"
        ]]

        for case in voting_data:
            case_no = str(case.get("case_number", ""))
            case_name = str(case.get("name", ""))

            agree, disagree, abstain = self._extract_counts(case)
            total = agree + disagree + abstain
            ratio = (agree / total * 100.0) if total > 0 else 0.0

            threshold = self._to_float(
                case.get("pass_percentage", case.get("meeting_pass_percentage", default_pass_percentage)),
                default_pass_percentage
            )

            passed = ratio >= threshold if total > 0 else False
            result_text = "通過" if passed else "未通過"

            table_data.append([
                case_no,
                case_name,
                f"{int(agree) if agree.is_integer() else agree}",
                f"{int(disagree) if disagree.is_integer() else disagree}",
                f"{int(abstain) if abstain.is_integer() else abstain}",
                f"{ratio:.2f}",
                f"{threshold:.2f}",
                result_text
            ])

        col_widths = [14*mm, 58*mm, 16*mm, 18*mm, 16*mm, 22*mm, 20*mm, 22*mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            ("FONTNAME", (0, 0), (-1, 0), font_bold),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9ca3af")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("FONTNAME", (0, 1), (-1, -1), font_name),
        ]

        for r in range(1, len(table_data)):
            result_text = table_data[r][7]
            if result_text == "通過":
                style_cmds.append(("TEXTCOLOR", (7, r), (7, r), colors.HexColor("#16a34a")))
                style_cmds.append(("FONTNAME", (7, r), (7, r), font_bold))
            else:
                style_cmds.append(("TEXTCOLOR", (7, r), (7, r), colors.HexColor("#dc2626")))
                style_cmds.append(("FONTNAME", (7, r), (7, r), font_bold))

        table.setStyle(TableStyle(style_cmds))
        story.append(table)

        doc.build(story)
        return output_path
