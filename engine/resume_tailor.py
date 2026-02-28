"""
Resume Tailor Engine
Takes master profile + parsed JD → generates a tailored resume as structured data.
Uses Claude API for intelligent selection and rewording.
"""

import json
import re
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

import anthropic

from engine.jd_parser import ParsedJD


@dataclass
class TailoredResume:
    """Output of the tailoring engine - ready for rendering."""
    target_title: str = ""
    target_company: str = ""
    personal: dict = field(default_factory=dict)
    education: list = field(default_factory=list)
    technical_skills: dict = field(default_factory=dict)
    work_experience: list = field(default_factory=list)
    research_experience: list = field(default_factory=list)
    projects: list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    ats_score: float = 0.0
    keywords_matched: list = field(default_factory=list)
    keywords_missing: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


def load_master_profile(path: str = "config/master_profile.json") -> dict:
    """Load master profile JSON."""
    with open(path) as f:
        return json.load(f)


def compute_ats_score(tailored: TailoredResume, parsed_jd: ParsedJD) -> float:
    """Compute keyword match score between tailored resume and JD."""
    jd_keywords = set(k.lower() for k in parsed_jd.keywords + parsed_jd.required_skills + parsed_jd.tech_stack)
    if not jd_keywords:
        return 1.0

    # Build resume text blob
    resume_text = ""
    for sk_category in tailored.technical_skills.values():
        if isinstance(sk_category, list):
            resume_text += " ".join(sk_category) + " "
    for exp in tailored.work_experience + tailored.research_experience:
        for bullet in exp.get("bullets", []):
            resume_text += bullet + " "
    for proj in tailored.projects:
        for bullet in proj.get("bullets", []):
            resume_text += bullet + " "

    resume_lower = resume_text.lower()

    matched = []
    missing = []
    for kw in jd_keywords:
        if kw.lower() in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    tailored.keywords_matched = matched
    tailored.keywords_missing = missing
    score = len(matched) / len(jd_keywords) if jd_keywords else 1.0
    tailored.ats_score = round(score, 2)
    return score


