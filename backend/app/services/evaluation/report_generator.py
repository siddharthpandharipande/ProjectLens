"""Comprehensive PDF and JSON Report Generator for ProjectLens (Final Phase).

Uses ReportLab to generate publication-grade academic evaluation reports
strictly adhering to Neo-Brutalist design tokens: #FAF6EE canvas, #121212 borders,
#FFE600 headers, hard tabular lines, and readable multi-page typography.
"""

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that performs two passes to render 'Page X of Y' footers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Any] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#121212"))

        # Header rule and label
        self.drawString(54, letter[1] - 36, "PROJECTLENS FACULTY SUITE — EVALUATION & DEFENSE REPORT")
        self.setStrokeColor(colors.HexColor("#121212"))
        self.setLineWidth(1.5)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Footer rule and page info
        self.setStrokeColor(colors.HexColor("#121212"))
        self.setLineWidth(1.5)
        self.line(54, 45, letter[0] - 54, 45)

        self.setFont("Helvetica", 8)
        self.drawString(
            54,
            32,
            "Academic Advisory Signal • Not an automated misconduct verdict",
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


class EvaluationReportGenerator:
    """Generates formal PDF and JSON evaluation reports."""

    @classmethod
    def generate_pdf_report(cls, evaluation_data: Dict[str, Any]) -> bytes:
        """Render a complete multi-page PDF evaluation report and return bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Custom Neo-Brutalist Styles
        style_title = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#121212"),
            spaceAfter=6,
        )
        style_subtitle = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4b4731"),
            spaceAfter=12,
        )
        style_h1 = ParagraphStyle(
            "Heading1",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#121212"),
            spaceBefore=14,
            spaceAfter=6,
        )
        style_h2 = ParagraphStyle(
            "Heading2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#121212"),
            spaceBefore=8,
            spaceAfter=4,
        )
        style_body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1c1b1b"),
            spaceAfter=4,
        )
        style_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#121212"),
        )
        style_table_cell = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1c1b1b"),
        )
        style_table_head = ParagraphStyle(
            "TableHead",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#121212"),
        )

        story: List[Any] = []

        project = evaluation_data.get("project")
        if isinstance(project, dict):
            project_title = project.get("title") or "Project"
            project_id = project.get("id") or "proj_unknown"
        else:
            project_title = getattr(project, "title", "Project") or "Project"
            project_id = getattr(project, "id", "proj_unknown")
        score = evaluation_data.get("overall_score")
        grade = evaluation_data.get("grade") or "N/A"
        status_val = evaluation_data.get("evaluation_status", "complete").upper()
        coverage = evaluation_data.get("coverage_pct", 100.0)
        now_str = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

        # ── 1. Document Header & Score Banner ──
        story.append(Paragraph(f"{project_title}", style_title))
        story.append(
            Paragraph(
                f"Project Identifier: <b>{project_id}</b> • Generated: {now_str} • Status: <b>{status_val}</b>",
                style_subtitle,
            )
        )
        story.append(Spacer(1, 4))

        # Overall Score Block (Neo-Brutalist Box)
        score_display = f"{score:.1f}" if score is not None else "N/A"
        score_data = [
            [
                Paragraph("<b>CALCULATED FACULTY SCORE</b>", style_table_head),
                Paragraph("<b>LETTER GRADE</b>", style_table_head),
                Paragraph("<b>EVALUATION COVERAGE</b>", style_table_head),
            ],
            [
                Paragraph(f"<font size=24><b>{score_display}</b></font> / 100", style_title),
                Paragraph(f"<font size=24><b>{grade}</b></font>", style_title),
                Paragraph(f"<font size=16><b>{coverage:.0f}%</b></font> assessed", style_title),
            ],
        ]
        score_table = Table(score_data, colWidths=[200, 150, 154])
        score_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFE600")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FAF6EE")),
                ("BOX", (0, 0), (-1, -1), 2.0, colors.HexColor("#121212")),
                ("INNERGRID", (0, 0), (-1, -1), 1.0, colors.HexColor("#121212")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(score_table)
        story.append(Spacer(1, 12))

        # ── 2. Executive Summary ──
        story.append(Paragraph("1. Executive Summary & Assessment Overview", style_h1))
        exec_summary = evaluation_data.get("executive_summary") or "Comprehensive project evaluation completed."
        story.append(Paragraph(exec_summary, style_body))
        story.append(Spacer(1, 8))

        # ── 3. Category Breakdown Table ──
        story.append(Paragraph("2. Category-Wise Evaluation & Rubric Contributions", style_h1))
        cat_scores = evaluation_data.get("category_scores", [])
        table_rows = [
            [
                Paragraph("Category", style_table_head),
                Paragraph("Score", style_table_head),
                Paragraph("Weight", style_table_head),
                Paragraph("Contribution", style_table_head),
                Paragraph("Assessment Status", style_table_head),
            ]
        ]
        for c in cat_scores:
            c_score = f"{c.score:.1f}/100" if c.score is not None else "—"
            c_contrib = f"{c.contribution:.1f} pts" if c.score is not None else "0.0 pts"
            table_rows.append([
                Paragraph(f"<b>{c.name}</b>", style_table_cell),
                Paragraph(c_score, style_table_cell),
                Paragraph(f"{c.weight:.0f}%", style_table_cell),
                Paragraph(c_contrib, style_table_cell),
                Paragraph(c.status.upper(), style_table_cell),
            ])

        cat_table = Table(table_rows, colWidths=[200, 60, 60, 84, 100])
        cat_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2ECE1")),
                ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#121212")),
                ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#121212")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(cat_table)
        story.append(Spacer(1, 12))

        # ── 4. Key Strengths and Weaknesses ──
        story.append(Paragraph("3. Observed Engineering Strengths", style_h1))
        strengths = evaluation_data.get("strengths", [])
        if strengths:
            for s in strengths[:5]:
                story.append(Paragraph(f"• <b>Strength:</b> {s}", style_body))
        else:
            story.append(Paragraph("No distinct strengths recorded.", style_body))
        story.append(Spacer(1, 8))

        story.append(Paragraph("4. Areas for Improvement & Identified Weaknesses", style_h1))
        weaknesses = evaluation_data.get("weaknesses", [])
        if weaknesses:
            for w in weaknesses[:5]:
                story.append(Paragraph(f"• <b>Improvement Area:</b> {w}", style_body))
        else:
            story.append(Paragraph("No critical weaknesses noted.", style_body))
        story.append(Spacer(1, 8))

        # ── 5. Risk Advisory & Critical Flags ──
        story.append(Paragraph("5. Advisory Risk Screening Signals", style_h1))
        risks = evaluation_data.get("risks", [])
        if risks:
            for r in risks[:4]:
                story.append(Paragraph(f"⚠ <b>Risk Note:</b> {r}", style_body))
        else:
            story.append(Paragraph("No high-severity risk signals detected across static analyzers.", style_body))
        story.append(Spacer(1, 10))

        # ── 6. Prioritized Actionable Recommendations ──
        story.append(Paragraph("6. Prioritized Action Plan & Next Steps", style_h1))
        recommendations = evaluation_data.get("recommendations", [])
        if recommendations:
            rec_rows = [
                [
                    Paragraph("Priority", style_table_head),
                    Paragraph("Action Item", style_table_head),
                    Paragraph("Why It Matters", style_table_head),
                    Paragraph("Expected Benefit", style_table_head),
                ]
            ]
            for rec in recommendations[:4]:
                rec_rows.append([
                    Paragraph(f"<b>{rec.priority}</b>", style_table_cell),
                    Paragraph(f"<b>{rec.title}</b><br/>{rec.description}", style_table_cell),
                    Paragraph(rec.why_it_matters, style_table_cell),
                    Paragraph(rec.expected_benefit, style_table_cell),
                ])
            rec_table = Table(rec_rows, colWidths=[65, 175, 134, 130])
            rec_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2ECE1")),
                    ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#121212")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#121212")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(rec_table)
        story.append(Spacer(1, 12))

        # ── 7. Viva Defense Sample Questions ──
        viva_set = evaluation_data.get("viva_set")
        if viva_set and getattr(viva_set, "questions", None):
            story.append(Paragraph("7. Sample Viva Defense Questions (Examiner Focus)", style_h1))
            for q in viva_set.questions[:3]:
                q_text = getattr(q, "question", "") or getattr(q, "question_text", "")
                cat = getattr(q, "category", "General")
                diff = getattr(q, "difficulty", "intermediate").upper()
                rationale = getattr(q, "examiner_rationale", "")
                story.append(
                    Paragraph(
                        f"<b>Q [{cat} • {diff}]:</b> {q_text}",
                        style_body,
                    )
                )
                if rationale:
                    story.append(
                        Paragraph(
                            f"<i>Examiner Rationale:</i> {rationale}",
                            style_body,
                        )
                    )
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 8))

        # ── 8. Disclaimer & Academic Standard ──
        story.append(Spacer(1, 8))
        story.append(
            HRFlowable(
                width="100%",
                thickness=1.5,
                color=colors.HexColor("#121212"),
                spaceAfter=6,
            )
        )
        disclaimer = (
            "<b>ACADEMIC INTEGRITY NOTICE & ADVISORY STANDARD:</b> ProjectLens is an evaluation assistant "
            "designed to assist academic faculty and viva panels. All similarity, complexity, and AI signals "
            "are analytical screening indicators rather than definitive judgements. Final assessment, grade "
            "determination, and academic adjudication remain the exclusive responsibility of evaluators."
        )
        story.append(Paragraph(disclaimer, style_body))

        # Build document
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()

    @classmethod
    def generate_json_export(cls, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Produce clean, machine-readable JSON evaluation export."""
        project = evaluation_data.get("project")
        if isinstance(project, dict):
            p_id = project.get("id") or "unknown"
            p_title = project.get("title") or "Project"
            course = project.get("course") or "N/A"
            team = project.get("team") or "N/A"
        else:
            p_id = getattr(project, "id", "unknown") if project else "unknown"
            p_title = getattr(project, "title", "Project") if project else "Project"
            course = getattr(project, "course", "N/A") if project else "N/A"
            team = getattr(project, "team", "N/A") if project else "N/A"

        cat_scores = [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in evaluation_data.get("category_scores", [])
        ]
        recommendations = [
            r.model_dump() if hasattr(r, "model_dump") else r
            for r in evaluation_data.get("recommendations", [])
        ]
        return {
            "project": {
                "id": p_id,
                "title": p_title,
                "course": course,
                "team": team,
            },
            "projectId": p_id,
            "projectTitle": p_title,
            "evaluatedAt": datetime.now(timezone.utc).isoformat(),
            "evaluation": {
                "overallScore": evaluation_data.get("overall_score"),
                "grade": evaluation_data.get("grade"),
                "evaluationStatus": evaluation_data.get("evaluation_status"),
                "coveragePct": evaluation_data.get("coverage_pct"),
            },
            "overallScore": evaluation_data.get("overall_score"),
            "grade": evaluation_data.get("grade"),
            "evaluationStatus": evaluation_data.get("evaluation_status"),
            "coveragePct": evaluation_data.get("coverage_pct"),
            "categoryScores": cat_scores,
            "strengths": evaluation_data.get("strengths", []),
            "weaknesses": evaluation_data.get("weaknesses", []),
            "risks": evaluation_data.get("risks", []),
            "recommendations": recommendations,
            "moduleStatuses": evaluation_data.get("module_statuses", {}),
            "executiveSummary": evaluation_data.get("executive_summary"),
        }

    # Alias for convenience
    generate_pdf = generate_pdf_report
