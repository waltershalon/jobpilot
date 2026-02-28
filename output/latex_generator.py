"""
LaTeX Resume Generator
Generates a tailored resume as .tex and compiles to a one-page PDF.
Matches the original .tex template (config/template_reference.tex).
All personal info comes from the profile — supports any user.
"""

import os
import subprocess
from pathlib import Path

from engine.resume_tailor import TailoredResume


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text


def _build_bullet_items(bullets: list) -> str:
    """Build LaTeX bullet items from a list."""
    lines = []
    for b in bullets:
        text = _escape_latex(b)
        lines.append(f"          \\resumeItem{{\\textbullet\\ {text}}}")
    return "\n".join(lines)


def _get_page_count(pdf_path: str) -> int:
    """Get page count of a PDF."""
    try:
        result = subprocess.run(
            ["pdfinfo", pdf_path], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split("\n"):
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except Exception:
        pass
    return 0


def _build_contact_line(personal: dict) -> str:
    """Build the contact/links line dynamically from profile."""
    parts = []
    email = personal.get("email", "")
    if email:
        parts.append(f"\\href{{mailto:{email}}}{{{_escape_latex(email)}}}")

    phone = personal.get("phone", "")
    if phone:
        parts.append(_escape_latex(phone))

    links = personal.get("links", {})
    if links.get("linkedin"):
        url = links["linkedin"]
        if not url.startswith("http"):
            url = f"https://linkedin.com/in/{url}"
        parts.append(f"\\href{{{url}}}{{LinkedIn}}")
    if links.get("github"):
        url = links["github"]
        if not url.startswith("http"):
            url = f"https://github.com/{url}"
        parts.append(f"\\href{{{url}}}{{GitHub}}")
    if links.get("website"):
        url = links["website"]
        if not url.startswith("http"):
            url = f"https://{url}"
        parts.append(f"\\href{{{url}}}{{Website}}")

    return " $|$ ".join(parts)


def generate_latex(tailored: TailoredResume, output_dir: str, base_name: str) -> dict:
    """
    Generate .tex file and compile to one-page PDF.
    All personal info comes from tailored.personal — nothing hardcoded.
    Template matches config/template_reference.tex exactly.
    Returns dict with paths: {"tex": path, "pdf": path, "pages": int}
    """
    personal = tailored.personal
    name = _escape_latex(personal.get("name", ""))
    contact_line = _build_contact_line(personal)

    # ── Build sections ───────────────────────────────────────────

    # Education — vspace between entries to prevent overlap
    edu_items = []
    for edu in tailored.education:
        gpa_str = f" (GPA: {edu['gpa']})" if edu.get('gpa') else ""
        edu_items.append(f"""  \\resumeSubheading
      {{{_escape_latex(edu.get('institution', ''))}}}{{{_escape_latex(edu.get('location', ''))}}}
      {{{_escape_latex(edu.get('degree', ''))}{gpa_str}}}{{{_escape_latex(edu.get('start_date', ''))} -- {_escape_latex(edu.get('end_date', ''))}}}""")
    edu_section = "\n  \\vspace{2pt}\n".join(edu_items)

    # Technical Skills
    skill_labels = {
        "languages": "Programming Languages",
        "data_engineering": "Data Engineering",
        "cloud_and_tools": "Libraries \\& Tools",
        "ai_ml": "AI/ML",
    }
    skill_items = []
    for key, label in skill_labels.items():
        skills = tailored.technical_skills.get(key, [])
        if skills:
            escaped = [_escape_latex(s) for s in skills]
            skill_items.append(
                f"  \\resumeItem{{\\textbf{{{label}}}: {', '.join(escaped)}}}"
            )
    skills_section = "\n".join(skill_items)

    # Work Experience
    work_items = []
    for exp in tailored.work_experience:
        bullets = _build_bullet_items(exp.get("bullets", []))
        work_items.append(f"""  \\resumeSubheading
      {{{_escape_latex(exp.get('title', ''))}}}{{{_escape_latex(exp.get('start_date', ''))} -- {_escape_latex(exp.get('end_date', ''))}}}
      {{{_escape_latex(exp.get('company', ''))}}}{{{_escape_latex(exp.get('location', ''))}}}
      \\resumeSubHeadingList
{bullets}
      \\resumeSubHeadingListEnd""")
    work_section = "\n".join(work_items)

    # Research Experience
    research_items = []
    for exp in tailored.research_experience:
        bullets = _build_bullet_items(exp.get("bullets", []))
        research_items.append(f"""  \\resumeSubheading
      {{{_escape_latex(exp.get('title', ''))}}}{{{_escape_latex(exp.get('start_date', ''))} -- {_escape_latex(exp.get('end_date', ''))}}}
      {{{_escape_latex(exp.get('company', ''))}}}{{{_escape_latex(exp.get('location', ''))}}}
      \\resumeSubHeadingList
{bullets}
      \\resumeSubHeadingListEnd""")
    research_section = "\n".join(research_items)

    # Projects
    project_items = []
    for proj in tailored.projects:
        bullets = _build_bullet_items(proj.get("bullets", []))
        project_items.append(f"""  \\resumeSubheading
      {{{_escape_latex(proj.get('title', ''))}}}{{{_escape_latex(proj.get('date', ''))}}}
      {{{_escape_latex(proj.get('institution', ''))}}}{{}}
      \\resumeSubHeadingList
{bullets}
      \\resumeSubHeadingListEnd""")
    projects_section = "\n".join(project_items)

    # Certifications — compact comma-separated line to save vertical space
    if tailored.certifications:
        escaped_certs = [_escape_latex(c) for c in tailored.certifications]
        certs_section = f"  \\resumeItem{{{', '.join(escaped_certs)}}}"
    else:
        certs_section = ""

    # ── Assemble sections (order: Skills, Experience, Research, Projects, Education, Certs)

    sections = []

    sections.append(f"""\\section{{Technical Skills}}
\\resumeSubHeadingList
{skills_section}
\\resumeSubHeadingListEnd""")

    if work_section:
        sections.append(f"""\\section{{Experience}}
\\resumeSubHeadingList
{work_section}
\\resumeSubHeadingListEnd""")

    if research_section:
        sections.append(f"""\\section{{Research Experience}}
\\resumeSubHeadingList
{research_section}
\\resumeSubHeadingListEnd""")

    if projects_section:
        sections.append(f"""\\section{{Projects}}
\\resumeSubHeadingList
{projects_section}
\\resumeSubHeadingListEnd""")

    sections.append(f"""\\section{{Education}}
\\resumeSubHeadingList
{edu_section}
\\resumeSubHeadingListEnd""")

    if certs_section:
        sections.append(f"""\\section{{Certifications}}
\\resumeSubHeadingList
{certs_section}
\\resumeSubHeadingListEnd""")

    body = "\n\n".join(sections)

    # ── Full .tex — matches template_reference.tex exactly ───────
    # Only diff: helvet instead of roboto (roboto not in texlive)

    tex_content = rf"""\documentclass[letterpaper,10pt]{{article}}

\usepackage{{latexsym}}
\usepackage[empty]{{fullpage}}
\usepackage{{titlesec}}
\usepackage{{marvosym}}
\usepackage[usenames,dvipsnames]{{color}}
\usepackage{{verbatim}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[english]{{babel}}
\usepackage{{tabularx}}
\input{{glyphtounicode}}

% Font options
\usepackage[scaled=0.95]{{helvet}}
\renewcommand{{\familydefault}}{{\sfdefault}}

\pagestyle{{fancy}}
\fancyhf{{}}
\fancyfoot{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

\addtolength{{\oddsidemargin}}{{-0.5in}}
\addtolength{{\evensidemargin}}{{-0.5in}}
\addtolength{{\textwidth}}{{1in}}
\addtolength{{\topmargin}}{{-.5in}}
\addtolength{{\textheight}}{{1.5in}}

\urlstyle{{same}}
\raggedbottom
\raggedright
\setlength{{\tabcolsep}}{{0in}}

% Section formatting
\titleformat{{\section}}{{\Large\bfseries\scshape\raggedright}}{{}}{{0em}}{{}}[\titlerule]
\titlespacing*{{\section}}{{0pt}}{{4pt}}{{4pt}}

% Ensure PDF is machine readable
\pdfgentounicode=1

% Custom commands
\newcommand{{\resumeItem}}[1]{{\item\small{{#1}}}}
\newcommand{{\resumeSubheading}}[4]{{
\vspace{{-1pt}}\item
  \begin{{tabular*}}{{0.97\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}
    \textbf{{#1}} & #2 \\
    \textit{{#3}} & \textit{{#4}} \\
  \end{{tabular*}}\vspace{{-7pt}}
}}
\renewcommand\labelitemii{{$\vcenter{{\hbox{{\tiny$\bullet$}}}}$}}
\newcommand{{\resumeSubHeadingList}}{{\begin{{itemize}}[leftmargin=0.15in, label={{}}]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}

\begin{{document}}

\begin{{center}}
  \textbf{{\Huge {name}}} \\
  \small {contact_line}
\end{{center}}

{body}

\end{{document}}"""

    # ── Write and compile ────────────────────────────────────────

    os.makedirs(output_dir, exist_ok=True)
    tex_path = os.path.join(output_dir, f"{base_name}.tex")
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

    with open(tex_path, "w") as f:
        f.write(tex_content)

    try:
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode",
                 "-output-directory", output_dir, tex_path],
                capture_output=True, text=True, timeout=30, cwd=output_dir
            )

        pages = _get_page_count(pdf_path) if os.path.exists(pdf_path) else 0
        if pages > 1:
            print(f"WARNING: Resume is {pages} pages — content needs trimming.")

        for ext in [".aux", ".log", ".out"]:
            aux_file = os.path.join(output_dir, f"{base_name}{ext}")
            if os.path.exists(aux_file):
                try:
                    os.remove(aux_file)
                except OSError:
                    pass

    except subprocess.TimeoutExpired:
        print("LaTeX compilation timed out")
    except FileNotFoundError:
        print("pdflatex not found. Install texlive: apt install texlive-latex-extra")

    return {
        "tex": tex_path,
        "pdf": pdf_path if os.path.exists(pdf_path) else None,
        "pages": _get_page_count(pdf_path) if os.path.exists(pdf_path) else 0,
    }
