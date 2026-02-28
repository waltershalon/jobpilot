"""
JobPilot FastAPI Backend
========================
REST API for the resume tailoring pipeline.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import hashlib
import base64

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.jd_parser import parse_jd, fetch_jd_from_url, ParsedJD
from engine.resume_tailor import tailor_resume, TailoredResume, load_master_profile, generate_suggestions, apply_user_edits
from engine.cover_letter_gen import generate_cover_letter
from engine.ats_optimizer import analyze_ats_coverage
from output.latex_generator import generate_latex
from output.pdf_generator import generate_pdf
from output.docx_generator import generate_docx
from scrapers.linkedin_scraper import scrape_linkedin_jobs
from scrapers.indeed_scraper import scrape_indeed_jobs
from scrapers.greenhouse_lever import scrape_greenhouse_board, scrape_lever_board
from tracker.application_tracker import (
    add_application, update_status, get_applications, get_stats,
    check_duplicate, get_follow_ups, set_follow_up, _load_data
)

app = FastAPI(title="JobPilot API", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure output dir exists
OUTPUT_DIR = PROJECT_ROOT / "generated_resumes"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Pydantic Models ──────────────────────────────────────────────

class TailorRequest(BaseModel):
    jd_url: Optional[str] = None
    jd_text: Optional[str] = None
    user_id: Optional[str] = None  # If set, uses profile from config/profiles/{user_id}.json

class ScrapeRequest(BaseModel):
    source: str = "all"  # all, linkedin, indeed
    query: Optional[str] = None

class BoardRequest(BaseModel):
    url: str
    filter: str = "AI,ML,Data,Engineer"

class StatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class FollowUpRequest(BaseModel):
    days: int = 7

class SuggestionsRequest(BaseModel):
    jd_url: Optional[str] = None
    jd_text: Optional[str] = None
    user_id: Optional[str] = None

class FinalizeRequest(BaseModel):
    session_id: str
    user_edits: dict  # {selected_experiences, bullet_decisions, selected_projects, ...}


# ── Helper ───────────────────────────────────────────────────────

# In-memory session cache for suggestions (30-min TTL)
_suggestion_cache = {}

def _cache_suggestions(session_id: str, data: dict):
    _suggestion_cache[session_id] = {
        "data": data,
        "created": datetime.now()
    }
    # Clean old sessions (>30 min)
    cutoff = datetime.now()
    expired = [k for k, v in _suggestion_cache.items()
               if (cutoff - v["created"]).seconds > 1800]
    for k in expired:
        del _suggestion_cache[k]

def _get_cached_suggestions(session_id: str) -> dict:
    entry = _suggestion_cache.get(session_id)
    if not entry:
        return None
    if (datetime.now() - entry["created"]).seconds > 1800:
        del _suggestion_cache[session_id]
        return None
    return entry["data"]

def sanitize_filename(text: str) -> str:
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in text).strip()[:50]


# ── API Endpoints ────────────────────────────────────────────────

@app.get("/api/health")
def health():
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {"status": "ok", "api_key_set": has_key}


# ── Profile ──────────────────────────────────────────────────────

@app.get("/api/profile")
def get_profile():
    """Get the master profile."""
    try:
        profile = load_master_profile(str(PROJECT_ROOT / "config" / "master_profile.json"))
        return profile
    except Exception as e:
        raise HTTPException(500, str(e))


@app.put("/api/profile")
def update_profile(profile: dict):
    """Update the master profile."""
    try:
        path = PROJECT_ROOT / "config" / "master_profile.json"
        with open(path, "w") as f:
            json.dump(profile, f, indent=2)
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Profile Upload (Multi-user) ──────────────────────────────────

@app.post("/api/profile/upload")
async def upload_resume_profile(file: UploadFile = File(...)):
    """
    Upload a PDF resume. Claude API parses it into a structured profile.
    Returns a user_id that can be used for all subsequent API calls.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    try:
        import anthropic

        # Read file bytes
        pdf_bytes = await file.read()
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        # Generate user_id from file hash
        file_hash = hashlib.sha256(pdf_bytes).hexdigest()[:12]

        client = anthropic.Anthropic()

        parse_prompt = """Parse this resume PDF into a structured JSON profile.
Return ONLY valid JSON with this exact schema (no markdown, no explanation):
{
  "personal": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "optional phone",
    "links": {
      "linkedin": "full URL or empty string",
      "github": "full URL or empty string",
      "website": "full URL or empty string"
    },
    "location": "City, State, Country",
    "target_locations": ["US - Remote"],
    "target_titles": ["Title 1", "Title 2"]
  },
  "education": [
    {
      "id": "edu_1",
      "institution": "University Name",
      "location": "City, State",
      "degree": "Degree Name",
      "gpa": "3.9 or null",
      "start_date": "Mon YYYY",
      "end_date": "Mon YYYY"
    }
  ],
  "technical_skills": {
    "languages": ["Python", "SQL"],
    "data_engineering": ["Spark", "Airflow"],
    "cloud_and_tools": ["AWS", "Docker"],
    "ai_ml": ["PyTorch", "LLMs"]
  },
  "work_experience": [
    {
      "id": "exp_1",
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, State",
      "start_date": "Mon YYYY",
      "end_date": "Present or Mon YYYY",
      "category": "industry",
      "tags": ["python", "ml"],
      "bullets": ["Accomplishment with metrics...", "Another bullet..."]
    }
  ],
  "research_experience": [
    {
      "id": "research_1",
      "title": "Title",
      "company": "Lab/Institution",
      "location": "City, State",
      "start_date": "Mon YYYY",
      "end_date": "Mon YYYY",
      "category": "research",
      "tags": ["ml", "data"],
      "bullets": ["Research accomplishment..."]
    }
  ],
  "projects": [
    {
      "id": "proj_1",
      "title": "Project Name",
      "institution": "Where",
      "date": "Season YYYY",
      "tags": ["tag1"],
      "bullets": ["Project detail..."]
    }
  ],
  "certifications": ["Cert 1", "Cert 2"]
}

RULES:
- Extract ALL information from the resume — don't omit anything
- If a section doesn't exist in the resume, use an empty list []
- For target_titles, infer from the person's experience what roles they'd target
- Keep bullet points as close to the original resume text as possible
- Separate research/academic roles from industry work experience
- Generate unique IDs for each entry (edu_1, exp_1, research_1, proj_1, etc.)"""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": parse_prompt}
                ]
            }]
        )

        # Parse the JSON response
        response_text = message.content[0].text.strip()
        # Handle potential markdown code block wrapping
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

        profile = json.loads(response_text)

        # Use the person's name in the user_id for readability
        name = profile.get("personal", {}).get("name", "user")
        name_slug = name.replace(" ", "_").lower()[:20]
        user_id = f"{name_slug}_{file_hash[:8]}"

        # Save profile
        profiles_dir = PROJECT_ROOT / "config" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_path = profiles_dir / f"{user_id}.json"
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

        return {
            "user_id": user_id,
            "name": profile.get("personal", {}).get("name", "Unknown"),
            "email": profile.get("personal", {}).get("email", ""),
            "education_count": len(profile.get("education", [])),
            "work_experience_count": len(profile.get("work_experience", [])),
            "research_experience_count": len(profile.get("research_experience", [])),
            "projects_count": len(profile.get("projects", [])),
            "profile_path": str(profile_path),
        }

    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Failed to parse resume into profile: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.get("/api/profile/{user_id}")
