"""
Greenhouse & Lever Job Board Scraper
Scrapes jobs from company-specific Greenhouse and Lever boards.
These are the most automation-friendly ATS platforms.
"""

import time
import random
import json
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from scrapers.linkedin_scraper import JobListing, HEADERS


# Common healthcare AI / ML companies using Greenhouse or Lever
DEFAULT_BOARDS = {
    "greenhouse": [
        # Add company board URLs as you find them
        # Format: {"name": "Company", "url": "https://boards.greenhouse.io/company"}
    ],
    "lever": [
        # Format: {"name": "Company", "url": "https://jobs.lever.co/company"}
    ]
}


def scrape_greenhouse_board(board_url: str, company_name: str = "",
                            title_filter: str = None) -> list[JobListing]:
    """Scrape jobs from a Greenhouse board."""
    jobs = []

    try:
        # Greenhouse has a JSON API
        api_url = board_url.rstrip("/")
        if "boards.greenhouse.io" in api_url:
            company_slug = api_url.split("/")[-1]
            json_url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"

            resp = requests.get(json_url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for job_data in data.get("jobs", []):
                    title = job_data.get("title", "")

                    # Filter by title keywords if specified
                    if title_filter:
                        title_lower = title.lower()
                        filters = [f.lower() for f in title_filter.split(",")]
                        if not any(f in title_lower for f in filters):
                            continue

                    job = JobListing(
                        title=title,
                        company=company_name or company_slug,
                        location=job_data.get("location", {}).get("name", ""),
                        url=job_data.get("absolute_url", ""),
                        job_id=str(job_data.get("id", "")),
                        source="greenhouse"
                    )
                    jobs.append(job)

                return jobs

        # Fallback: HTML scraping
        time.sleep(random.uniform(1, 3))
        resp = requests.get(board_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for opening in soup.find_all("div", class_="opening"):
            job = JobListing(source="greenhouse")

            link = opening.find("a")
            if link:
                job.title = link.get_text(strip=True)
                href = link.get("href", "")
                job.url = href if href.startswith("http") else board_url.rstrip("/") + href

            loc = opening.find("span", class_="location")
            if loc:
                job.location = loc.get_text(strip=True)

            job.company = company_name

            if title_filter:
                title_lower = job.title.lower()
                filters = [f.lower() for f in title_filter.split(",")]
                if not any(f in title_lower for f in filters):
                    continue

            if job.title:
                jobs.append(job)

    except Exception as e:
        print(f"Greenhouse scraping error for {board_url}: {e}")

    return jobs


def scrape_lever_board(board_url: str, company_name: str = "",
                       title_filter: str = None) -> list[JobListing]:
    """Scrape jobs from a Lever board."""
    jobs = []

    try:
        # Lever also has a JSON API
        api_url = board_url.rstrip("/")
        if "jobs.lever.co" in api_url:
            company_slug = api_url.split("/")[-1].split("?")[0]
            json_url = f"https://api.lever.co/v0/postings/{company_slug}"

            resp = requests.get(json_url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for posting in data:
                    title = posting.get("text", "")

                    if title_filter:
                        title_lower = title.lower()
                        filters = [f.lower() for f in title_filter.split(",")]
                        if not any(f in title_lower for f in filters):
                            continue

                    categories = posting.get("categories", {})
                    job = JobListing(
                        title=title,
                        company=company_name or company_slug,
                        location=categories.get("location", ""),
                        url=posting.get("hostedUrl", ""),
                        job_id=posting.get("id", ""),
                        source="lever"
                    )
                    jobs.append(job)

                return jobs

        # Fallback: HTML
        time.sleep(random.uniform(1, 3))
        resp = requests.get(board_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for posting in soup.find_all("div", class_="posting"):
            job = JobListing(source="lever")

            title_elem = posting.find("h5")
            if title_elem:
                job.title = title_elem.get_text(strip=True)

            link = posting.find("a", class_="posting-title")
            if link:
                job.url = link.get("href", "")
                if not job.title:
                    job.title = link.get_text(strip=True)

            loc_elem = posting.find("span", class_="location")
            if loc_elem:
                job.location = loc_elem.get_text(strip=True)

            job.company = company_name

            if title_filter:
                title_lower = job.title.lower()
                filters = [f.lower() for f in title_filter.split(",")]
                if not any(f in title_lower for f in filters):
                    continue

            if job.title:
                jobs.append(job)

    except Exception as e:
        print(f"Lever scraping error for {board_url}: {e}")

    return jobs


def fetch_greenhouse_description(job: JobListing) -> str:
    """Fetch job description from Greenhouse."""
    if not job.url:
        return ""

    try:
        # Try JSON API first if we have job ID
        if job.job_id and "greenhouse" in job.source:
            api_url = f"https://boards-api.greenhouse.io/v1/boards/*/jobs/{job.job_id}"
            # We need the board name, try to extract from URL
            pass

        time.sleep(random.uniform(1, 2))
        resp = requests.get(job.url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        desc = soup.find("div", id="content")
        if not desc:
            desc = soup.find("div", class_="job-post")
        if desc:
            job.description = desc.get_text(separator="\n", strip=True)
            return job.description

    except Exception as e:
        print(f"Error fetching Greenhouse JD: {e}")

    return ""


def fetch_lever_description(job: JobListing) -> str:
    """Fetch job description from Lever."""
    if not job.url:
        return ""

    try:
        time.sleep(random.uniform(1, 2))
        resp = requests.get(job.url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        desc = soup.find("div", class_="posting-page")
        if not desc:
            desc = soup.find("div", {"class": lambda x: x and "description" in str(x).lower()})
        if desc:
            job.description = desc.get_text(separator="\n", strip=True)
            return job.description

    except Exception as e:
        print(f"Error fetching Lever JD: {e}")

    return ""


if __name__ == "__main__":
    print("Greenhouse/Lever scraper ready.")
    print("Add company board URLs to DEFAULT_BOARDS or pass them directly.")
    print("\nExample usage:")
    print('  scrape_greenhouse_board("https://boards.greenhouse.io/openai", "OpenAI", "ML,AI")')
    print('  scrape_lever_board("https://jobs.lever.co/anthropic", "Anthropic", "ML,AI")')
