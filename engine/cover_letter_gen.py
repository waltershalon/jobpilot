"""
Cover Letter Generator
Generates targeted cover letters using Claude API.
"""

import json
import os
from typing import Optional

import anthropic

from engine.jd_parser import ParsedJD
from engine.resume_tailor import TailoredResume


def generate_cover_letter(
    parsed_jd: ParsedJD,
    tailored_resume: TailoredResume,
    api_key: str = None,
    tone: str = "professional but personable",
    max_words: int = 350
) -> str:
    """
    Generate a cover letter tailored to the job.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY environment variable or pass api_key")

    client = anthropic.Anthropic(api_key=api_key)

    # Build experience summary from tailored resume
    exp_summary = []
    for exp in tailored_resume.work_experience + tailored_resume.research_experience:
        exp_summary.append(f"- {exp.get('title', '')} at {exp.get('company', '')}: " +
                          "; ".join(exp.get("bullets", [])[:2]))

    # Dynamic role + education from profile
    candidate_name = tailored_resume.personal.get("name", "Candidate")
    current_role = "Professional"
    if tailored_resume.work_experience:
        w = tailored_resume.work_experience[0]
        current_role = f"{w.get('title', '')} at {w.get('company', '')}"
    education_line = "N/A"
    if tailored_resume.education:
        e = tailored_resume.education[0]
        gpa_str = f" (GPA {e['gpa']})" if e.get("gpa") else ""
        education_line = f"{e.get('degree', '')} from {e.get('institution', '')}{gpa_str}"

    prompt = f"""Write a cover letter for this job application.

CANDIDATE:
- Name: {candidate_name}
- Current Role: {current_role}
- Education: {education_line}
- Key strengths relevant to this role:
{chr(10).join(exp_summary[:4])}

TARGET JOB:
- Title: {parsed_jd.title}
- Company: {parsed_jd.company}
- Industry: {parsed_jd.industry}
- Key requirements: {', '.join(parsed_jd.required_skills[:8])}
- Summary: {parsed_jd.summary}

INSTRUCTIONS:
- Tone: {tone}
- Max {max_words} words
- NO generic filler ("I am writing to express my interest...")
- Open with something specific about the company or role that connects to the candidate's background
- Highlight 2-3 most relevant experiences with specific results/numbers
- Connect the candidate's unique background as a differentiator if relevant to the role
- Close with a confident call to action
- Do NOT include addresses, dates, or "Dear Hiring Manager" headers (those go in the template)
- Just the letter body paragraphs

Return ONLY the cover letter text, no JSON wrapping."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()


if __name__ == "__main__":
    print("Cover letter generator ready. Use via main.py or import directly.")