def tailor_resume(
    parsed_jd: ParsedJD,
    master_profile: dict = None,
    profile_path: str = "config/master_profile.json",
    api_key: str = None,
    max_work_exp: int = 2,
    max_research_exp: int = 2,
    max_bullets: int = 3,
    max_projects: int = 1
) -> TailoredResume:
    """
    Generate a tailored resume from master profile + parsed JD.
    """
    if master_profile is None:
        master_profile = load_master_profile(profile_path)

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY environment variable or pass api_key")

    client = anthropic.Anthropic(api_key=api_key)

    # Combine all experiences for the LLM to choose from
    all_experiences = []
    for exp in master_profile.get("work_experience", []):
        all_experiences.append({**exp, "source": "work_experience"})
    for exp in master_profile.get("research_experience", []):
        all_experiences.append({**exp, "source": "research_experience"})

    prompt = f"""You are an expert resume tailor and ATS optimization specialist.

CRITICAL CONSTRAINT: The output MUST fit on ONE PAGE of a LaTeX resume (letter paper, 10pt font, tight margins).
This means strict content limits — do NOT exceed them.

TARGET JOB:
- Title: {parsed_jd.title}
- Company: {parsed_jd.company}
- Industry: {parsed_jd.industry}
- Required Skills: {json.dumps(parsed_jd.required_skills)}
- Preferred Skills: {json.dumps(parsed_jd.preferred_skills)}
- Tech Stack: {json.dumps(parsed_jd.tech_stack)}
- Keywords: {json.dumps(parsed_jd.keywords)}
- Summary: {parsed_jd.summary}

CANDIDATE'S FULL EXPERIENCE:
{json.dumps(all_experiences, indent=2)}

CANDIDATE'S PROJECTS:
{json.dumps(master_profile.get('projects', []), indent=2)}

CANDIDATE'S SKILLS:
{json.dumps(master_profile.get('technical_skills', {}), indent=2)}

STRICT INSTRUCTIONS (one-page constraint):
1. Select EXACTLY {max_work_exp} work experiences and {max_research_exp} research experiences (most relevant).
2. For each experience, write EXACTLY {max_bullets} bullets. Each bullet MUST be a SINGLE LINE (under 120 characters).
   - Naturally incorporate keywords from the JD
   - Keep quantifiable achievements and metrics
   - Be concise — no filler words, every word earns its spot
   - Maintain truthfulness — only reword existing content, never fabricate
3. Select EXACTLY {max_projects} project (most relevant). Give it 2 bullets max, each under 110 characters.
4. Reorder technical skills to lead with the most relevant for this role. Keep max 6-7 items per category.
5. Group selected experiences into "work_experience" and "research_experience" based on their source field.

Return ONLY valid JSON:
{{
  "technical_skills": {{
    "languages": ["ordered by relevance"],
    "data_engineering": ["ordered by relevance"],
    "cloud_and_tools": ["ordered by relevance"],
    "ai_ml": ["ordered by relevance"]
  }},
  "selected_work_experience": [
    {{
      "id": "original_id",
      "title": "original or slightly adjusted title",
      "company": "company",
      "location": "location",
      "start_date": "date",
      "end_date": "date",
      "bullets": ["rewritten bullet 1", "rewritten bullet 2", ...]
    }}
  ],
  "selected_research_experience": [
    {{
      "id": "original_id",
      "title": "title",
      "company": "company",
      "location": "location",
      "start_date": "date",
      "end_date": "date",
      "bullets": ["rewritten bullet 1", ...]
    }}
  ],
  "selected_projects": [
    {{
      "id": "original_id",
      "title": "title",
      "institution": "institution",
      "date": "date",
      "bullets": ["rewritten bullets"]
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        raise ValueError("Failed to get tailored resume JSON from API")

    data = json.loads(json_match.group())

    # Build the tailored resume
    tailored = TailoredResume(
        target_title=parsed_jd.title,
        target_company=parsed_jd.company,
        personal=master_profile.get("personal", {}),
        education=master_profile.get("education", []),
        technical_skills=data.get("technical_skills", master_profile.get("technical_skills", {})),
        work_experience=data.get("selected_work_experience", []),
        research_experience=data.get("selected_research_experience", []),
        projects=data.get("selected_projects", []),
        certifications=master_profile.get("certifications", [])
    )

    # Compute ATS match score
    compute_ats_score(tailored, parsed_jd)

    return tailored


def generate_suggestions(
    parsed_jd: ParsedJD,
    master_profile: dict = None,
    profile_path: str = "config/master_profile.json",
    api_key: str = None,
) -> dict:
    """
    Phase 1: Generate AI suggestions without committing to a final resume.
    Returns structured suggestions for the user to accept/reject/edit.
    """
    if master_profile is None:
        master_profile = load_master_profile(profile_path)

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY environment variable or pass api_key")

    client = anthropic.Anthropic(api_key=api_key)

    all_experiences = []
    for exp in master_profile.get("work_experience", []):
        all_experiences.append({**exp, "source": "work_experience"})
    for exp in master_profile.get("research_experience", []):
        all_experiences.append({**exp, "source": "research_experience"})

    prompt = f"""You are an expert resume tailor and ATS optimization specialist.
You are generating SUGGESTIONS for the user to review — NOT a final resume.
The user will accept, reject, or edit each suggestion before generating the final PDF.

TARGET JOB:
- Title: {parsed_jd.title}
- Company: {parsed_jd.company}
- Industry: {parsed_jd.industry}
- Required Skills: {json.dumps(parsed_jd.required_skills)}
- Preferred Skills: {json.dumps(parsed_jd.preferred_skills)}
- Tech Stack: {json.dumps(parsed_jd.tech_stack)}
- Keywords: {json.dumps(parsed_jd.keywords)}
- Summary: {parsed_jd.summary}

