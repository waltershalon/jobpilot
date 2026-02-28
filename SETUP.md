# JobPilot - Setup & Usage

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your API key
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Tailor a resume for a specific job
```bash
# From a URL:
python main.py tailor --jd "https://boards.greenhouse.io/company/jobs/12345"

# From pasted text:
python main.py tailor --text "We are looking for an ML Engineer..."

# From a file:
python main.py tailor --jd path/to/job_description.txt
```

### 4. Scrape job listings
```bash
python main.py scrape                    # All sources
python main.py scrape --source linkedin  # LinkedIn only
python main.py scrape --source indeed    # Indeed only
```

### 5. Scrape a specific company board
```bash
python main.py board --url "https://boards.greenhouse.io/openai"
python main.py board --url "https://jobs.lever.co/anthropic" --filter "ML,AI,Engineer"
```

### 6. Batch: scrape + auto-tailor
```bash
python main.py batch  # Scrapes new jobs, then generates tailored resumes for matches
```

### 7. Track your applications
```bash
python main.py dashboard   # See all applications
python main.py followups   # See pending follow-ups
```

## Output
Tailored resumes, cover letters, and JSON data are saved to `generated_resumes/`.

## Configuration
Edit `config/settings.yaml` to change:
- Target job titles and locations
- Max experiences/bullets per resume
- Scraper settings
- ATS score thresholds

Edit `config/master_profile.json` to update your experience data.

## Project Structure
```
jobpilot/
├── config/
│   ├── master_profile.json    # Your career data (source of truth)
│   └── settings.yaml          # Configuration
├── engine/
│   ├── jd_parser.py           # Parse job descriptions (Claude API)
│   ├── resume_tailor.py       # Tailor resume to JD (Claude API)
│   ├── cover_letter_gen.py    # Generate cover letters (Claude API)
│   └── ats_optimizer.py       # ATS keyword scoring
├── output/
│   ├── pdf_generator.py       # Generate PDF resumes
│   └── docx_generator.py      # Generate DOCX resumes
├── scrapers/
│   ├── linkedin_scraper.py    # LinkedIn job scraper
│   ├── indeed_scraper.py      # Indeed job scraper
│   └── greenhouse_lever.py    # Greenhouse/Lever board scraper
├── tracker/
│   └── application_tracker.py # JSON-based application tracker
├── generated_resumes/         # Output directory
├── main.py                    # CLI entry point
└── requirements.txt
```
