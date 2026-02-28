"""
ATS Optimizer
Scores keyword coverage and suggests improvements.
"""

import json
from typing import Tuple
from engine.jd_parser import ParsedJD
from engine.resume_tailor import TailoredResume


def analyze_ats_coverage(tailored: TailoredResume, parsed_jd: ParsedJD) -> dict:
    """
    Detailed ATS analysis: which keywords are covered, which are missing,
    and suggestions for improvement.
    """
    # Collect all JD keywords
    all_jd_keywords = set()
    for kw in parsed_jd.keywords:
        all_jd_keywords.add(kw.lower())
    for skill in parsed_jd.required_skills:
        all_jd_keywords.add(skill.lower())
    for skill in parsed_jd.preferred_skills:
        all_jd_keywords.add(skill.lower())
    for tech in parsed_jd.tech_stack:
        all_jd_keywords.add(tech.lower())

    # Build resume text
    resume_text = ""
    for category, skills in tailored.technical_skills.items():
        if isinstance(skills, list):
            resume_text += " ".join(skills).lower() + " "
    for exp in tailored.work_experience + tailored.research_experience:
        for bullet in exp.get("bullets", []):
            resume_text += bullet.lower() + " "
        resume_text += exp.get("title", "").lower() + " "
    for proj in tailored.projects:
        for bullet in proj.get("bullets", []):
            resume_text += bullet.lower() + " "
        resume_text += proj.get("title", "").lower() + " "

    # Categorize keywords
    matched_required = []
    missing_required = []
    matched_preferred = []
    missing_preferred = []
    matched_tech = []
    missing_tech = []

    for skill in parsed_jd.required_skills:
        if skill.lower() in resume_text:
            matched_required.append(skill)
        else:
            missing_required.append(skill)

    for skill in parsed_jd.preferred_skills:
        if skill.lower() in resume_text:
            matched_preferred.append(skill)
        else:
            missing_preferred.append(skill)

    for tech in parsed_jd.tech_stack:
        if tech.lower() in resume_text:
            matched_tech.append(tech)
        else:
            missing_tech.append(tech)

    # Overall score
    total = len(all_jd_keywords)
    matched_all = set(k.lower() for k in matched_required + matched_preferred + matched_tech)
    score = len(matched_all) / total if total > 0 else 1.0

    # Priority score: required skills matter more
    req_total = len(parsed_jd.required_skills)
    req_score = len(matched_required) / req_total if req_total > 0 else 1.0

    return {
        "overall_score": round(score, 2),
        "required_skills_score": round(req_score, 2),
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "missing_preferred": missing_preferred,
        "matched_tech": matched_tech,
        "missing_tech": missing_tech,
        "total_keywords": total,
        "total_matched": len(matched_all),
        "recommendation": _get_recommendation(score, req_score, missing_required)
    }


def _get_recommendation(score: float, req_score: float, missing_required: list) -> str:
    """Generate actionable recommendation based on scores."""
    if req_score >= 0.9 and score >= 0.7:
        return "Strong match. Resume is well-tailored for this role."
    elif req_score >= 0.7:
        missing = ", ".join(missing_required[:5])
        return f"Good match but missing some required skills: {missing}. Consider if you can add these through rewording."
    elif req_score >= 0.5:
        return f"Moderate match. Missing several required skills. This role may be a stretch but worth applying if interested."
    else:
        return "Weak match. Consider whether this role aligns with your background before applying."


def print_ats_report(analysis: dict):
    """Pretty print ATS analysis."""
    print("\n" + "=" * 60)
    print("ATS KEYWORD ANALYSIS REPORT")
    print("=" * 60)
    print(f"\nOverall Score: {analysis['overall_score']:.0%}")
    print(f"Required Skills Score: {analysis['required_skills_score']:.0%}")
    print(f"Keywords: {analysis['total_matched']}/{analysis['total_keywords']} matched")

    if analysis['matched_required']:
        print(f"\n✓ Required Skills Matched: {', '.join(analysis['matched_required'])}")
    if analysis['missing_required']:
        print(f"\n✗ Required Skills MISSING: {', '.join(analysis['missing_required'])}")
    if analysis['matched_tech']:
        print(f"\n✓ Tech Stack Matched: {', '.join(analysis['matched_tech'])}")
    if analysis['missing_tech']:
        print(f"\n✗ Tech Stack Missing: {', '.join(analysis['missing_tech'])}")

    print(f"\nRecommendation: {analysis['recommendation']}")
    print("=" * 60)
