#!/usr/bin/env python3
"""
JobPilot - Automated Job Application Pipeline
=============================================

Usage:
  python main.py tailor --jd <url_or_file>       Tailor resume for a specific job
  python main.py tailor --text "paste JD here"    Tailor resume from pasted text
  python main.py scrape                           Scrape new job listings
  python main.py scrape --source linkedin         Scrape from specific source
  python main.py batch                            Scrape + tailor for all new jobs
  python main.py dashboard                        Show application dashboard
  python main.py followups                        Show pending follow-ups
  python main.py board --url <board_url>          Scrape a specific Greenhouse/Lever board
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.jd_parser import parse_jd, fetch_jd_from_url, ParsedJD
from engine.resume_tailor import tailor_resume, TailoredResume
from engine.cover_letter_gen import generate_cover_letter
from engine.ats_optimizer import analyze_ats_coverage, print_ats_report
from output.latex_generator import generate_latex
from output.docx_generator import generate_docx
from scrapers.linkedin_scraper import scrape_linkedin_jobs, fetch_job_description
from scrapers.indeed_scraper import scrape_indeed_jobs, fetch_indeed_description
from scrapers.greenhouse_lever import (
    scrape_greenhouse_board, scrape_lever_board,
    fetch_greenhouse_description, fetch_lever_description
)
from tracker.application_tracker import (
    add_application, update_status, check_duplicate,
    print_dashboard, get_follow_ups, get_stats, set_follow_up
)


def load_settings():
    """Load settings from YAML config."""
    settings_path = PROJECT_ROOT / "config" / "settings.yaml"
    if settings_path.exists():
        with open(settings_path) as f:
            return yaml.safe_load(f)
    return {}


def ensure_output_dir():
    """Ensure output directory exists."""
    output_dir = PROJECT_ROOT / "generated_resumes"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def sanitize_filename(text: str) -> str:
    """Create a safe filename from text."""
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in text).strip()[:50]


def cmd_tailor(args):
    """Tailor resume for a specific job."""
    settings = load_settings()
    output_dir = ensure_output_dir()

    print("\n" + "=" * 60)
    print("JOBPILOT - Resume Tailoring Engine")
    print("=" * 60)

    # Get job description
    if args.jd:
        if args.jd.startswith("http"):
            print(f"\nFetching JD from: {args.jd}")
            parsed = parse_jd(url=args.jd)
        else:
            print(f"\nReading JD from file: {args.jd}")
            with open(args.jd) as f:
                parsed = parse_jd(text=f.read())
    elif args.text:
        print("\nParsing pasted JD...")
        parsed = parse_jd(text=args.text)
    else:
        print("Error: Provide --jd <url_or_file> or --text 'job description'")
        sys.exit(1)

    print(f"\nParsed Job: {parsed.title} @ {parsed.company}")
    print(f"Industry: {parsed.industry}")
    print(f"Seniority: {parsed.seniority}")
    print(f"Required Skills: {', '.join(parsed.required_skills[:10])}")
    print(f"Tech Stack: {', '.join(parsed.tech_stack[:10])}")

    # Check for duplicate
    if check_duplicate(parsed.company, parsed.title):
        print(f"\n⚠ You've already applied to {parsed.title} @ {parsed.company}")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            return

    # Tailor resume
    print("\nTailoring resume...")
    tailoring_config = settings.get("tailoring", {})
    tailored = tailor_resume(
        parsed,
        profile_path=str(PROJECT_ROOT / "config" / "master_profile.json"),
        max_work_exp=tailoring_config.get("max_experiences", 4),
        max_bullets=tailoring_config.get("max_bullets_per_exp", 4),
        max_projects=tailoring_config.get("max_projects", 2)
    )

    # ATS analysis
    ats = analyze_ats_coverage(tailored, parsed)
    print_ats_report(ats)

    # Generate output files
    timestamp = datetime.now().strftime("%Y%m%d")
    company_safe = sanitize_filename(parsed.company)
    title_safe = sanitize_filename(parsed.title)
    user_name = sanitize_filename(tailored.personal.get("name", "Candidate").replace(" ", "_"))
    base_name = f"{user_name}_{company_safe}_{title_safe}_{timestamp}"

    # Primary: LaTeX → PDF
    print(f"\nGenerating LaTeX resume...")
    latex_result = generate_latex(tailored, str(output_dir), base_name)
    pdf_path = output_dir / f"{base_name}.pdf"
    tex_path = output_dir / f"{base_name}.tex"
    print(f"  TEX: {tex_path.name}")
    if latex_result.get("pdf"):
        print(f"  PDF: {pdf_path.name} ({latex_result['pages']} page{'s' if latex_result['pages'] != 1 else ''})")
    else:
        print("  PDF compilation failed — .tex file still available")

    # Also generate DOCX as backup
    docx_path = output_dir / f"{base_name}.docx"
    print(f"Generating DOCX: {docx_path.name}")
    generate_docx(tailored, str(docx_path))

    # Generate cover letter
    print("Generating cover letter...")
    cover_letter = generate_cover_letter(parsed, tailored)
    cl_path = output_dir / f"{base_name}_cover_letter.txt"
    with open(cl_path, "w") as f:
        f.write(cover_letter)
    print(f"Cover letter: {cl_path.name}")

    # Save tailored JSON for reference
    json_path = output_dir / f"{base_name}_tailored.json"
    with open(json_path, "w") as f:
        f.write(tailored.to_json())

    # Track the application
    app_id = add_application(
        company=parsed.company,
        title=parsed.title,
        location=parsed.location,
        url=args.jd if args.jd and args.jd.startswith("http") else "",
        source="manual",
        status="resume_ready",
        resume_path=str(pdf_path),
        cover_letter_path=str(cl_path),
        ats_score=ats["overall_score"],
        keywords_matched=ats["matched_required"] + ats["matched_tech"],
        keywords_missing=ats["missing_required"] + ats["missing_tech"]
    )
    print(f"\nTracked as application #{app_id}")

    print(f"\n✓ All files saved to: {output_dir}/")
    print(f"  Resume (PDF):    {pdf_path.name}")
    print(f"  Resume (DOCX):   {docx_path.name}")
    print(f"  Cover Letter:    {cl_path.name}")
    print(f"  ATS Score:       {ats['overall_score']:.0%}")


def cmd_scrape(args):
    """Scrape new job listings."""
    settings = load_settings()
    search_config = settings.get("search", {})
    titles = search_config.get("titles", ["AI Engineer", "ML Engineer"])
    locations = search_config.get("locations", ["United States"])

    all_jobs = []
    source = getattr(args, 'source', 'all')

    for title in titles[:3]:  # Limit to top 3 titles to avoid rate limits
        for location in locations[:1]:  # Primary location
            print(f"\nSearching: {title} in {location}...")

            if source in ('all', 'linkedin'):
                print("  LinkedIn...", end=" ", flush=True)
                jobs = scrape_linkedin_jobs(title, location, max_results=10)
                all_jobs.extend(jobs)
                print(f"found {len(jobs)}")

            if source in ('all', 'indeed'):
                print("  Indeed...", end=" ", flush=True)
                jobs = scrape_indeed_jobs(title, location, max_results=10)
                all_jobs.extend(jobs)
                print(f"found {len(jobs)}")

    # Deduplicate by company+title
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.company.lower(), job.title.lower())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    # Track discovered jobs
    new_count = 0
    for job in unique_jobs:
        if not check_duplicate(job.company, job.title):
            add_application(
                company=job.company,
                title=job.title,
                location=job.location,
                url=job.url,
                source=job.source,
                status="discovered"
            )
            new_count += 1

    print(f"\n✓ Found {len(unique_jobs)} jobs, {new_count} new")
    print("\nNew discoveries:")
    for job in unique_jobs[:15]:
        print(f"  {job.title[:40]:40s} @ {job.company[:30]:30s} ({job.source})")


def cmd_batch(args):
    """Scrape + auto-tailor for all discovered jobs."""
    print("\nRunning batch pipeline...")

    # First scrape
    cmd_scrape(args)

    # Then tailor for discovered jobs
    from tracker.application_tracker import get_applications
    discovered = get_applications(status="discovered")

    if not discovered:
        print("\nNo new jobs to process.")
        return

    print(f"\nFound {len(discovered)} discovered jobs. Processing...")

    for app in discovered[:5]:  # Process top 5 at a time
        print(f"\n--- Processing: {app['title']} @ {app['company']} ---")

        try:
            # Get the full JD
            if app.get("url"):
                jd_text = fetch_jd_from_url(app["url"])
            else:
                print("  No URL, skipping...")
                continue

            if not jd_text or len(jd_text) < 100:
                print("  Could not fetch JD, skipping...")
                continue

            # Parse and tailor
            parsed = parse_jd(text=jd_text)
            tailored = tailor_resume(
                parsed,
                profile_path=str(PROJECT_ROOT / "config" / "master_profile.json")
            )

            ats = analyze_ats_coverage(tailored, parsed)

            # Only generate files if ATS score is decent
            if ats["overall_score"] >= 0.4:
                output_dir = ensure_output_dir()
                timestamp = datetime.now().strftime("%Y%m%d")
                company_safe = sanitize_filename(app["company"])
                title_safe = sanitize_filename(app["title"])
                user_name = sanitize_filename(tailored.personal.get("name", "Candidate").replace(" ", "_"))
                base_name = f"{user_name}_{company_safe}_{title_safe}_{timestamp}"

                latex_result = generate_latex(tailored, str(output_dir), base_name)

                docx_path = output_dir / f"{base_name}.docx"
                generate_docx(tailored, str(docx_path))

                cover_letter = generate_cover_letter(parsed, tailored)
                cl_path = output_dir / f"{base_name}_cover_letter.txt"
                with open(cl_path, "w") as f:
                    f.write(cover_letter)

                update_status(app["id"], "resume_ready",
                             f"ATS Score: {ats['overall_score']:.0%}")
                print(f"  ✓ ATS: {ats['overall_score']:.0%} - Resume generated")
            else:
                update_status(app["id"], "low_match",
                             f"ATS Score: {ats['overall_score']:.0%} - below threshold")
                print(f"  ✗ ATS: {ats['overall_score']:.0%} - below threshold, skipped")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    print("\n✓ Batch processing complete")


def cmd_board(args):
    """Scrape a specific Greenhouse/Lever board."""
    url = args.url
    title_filter = getattr(args, 'filter', 'AI,ML,Data,Engineer')

    if "greenhouse" in url:
        print(f"Scraping Greenhouse board: {url}")
        jobs = scrape_greenhouse_board(url, title_filter=title_filter)
    elif "lever" in url:
        print(f"Scraping Lever board: {url}")
        jobs = scrape_lever_board(url, title_filter=title_filter)
    else:
        print("URL must be a Greenhouse or Lever board URL")
        return

    print(f"\nFound {len(jobs)} matching jobs:")
    for job in jobs:
        print(f"  {job.title} ({job.location}) - {job.url}")

    # Track
    new_count = 0
    for job in jobs:
        if not check_duplicate(job.company, job.title):
            add_application(
                company=job.company, title=job.title,
                location=job.location, url=job.url, source=job.source,
                status="discovered"
            )
            new_count += 1
    print(f"\n{new_count} new jobs added to tracker")


def cmd_dashboard(args):
    """Show application dashboard."""
    print_dashboard()


def cmd_followups(args):
    """Show pending follow-ups."""
    follow_ups = get_follow_ups()
    if not follow_ups:
        print("\nNo pending follow-ups. Nice!")
        return

    print(f"\nPending Follow-ups ({len(follow_ups)}):")
    for app in follow_ups:
        days_since = ""
        if app.get("date_applied"):
            applied = datetime.fromisoformat(app["date_applied"])
            days = (datetime.now() - applied).days
            days_since = f" ({days} days ago)"
        print(f"  [{app['id']}] {app['title']} @ {app['company']}{days_since}")
        print(f"       URL: {app.get('url', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        description="JobPilot - Automated Job Application Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # tailor
    p_tailor = subparsers.add_parser("tailor", help="Tailor resume for a job")
    p_tailor.add_argument("--jd", help="Job description URL or file path")
    p_tailor.add_argument("--text", help="Paste job description text directly")
    p_tailor.set_defaults(func=cmd_tailor)

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Scrape new job listings")
    p_scrape.add_argument("--source", choices=["all", "linkedin", "indeed"],
                          default="all", help="Source to scrape")
    p_scrape.set_defaults(func=cmd_scrape)

    # batch
    p_batch = subparsers.add_parser("batch", help="Scrape + auto-tailor all new jobs")
    p_batch.add_argument("--source", choices=["all", "linkedin", "indeed"],
                         default="all")
    p_batch.set_defaults(func=cmd_batch)

    # board
    p_board = subparsers.add_parser("board", help="Scrape a Greenhouse/Lever board")
    p_board.add_argument("--url", required=True, help="Board URL")
    p_board.add_argument("--filter", default="AI,ML,Data,Engineer",
                         help="Title filter keywords (comma-separated)")
    p_board.set_defaults(func=cmd_board)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Show application dashboard")
    p_dash.set_defaults(func=cmd_dashboard)

    # followups
    p_follow = subparsers.add_parser("followups", help="Show pending follow-ups")
    p_follow.set_defaults(func=cmd_followups)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