CANDIDATE'S FULL EXPERIENCE:
{json.dumps(all_experiences, indent=2)}

CANDIDATE'S PROJECTS:
{json.dumps(master_profile.get('projects', []), indent=2)}

CANDIDATE'S SKILLS:
{json.dumps(master_profile.get('technical_skills', {}), indent=2)}

INSTRUCTIONS — Generate suggestions for EVERY experience and project:

1. For EACH work/research experience, generate suggestions:
   - "selected": true/false — whether you recommend including it
   - "relevance_score": 1-10 — how relevant to this JD
   - "relevance_reason": brief reason (10 words max)
   - For EACH bullet in that experience:
     - "original": the original bullet text
     - "suggested": your reworded version (under 120 chars, incorporate JD keywords naturally)
     - "action": "keep" (original is good), "revise" (suggest rewrite), or "remove" (not relevant)
     - "reason": brief reason for the suggestion (15 words max)
     - "keywords_added": list of JD keywords you incorporated

2. For EACH project:
   - "selected": true/false
   - "relevance_score": 1-10
   - Same bullet format as above

3. Skill reordering: reorder each category to lead with most JD-relevant items.

4. Missing keyword suggestions: For each JD keyword NOT naturally covered,
   suggest WHERE it could be added (which experience, which bullet).

