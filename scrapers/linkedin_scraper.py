"""
LinkedIn Job Scraper
Uses LinkedIn's public job search (no login required, read-only, safe).
Falls back to Google search if LinkedIn blocks direct access.
"""

import time
import random
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


@dataclass
class JobListing:
    """Represents a scraped job posting."""
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    date_posted: str = ""
    source: str = "linkedin"
    job_id: str = ""

    def to_dict(self):
        return asdict(self)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_linkedin_jobs(
    query: str = "AI Engineer",
    location: str = "United States",
    max_results: int = 25,
    experience_level: str = None
) -> list[JobListing]:
    """
    Scrape LinkedIn public job listings (no login).
    Uses LinkedIn's guest job search API.
    """
    jobs = []
    encoded_query = quote_plus(query)
    encoded_location = quote_plus(location)

    # LinkedIn public job search URL
    # f_E=3,4 = mid-senior level, f_TPR=r604800 = past week
    exp_filter = ""
    if experience_level == "mid":
        exp_filter = "&f_E=3,4"
    elif experience_level == "senior":
        exp_filter = "&f_E=4,5"

    for start in range(0, max_results, 25):
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={encoded_query}"
            f"&location={encoded_location}"
            f"&f_TPR=r604800"  # past week
            f"{exp_filter}"
            f"&start={start}"
        )

        try:
            time.sleep(random.uniform(2, 5))  # Be respectful
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code != 200:
                print(f"LinkedIn returned {resp.status_code}, trying alternative method...")
                jobs.extend(_scrape_via_google(query, location, max_results))
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            # LinkedIn public job cards
            cards = soup.find_all("div", class_="base-card")
            if not cards:
                cards = soup.find_all("li", class_="result-card")

            if not cards:
                print("No job cards found. LinkedIn may have changed layout.")
                jobs.extend(_scrape_via_google(query, location, max_results - len(jobs)))
                break

            for card in cards:
                job = JobListing(source="linkedin")

                title_elem = card.find("h3", class_="base-search-card__title")
                if title_elem:
                    job.title = title_elem.get_text(strip=True)

                company_elem = card.find("h4", class_="base-search-card__subtitle")
                if company_elem:
                    job.company = company_elem.get_text(strip=True)

                loc_elem = card.find("span", class_="job-search-card__location")
                if loc_elem:
                    job.location = loc_elem.get_text(strip=True)

                link_elem = card.find("a", class_="base-card__full-link")
                if link_elem:
                    job.url = link_elem.get("href", "").split("?")[0]
                    # Extract job ID from URL
                    if "/view/" in job.url:
                        job.job_id = job.url.split("/view/")[-1].rstrip("/")

                date_elem = card.find("time")
                if date_elem:
                    job.date_posted = date_elem.get("datetime", "")

                if job.title and job.company:
                    jobs.append(job)

                if len(jobs) >= max_results:
                    break

        except Exception as e:
            print(f"LinkedIn scraping error: {e}")
            jobs.extend(_scrape_via_google(query, location, max_results - len(jobs)))
            break

        if len(jobs) >= max_results:
            break

    return jobs[:max_results]


def _scrape_via_google(query: str, location: str, max_results: int) -> list[JobListing]:
    """
    Fallback: search Google for LinkedIn job postings.
    """
    jobs = []
    search_query = f"site:linkedin.com/jobs/view {query} {location}"
    url = f"https://www.google.com/search?q={quote_plus(search_query)}&num={min(max_results, 20)}"

    try:
        time.sleep(random.uniform(1, 3))
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for result in soup.find_all("div", class_="g"):
            link = result.find("a")
            if not link or "linkedin.com/jobs" not in link.get("href", ""):
                continue

            job = JobListing(source="linkedin_via_google")
            job.url = link.get("href", "")

            title_elem = result.find("h3")
            if title_elem:
                text = title_elem.get_text(strip=True)
                # Parse "Title - Company | LinkedIn" format
                parts = text.replace(" | LinkedIn", "").split(" - ", 1)
                if len(parts) == 2:
                    job.title = parts[0].strip()
                    job.company = parts[1].strip()
                else:
                    job.title = text

            if job.title:
                jobs.append(job)

            if len(jobs) >= max_results:
                break

    except Exception as e:
        print(f"Google fallback error: {e}")

    return jobs


def fetch_job_description(job: JobListing) -> str:
    """Fetch the full job description for a listing."""
    if not job.url:
        return ""

    try:
        time.sleep(random.uniform(1, 3))
        resp = requests.get(job.url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        # LinkedIn job description containers
        desc = soup.find("div", class_="show-more-less-html__markup")
        if not desc:
            desc = soup.find("div", class_="description__text")
        if not desc:
            desc = soup.find("section", class_="description")

        if desc:
            job.description = desc.get_text(separator="\n", strip=True)
            return job.description

    except Exception as e:
        print(f"Error fetching JD: {e}")

    return ""


if __name__ == "__main__":
    print("Searching LinkedIn for AI Engineer jobs...")
    results = scrape_linkedin_jobs("AI ML Engineer", "United States", max_results=5)
    for j in results:
        print(f"\n{j.title} @ {j.company} ({j.location})")
        print(f"  URL: {j.url}")
