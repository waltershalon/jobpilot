# JobPilot

Automated job application pipeline that tailors resumes and cover letters to specific job descriptions using AI. JobPilot parses job postings, matches them against your profile, and generates ATS-optimized resumes in LaTeX/PDF and DOCX formats.

## Features

- **AI-Powered Resume Tailoring** - Uses Claude API to intelligently select and rewrite resume bullets for each job description
- **ATS Optimization** - Keyword analysis and scoring to maximize Applicant Tracking System compatibility
- **Multiple Output Formats** - Generates LaTeX (PDF) and DOCX resumes
- **Cover Letter Generation** - Auto-generates tailored cover letters for each application
- **Job Scraping** - Scrapes job listings from LinkedIn, Indeed, and Greenhouse/Lever boards
- **Application Tracking** - JSON-based tracker with dashboard and follow-up reminders
- **Web UI** - React frontend for interactive resume tailoring with real-time preview
- **REST API** - FastAPI backend for programmatic access

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Data-verse-ai/jobpilot.git
cd jobpilot
pip install -r requirements.txt
```

### 2. Configure

```bash
# Set up your API key
cp .env.example .env
# Edit .env with your Anthropic API key

# Set up your profile
cp config/master_profile.example.json config/master_profile.json
# Edit config/master_profile.json with your career data
```

### 3. Tailor a resume

```bash
# From a job posting URL
python main.py tailor --jd "https://boards.greenhouse.io/company/jobs/12345"

# From pasted text
python main.py tailor --text "We are looking for an ML Engineer..."

# From a file
python main.py tailor --jd path/to/job_description.txt
```

### 4. Run the web UI

```bash
# Start the API server
python -m uvicorn api:app --reload

# In another terminal, start the frontend
cd frontend && npm install && npm run dev
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `python main.py tailor --jd <url/file>` | Tailor resume for a specific job |
| `python main.py tailor --text "..."` | Tailor resume from pasted text |
| `python main.py scrape` | Scrape new job listings (all sources) |
| `python main.py scrape --source linkedin` | Scrape from a specific source |
| `python main.py batch` | Scrape + auto-tailor for all new matches |
| `python main.py board --url <url>` | Scrape a Greenhouse/Lever company board |
| `python main.py dashboard` | View application tracker dashboard |
| `python main.py followups` | View pending follow-ups |

## Project Structure

```
jobpilot/
├── config/
│   ├── master_profile.example.json  # Example profile (copy and fill in yours)
│   ├── settings.yaml                # Configuration (job titles, scrapers, output)
│   └── template_reference.tex       # LaTeX resume template
├── engine/
│   ├── jd_parser.py                 # Parse job descriptions via Claude API
│   ├── resume_tailor.py             # AI resume tailoring engine
│   ├── cover_letter_gen.py          # Cover letter generation
│   └── ats_optimizer.py             # ATS keyword scoring
├── output/
│   ├── latex_generator.py           # LaTeX/PDF resume generation
│   ├── pdf_generator.py             # Direct PDF generation
│   └── docx_generator.py            # DOCX resume generation
├── scrapers/
│   ├── linkedin_scraper.py          # LinkedIn job scraper
│   ├── indeed_scraper.py            # Indeed job scraper
│   └── greenhouse_lever.py          # Greenhouse/Lever board scraper
├── tracker/
│   └── application_tracker.py       # JSON-based application tracker
├── frontend/                        # React web UI
├── api.py                           # FastAPI REST backend
├── main.py                          # CLI entry point
└── requirements.txt
```

## Configuration

### Profile (`config/master_profile.json`)

Your career data including education, work experience, research, projects, skills, and certifications. This is the source of truth that the AI tailoring engine selects from.

### Settings (`config/settings.yaml`)

- Target job titles and locations
- Max experiences/bullets per resume section
- Scraper settings (sources, result limits)
- ATS keyword match thresholds
- Output format preferences

## Tech Stack

- **Backend**: Python, FastAPI, Anthropic Claude API
- **Frontend**: React, Vite
- **Resume Output**: LaTeX, ReportLab (PDF), python-docx
- **Scraping**: BeautifulSoup, Requests
- **Deployment**: Docker, Docker Compose

## License

MIT