Return ONLY valid JSON:
{{
  "experiences": [
    {{
      "id": "original_id",
      "source": "work_experience or research_experience",
      "title": "Job Title",
      "company": "Company",
      "location": "Location",
      "start_date": "date",
      "end_date": "date",
      "selected": true,
      "relevance_score": 8,
      "relevance_reason": "Direct ML engineering match",
      "bullets": [
        {{
          "original": "Original bullet text from resume...",
          "suggested": "Reworded version with keywords...",
          "action": "revise",
          "reason": "Added Docker and Kubernetes keywords",
          "keywords_added": ["Docker", "Kubernetes"]
        }}
      ]
    }}
  ],
  "projects": [
    {{
      "id": "proj_id",
      "title": "Project Title",
      "institution": "Where",
      "date": "When",
      "selected": true,
      "relevance_score": 7,
      "relevance_reason": "NLP skills match",
      "bullets": [
        {{
          "original": "Original...",
          "suggested": "Revised...",
          "action": "revise",
          "reason": "Added relevant NLP keywords",
          "keywords_added": ["NLP"]
        }}
      ]
    }}
  ],
  "skills": {{
    "languages": ["ordered by relevance"],
    "data_engineering": ["ordered"],
    "cloud_and_tools": ["ordered"],
    "ai_ml": ["ordered"]
  }},
  "keyword_suggestions": [
    {{
      "keyword": "missing keyword",
      "target_experience_id": "exp_id",
      "target_bullet_index": 0,
      "suggestion": "How to naturally incorporate it"
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        raise ValueError("Failed to get suggestions JSON from API")

    suggestions = json.loads(json_match.group())

    # Attach metadata
    suggestions["job"] = {
        "title": parsed_jd.title,
        "company": parsed_jd.company,
        "location": parsed_jd.location,
        "industry": parsed_jd.industry,
        "seniority": parsed_jd.seniority,
        "summary": parsed_jd.summary,
        "required_skills": parsed_jd.required_skills,
        "tech_stack": parsed_jd.tech_stack,
        "keywords": parsed_jd.keywords,
    }
    suggestions["profile"] = {
        "personal": master_profile.get("personal", {}),
        "education": master_profile.get("education", []),
        "certifications": master_profile.get("certifications", []),
    }

    return suggestions


def apply_user_edits(suggestions: dict, user_edits: dict) -> TailoredResume:
    """
    Phase 2: Apply user's accept/reject/edit decisions to build a TailoredResume.

    user_edits format:
    {
      "selected_experiences": {"exp_id": true/false, ...},
      "bullet_decisions": {
        "exp_id": {
          "0": {"action": "accept"|"reject"|"edit", "text": "custom text if edit"},
          "1": {...}
        }
      },
      "selected_projects": {"proj_id": true/false, ...},
      "project_bullet_decisions": {
        "proj_id": {
          "0": {"action": "accept"|"reject"|"edit", "text": "..."}
        }
      },
      "skills": { ... }  // optional override
    }
    """
    profile = suggestions.get("profile", {})
    job = suggestions.get("job", {})
    sel_exp = user_edits.get("selected_experiences", {})
    bullet_dec = user_edits.get("bullet_decisions", {})
    sel_proj = user_edits.get("selected_projects", {})
    proj_bullet_dec = user_edits.get("project_bullet_decisions", {})

    work_experience = []
    research_experience = []

    for exp in suggestions.get("experiences", []):
        exp_id = exp.get("id", "")
        # Check if user explicitly toggled, otherwise use AI recommendation
        include = sel_exp.get(exp_id, exp.get("selected", False))
        if not include:
            continue

        # Build bullets from decisions
        bullets = []
        exp_decisions = bullet_dec.get(exp_id, {})
        for i, bullet_info in enumerate(exp.get("bullets", [])):
            decision = exp_decisions.get(str(i), {})
            action = decision.get("action", "accept")

            if action == "reject":
                # Use original
                bullets.append(bullet_info.get("original", ""))
            elif action == "edit":
                # Use custom text
                bullets.append(decision.get("text", bullet_info.get("suggested", bullet_info.get("original", ""))))
            else:
                # Accept AI suggestion
                if bullet_info.get("action") == "remove":
                    continue  # Skip removed bullets
                bullets.append(bullet_info.get("suggested", bullet_info.get("original", "")))

        entry = {
            "id": exp_id,
            "title": exp.get("title", ""),
            "company": exp.get("company", ""),
            "location": exp.get("location", ""),
            "start_date": exp.get("start_date", ""),
            "end_date": exp.get("end_date", ""),
            "bullets": bullets,
        }

        if exp.get("source") == "research_experience":
            research_experience.append(entry)
        else:
            work_experience.append(entry)

    projects = []
    for proj in suggestions.get("projects", []):
        proj_id = proj.get("id", "")
        include = sel_proj.get(proj_id, proj.get("selected", False))
        if not include:
            continue

        bullets = []
        p_decisions = proj_bullet_dec.get(proj_id, {})
        for i, bullet_info in enumerate(proj.get("bullets", [])):
            decision = p_decisions.get(str(i), {})
            action = decision.get("action", "accept")
            if action == "reject":
                bullets.append(bullet_info.get("original", ""))
            elif action == "edit":
                bullets.append(decision.get("text", bullet_info.get("suggested", bullet_info.get("original", ""))))
            else:
                if bullet_info.get("action") == "remove":
                    continue
                bullets.append(bullet_info.get("suggested", bullet_info.get("original", "")))

        projects.append({
            "id": proj_id,
            "title": proj.get("title", ""),
            "institution": proj.get("institution", ""),
            "date": proj.get("date", ""),
            "bullets": bullets,
        })

    skills = user_edits.get("skills", suggestions.get("skills", {}))

    tailored = TailoredResume(
        target_title=job.get("title", ""),
        target_company=job.get("company", ""),
        personal=profile.get("personal", {}),
        education=profile.get("education", []),
        technical_skills=skills,
        work_experience=work_experience,
        research_experience=research_experience,
        projects=projects,
        certifications=profile.get("certifications", []),
    )

    return tailored


if __name__ == "__main__":
    # Quick test
    from engine.jd_parser import ParsedJD
    sample_jd = ParsedJD(
        title="ML Engineer",
        company="Test Corp",
        required_skills=["Python", "PyTorch", "AWS"],
        tech_stack=["Docker", "Kubernetes"],
        keywords=["machine learning", "deployment", "CI/CD"]
    )
    result = tailor_resume(sample_jd)
    print(result.to_json())
