"""
Indeed Job Scraper
Scrapes job listings from Indeed's public search.
"""

import time
import random
from dataclasses import asdict
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from scrapers.linkedin_scraper import JobListing, HEADERS


def scrape_indeed_jobs(
    query: str = "AI Engineer",
    location: str = "United States",
    max_results: int = 25
) -> list[JobListing]:
    """Scrape Indeed public job listings."""
    jobs = []

    for start in range(0, max_results, 10):
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(location)

        url = (
            f"https://www.indeed.com/jobs"
            f"?q={encoded_query}"
            f"&l={encoded_location}"
            f"&fromage=7"  # Past week
            f"&start={start}"
        )

        try:
            time.sleep(random.uniform(2, 5))
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code != 200:
                print(f"Indeed returned {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            # Indeed job cards
            cards = soup.find_all("div", class_="job_seen_beacon")
            if not cards:
                cards = soup.find_all("div", {"class": lambda x: x and "cardOutline" in x})
            if not cards:
                # Try alternative selectors
                cards = soup.find_all("td", {"class": "resultContent"})

            for card in cards:
                job = JobListing(source="indeed")

                # Title
                title_elem = card.find("h2", class_="jobTitle")
                if not title_elem:
                    title_elem = card.find("a", {"class": lambda x: x and "Title" in str(x)})
                if title_elem:
                    job.title = title_elem.get_text(strip=True)
                    link = title_elem.find("a")
                    if link:
                        href = link.get("href", "")
                        if href.startswith("/"):
                            job.url = f"https://www.indeed.com{href}"
                        else:
                            job.url = href
                        # Extract job ID
                        if "jk=" in job.url:
                            job.job_id = job.url.split("jk=")[-1].split("&")[0]

                # Company
                company_elem = card.find("span", {"data-testid": "company-name"})
                if not company_elem:
                    company_elem = card.find("span", class_="companyName")
                if company_elem:
                    job.company = company_elem.get_text(strip=True)

                # Location
                loc_elem = card.find("div", {"data-testid": "text-location"})
                if not loc_elem:
                    loc_elem = card.find("div", class_="companyLocation")
                if loc_elem:
                    job.location = loc_elem.get_text(strip=True)

                if job.title and job.company:
                    jobs.append(job)

                if len(jobs) >= max_results:
                    break

        except Exception as e:
            print(f"Indeed scraping error: {e}")
            break

        if len(jobs) >= max_results:
            break

    return jobs[:max_results]


def fetch_indeed_description(job: JobListing) -> str:
    """Fetch full job description from Indeed."""
    if not job.url:
        return ""

    try:
        time.sleep(random.uniform(1, 3))
        resp = requests.get(job.url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        desc = soup.find("div", id="jobDescriptionText")
        if not desc:
            desc = soup.find("div", {"class": lambda x: x and "Description" in str(x)})

        if desc:
            job.description = desc.get_text(separator="\n", strip=True)
            return job.description

    except Exception as e:
        print(f"Error fetching Indeed JD: {e}")

    return ""


if __name__ == "__main__":
    print("Searching Indeed for AI Engineer jobs...")
    results = scrape_indeed_jobs("AI ML Engineer", "United States", max_results=5)
    for j in results:
        print(f"\n{j.title} @ {j.company} ({j.location})")
        print(f"  URL: {j.url}")