def get_user_profile(user_id: str):
    """Get a specific user's profile."""
    profile_path = PROJECT_ROOT / "config" / "profiles" / f"{user_id}.json"
    if not profile_path.exists():
        raise HTTPException(404, "Profile not found")
    with open(profile_path) as f:
        return json.load(f)


# ── Tailor (Suggestions Flow) ────────────────────────────────────

@app.post("/api/tailor/suggestions")
def suggestions_endpoint(req: SuggestionsRequest):
    """Phase 1: Generate AI suggestions for resume tailoring (user reviews before finalize)."""
    if not req.jd_url and not req.jd_text:
        raise HTTPException(400, "Provide jd_url or jd_text")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set.")

    try:
        # Parse JD
        if req.jd_url:
            parsed = parse_jd(url=req.jd_url)
        else:
            parsed = parse_jd(text=req.jd_text)

        # Resolve profile
        if req.user_id:
            profile_path = str(PROJECT_ROOT / "config" / "profiles" / f"{req.user_id}.json")
            if not os.path.exists(profile_path):
                raise HTTPException(404, f"Profile not found: {req.user_id}")
        else:
            profile_path = str(PROJECT_ROOT / "config" / "master_profile.json")

        # Generate suggestions
        suggestions = generate_suggestions(parsed, profile_path=profile_path)

        # Cache with session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}_{hash(str(suggestions.get('job', {})))}"
        _cache_suggestions(session_id, suggestions)

        return {
            "session_id": session_id,
            **suggestions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Suggestion generation failed: {str(e)}")


@app.post("/api/tailor/finalize")
def finalize_endpoint(req: FinalizeRequest):
    """Phase 2: Apply user edits and generate final files (PDF, DOCX, cover letter)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set.")

    try:
        # Load cached suggestions
        suggestions = _get_cached_suggestions(req.session_id)
        if not suggestions:
            raise HTTPException(404, "Session expired or not found. Please regenerate suggestions.")

        # Apply user edits to build TailoredResume
        tailored = apply_user_edits(suggestions, req.user_edits)

        # Parse JD for ATS analysis
        job = suggestions.get("job", {})
        parsed = ParsedJD(
            title=job.get("title", ""),
            company=job.get("company", ""),
            location=job.get("location", ""),
            industry=job.get("industry", ""),
            seniority=job.get("seniority", ""),
            summary=job.get("summary", ""),
            required_skills=job.get("required_skills", []),
            tech_stack=job.get("tech_stack", []),
            keywords=job.get("keywords", []),
        )

        # ATS analysis
        ats = analyze_ats_coverage(tailored, parsed)

        # Generate files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_safe = sanitize_filename(parsed.company)
        title_safe = sanitize_filename(parsed.title)
        user_name = sanitize_filename(tailored.personal.get("name", "Candidate").replace(" ", "_"))
        base_name = f"{user_name}_{company_safe}_{title_safe}_{timestamp}"

        # LaTeX → PDF
        latex_result = generate_latex(tailored, str(OUTPUT_DIR), base_name)
        pdf_name = f"{base_name}.pdf"
        tex_name = f"{base_name}.tex"

        # DOCX backup
        docx_path = OUTPUT_DIR / f"{base_name}.docx"
        generate_docx(tailored, str(docx_path))

        # Cover letter
        cl_path = OUTPUT_DIR / f"{base_name}_cover_letter.txt"
        cover_letter = generate_cover_letter(parsed, tailored)
        with open(cl_path, "w") as f:
            f.write(cover_letter)

        # Track
        app_id = add_application(
            company=parsed.company,
            title=parsed.title,
            location=parsed.location,
            url="",
            source="web_ui",
            status="resume_ready",
            resume_path=str(OUTPUT_DIR / pdf_name),
            cover_letter_path=str(cl_path),
            ats_score=ats["overall_score"],
            keywords_matched=ats.get("matched_required", []) + ats.get("matched_tech", []),
            keywords_missing=ats.get("missing_required", []) + ats.get("missing_tech", [])
        )

        # Clean cache
        if req.session_id in _suggestion_cache:
            del _suggestion_cache[req.session_id]

        return {
            "application_id": app_id,
            "job": {
                "title": parsed.title,
                "company": parsed.company,
                "location": parsed.location,
                "seniority": parsed.seniority,
                "industry": parsed.industry,
                "summary": parsed.summary,
            },
            "ats": ats,
            "files": {
                "pdf": f"/api/files/{pdf_name}",
                "tex": f"/api/files/{tex_name}",
                "docx": f"/api/files/{docx_path.name}",
                "cover_letter": f"/api/files/{cl_path.name}",
            },
            "pages": latex_result.get("pages", 0),
            "cover_letter": cover_letter,
            "tailored_skills": tailored.technical_skills,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Finalization failed: {str(e)}")


# ── Tailor (Legacy auto-accept) ─────────────────────────────────

@app.post("/api/tailor")
def tailor_endpoint(req: TailorRequest):
    """Tailor resume for a specific job description (auto-accepts all AI suggestions)."""
    if not req.jd_url and not req.jd_text:
        raise HTTPException(400, "Provide jd_url or jd_text")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set. Export it before starting the server.")

    try:
        # Parse JD
        if req.jd_url:
            parsed = parse_jd(url=req.jd_url)
        else:
            parsed = parse_jd(text=req.jd_text)

        # Resolve profile path (user-specific or default)
        if req.user_id:
            profile_path = str(PROJECT_ROOT / "config" / "profiles" / f"{req.user_id}.json")
            if not os.path.exists(profile_path):
                raise HTTPException(404, f"Profile not found for user_id: {req.user_id}. Upload a resume first.")
        else:
            profile_path = str(PROJECT_ROOT / "config" / "master_profile.json")

        # Tailor
        tailored = tailor_resume(
            parsed,
            profile_path=profile_path
        )

        # ATS analysis
        ats = analyze_ats_coverage(tailored, parsed)

        # Generate files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_safe = sanitize_filename(parsed.company)
        title_safe = sanitize_filename(parsed.title)
        user_name = sanitize_filename(tailored.personal.get("name", "Candidate").replace(" ", "_"))
        base_name = f"{user_name}_{company_safe}_{title_safe}_{timestamp}"

        # Primary: LaTeX → PDF (your .tex template)
        latex_result = generate_latex(tailored, str(OUTPUT_DIR), base_name)
        pdf_name = f"{base_name}.pdf"
        tex_name = f"{base_name}.tex"

        # Also generate DOCX as backup
        docx_path = OUTPUT_DIR / f"{base_name}.docx"
        generate_docx(tailored, str(docx_path))

        # Cover letter
        cl_path = OUTPUT_DIR / f"{base_name}_cover_letter.txt"
        cover_letter = generate_cover_letter(parsed, tailored)
        with open(cl_path, "w") as f:
            f.write(cover_letter)

        # Track
        app_id = add_application(
            company=parsed.company,
            title=parsed.title,
            location=parsed.location,
            url=req.jd_url or "",
            source="web_ui",
            status="resume_ready",
            resume_path=str(OUTPUT_DIR / pdf_name),
            cover_letter_path=str(cl_path),
            ats_score=ats["overall_score"],
            keywords_matched=ats.get("matched_required", []) + ats.get("matched_tech", []),
            keywords_missing=ats.get("missing_required", []) + ats.get("missing_tech", [])
        )

        return {
            "application_id": app_id,
            "job": {
                "title": parsed.title,
                "company": parsed.company,
                "location": parsed.location,
                "seniority": parsed.seniority,
                "industry": parsed.industry,
                "summary": parsed.summary,
            },
            "ats": ats,
            "files": {
                "pdf": f"/api/files/{pdf_name}",
                "tex": f"/api/files/{tex_name}",
                "docx": f"/api/files/{docx_path.name}",
                "cover_letter": f"/api/files/{cl_path.name}",
            },
            "pages": latex_result.get("pages", 0),
            "cover_letter": cover_letter,
            "tailored_skills": tailored.technical_skills,
        }

    except Exception as e:
        raise HTTPException(500, f"Tailoring failed: {str(e)}")


@app.post("/api/parse-jd")
def parse_jd_endpoint(req: TailorRequest):
    """Parse a JD without tailoring (preview)."""
    if not req.jd_url and not req.jd_text:
        raise HTTPException(400, "Provide jd_url or jd_text")

    try:
        if req.jd_url:
            parsed = parse_jd(url=req.jd_url)
        else:
            parsed = parse_jd(text=req.jd_text)

        return parsed.to_dict()
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Files ────────────────────────────────────────────────────────

@app.get("/api/files/{filename}")
def download_file(filename: str):
    """Download a generated file."""
    filepath = OUTPUT_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(
        str(filepath),
        filename=filename,
        media_type="application/octet-stream"
    )


# ── Applications / Tracker ───────────────────────────────────────

@app.get("/api/applications")
def list_applications(status: Optional[str] = None):
    """List all tracked applications."""
    return get_applications(status=status)


@app.get("/api/applications/stats")
def application_stats():
    """Get application statistics."""
    return get_stats()


@app.patch("/api/applications/{app_id}/status")
def update_app_status(app_id: int, req: StatusUpdate):
    """Update application status."""
    update_status(app_id, req.status, req.notes)
    return {"status": "updated"}


@app.post("/api/applications/{app_id}/followup")
def set_app_follow_up(app_id: int, req: FollowUpRequest):
    """Set a follow-up reminder."""
    set_follow_up(app_id, req.days)
    return {"status": "follow-up set", "days": req.days}


@app.get("/api/applications/followups")
def list_follow_ups():
    """Get pending follow-ups."""
    return get_follow_ups()


# ── Scrapers ─────────────────────────────────────────────────────

@app.post("/api/scrape")
def scrape_jobs(req: ScrapeRequest):
    """Scrape jobs from specified sources."""
    all_jobs = []
    query = req.query or "AI ML Engineer"

    try:
        if req.source in ("all", "linkedin"):
            jobs = scrape_linkedin_jobs(query, "United States", max_results=15)
            all_jobs.extend([j.__dict__ for j in jobs])

        if req.source in ("all", "indeed"):
            jobs = scrape_indeed_jobs(query, "United States", max_results=15)
            all_jobs.extend([j.__dict__ for j in jobs])

        # Deduplicate
        seen = set()
        unique = []
        for job in all_jobs:
            key = (job.get("company", "").lower(), job.get("title", "").lower())
            if key not in seen and job.get("title"):
                seen.add(key)
                unique.append(job)

        # Track new ones
        new_count = 0
        for job in unique:
            if not check_duplicate(job["company"], job["title"]):
                add_application(
                    company=job["company"],
                    title=job["title"],
                    location=job.get("location", ""),
                    url=job.get("url", ""),
                    source=job.get("source", ""),
                    status="discovered"
                )
                new_count += 1

        return {
            "total_found": len(unique),
            "new_added": new_count,
            "jobs": unique[:20]
        }

    except Exception as e:
        raise HTTPException(500, f"Scraping failed: {str(e)}")


@app.post("/api/scrape/board")
def scrape_board(req: BoardRequest):
    """Scrape a specific Greenhouse/Lever board."""
    try:
        if "greenhouse" in req.url:
            jobs = scrape_greenhouse_board(req.url, title_filter=req.filter)
        elif "lever" in req.url:
            jobs = scrape_lever_board(req.url, title_filter=req.filter)
        else:
            raise HTTPException(400, "URL must be a Greenhouse or Lever board")

        results = [j.__dict__ for j in jobs]

        new_count = 0
        for job in results:
            if not check_duplicate(job["company"], job["title"]):
                add_application(
                    company=job["company"],
                    title=job["title"],
                    location=job.get("location", ""),
                    url=job.get("url", ""),
                    source=job.get("source", ""),
                    status="discovered"
                )
                new_count += 1

        return {"total_found": len(results), "new_added": new_count, "jobs": results}

    except Exception as e:
        raise HTTPException(500, str(e))


# ── Serve React Frontend (production) ────────────────────────────

FRONTEND_DIR = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 JobPilot API starting on http://localhost:9000")
    print("📖 API docs: http://localhost:9000/docs")
    print("⚛️  Frontend: http://localhost:5173 (run npm dev separately)\n")
    uvicorn.run(app, host="0.0.0.0", port=9000)

