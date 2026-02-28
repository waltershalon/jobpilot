"""
PDF Resume Generator
Generates clean, ATS-friendly PDF resumes from TailoredResume data.
Uses reportlab for PDF generation.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib import colors

from engine.resume_tailor import TailoredResume


def generate_pdf(tailored: TailoredResume, output_path: str):
    """Generate a clean ATS-friendly PDF resume."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch
    )

    # Styles
    styles = getSampleStyleSheet()
    dark = HexColor("#1a1a1a")
    accent = HexColor("#2c3e50")

    name_style = ParagraphStyle(
        "Name", parent=styles["Title"],
        fontSize=18, leading=22, alignment=TA_CENTER,
        textColor=dark, spaceAfter=2, fontName="Helvetica-Bold"
    )
    contact_style = ParagraphStyle(
        "Contact", parent=styles["Normal"],
        fontSize=9, leading=12, alignment=TA_CENTER,
        textColor=HexColor("#555555"), spaceAfter=6
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=11, leading=14, textColor=accent,
        spaceAfter=3, spaceBefore=8, fontName="Helvetica-Bold",
        borderWidth=0, borderPadding=0
    )
    exp_title_style = ParagraphStyle(
        "ExpTitle", parent=styles["Normal"],
        fontSize=10, leading=13, fontName="Helvetica-Bold",
        textColor=dark, spaceAfter=1
    )
    exp_detail_style = ParagraphStyle(
        "ExpDetail", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Oblique",
        textColor=HexColor("#555555"), spaceAfter=2
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=styles["Normal"],
        fontSize=9.5, leading=12.5, fontName="Helvetica",
        textColor=dark, leftIndent=12, spaceAfter=1.5,
        alignment=TA_JUSTIFY
    )
    skills_style = ParagraphStyle(
        "Skills", parent=styles["Normal"],
        fontSize=9.5, leading=13, fontName="Helvetica",
        textColor=dark, spaceAfter=2
    )

    story = []

    # === HEADER ===
    personal = tailored.personal
    story.append(Paragraph(personal.get("name", ""), name_style))

    contact_parts = []
    if personal.get("email"):
        contact_parts.append(personal["email"])
    for link_name in ["linkedin", "github", "website"]:
        link = personal.get("links", {}).get(link_name, "")
        if link:
            contact_parts.append(link_name.capitalize())
    story.append(Paragraph(" | ".join(contact_parts), contact_style))

    story.append(HRFlowable(width="100%", thickness=0.5, color=accent, spaceAfter=6))

    # === EDUCATION ===
    story.append(Paragraph("EDUCATION", section_style))
    story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor("#cccccc"), spaceAfter=4))

    for edu in tailored.education:
        left = f"<b>{edu.get('institution', '')}</b> | {edu.get('location', '')}"
        right = f"{edu.get('start_date', '')} – {edu.get('end_date', '')}"
        story.append(Table(
            [[Paragraph(left, exp_title_style), Paragraph(right, exp_title_style)]],
            colWidths=["75%", "25%"],
            style=TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ])
        ))
        degree = edu.get("degree", "")
        if edu.get("gpa"):
            degree += f" (GPA: {edu['gpa']})"
        story.append(Paragraph(degree, exp_detail_style))
        story.append(Spacer(1, 2))

    # === TECHNICAL SKILLS ===
    story.append(Paragraph("TECHNICAL KNOWLEDGE", section_style))
    story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor("#cccccc"), spaceAfter=4))

    skill_labels = {
        "languages": "Languages",
        "data_engineering": "Data Engineering",
        "cloud_and_tools": "Cloud & Tools",
        "ai_ml": "AI/ML"
    }
    for key, label in skill_labels.items():
        skills = tailored.technical_skills.get(key, [])
        if skills:
            story.append(Paragraph(
                f"<b>{label}:</b> {' | '.join(skills)}", skills_style
            ))

    # === WORK EXPERIENCE ===
    if tailored.work_experience:
        story.append(Paragraph("WORK EXPERIENCE", section_style))
        story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor("#cccccc"), spaceAfter=4))

        for exp in tailored.work_experience:
            left = f"<b>{exp.get('title', '')}</b> | {exp.get('company', '')} | {exp.get('location', '')}"
            right = f"{exp.get('start_date', '')} – {exp.get('end_date', '')}"
            story.append(Table(
                [[Paragraph(left, exp_title_style), Paragraph(right, exp_title_style)]],
                colWidths=["75%", "25%"],
                style=TableStyle([
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ])
            ))
            for bullet in exp.get("bullets", []):
                story.append(Paragraph(f"● {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    # === RESEARCH EXPERIENCE ===
    if tailored.research_experience:
        story.append(Paragraph("GRADUATE RESEARCH EXPERIENCE", section_style))
        story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor("#cccccc"), spaceAfter=4))

        for exp in tailored.research_experience:
            left = f"<b>{exp.get('title', '')}</b> | {exp.get('company', '')} | {exp.get('location', '')}"
            right = f"{exp.get('start_date', '')} – {exp.get('end_date', '')}"
            story.append(Table(
                [[Paragraph(left, exp_title_style), Paragraph(right, exp_title_style)]],
                colWidths=["75%", "25%"],
                style=TableStyle([
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ])
            ))
            for bullet in exp.get("bullets", []):
                story.append(Paragraph(f"● {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    # === PROJECTS ===
    if tailored.projects:
        story.append(Paragraph("PROJECTS", section_style))
        story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor("#cccccc"), spaceAfter=4))

        for proj in tailored.projects:
            left = f"<b>{proj.get('title', '')}</b> | {proj.get('institution', '')}"
            right = proj.get("date", "")
            story.append(Table(
                [[Paragraph(left, exp_title_style), Paragraph(right, exp_title_style)]],
                colWidths=["75%", "25%"],
                style=TableStyle([
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ])
            ))
            for bullet in proj.get("bullets", []):
                story.append(Paragraph(f"● {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    # === CERTIFICATIONS ===
    if tailored.certifications:
        story.append(Paragraph("CERTIFICATIONS", section_style))
        story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor("#cccccc"), spaceAfter=4))
        story.append(Paragraph(", ".join(tailored.certifications), skills_style))

    doc.build(story)
    return output_path
