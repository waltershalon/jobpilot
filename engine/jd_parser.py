"""
Job Description Parser
Extracts structured requirements from job postings using Claude API.
Accepts raw text or URLs.
"""

import json
import re
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

import anthropic
import requests
from bs4 import BeautifulSoup


@dataclass
class ParsedJD:
    """Structured representation of a job description."""
    title: str = ""
    company: str = ""
    location: str = ""
    remote_policy: str = ""  # remote, hybrid, onsite
    seniority: str = ""  # junior, mid, senior, staff
    salary_range: str = ""
    required_skills: list = field(default_factory=list)
    preferred_skills: list = field(default_factory=list)
    tech_stack: list = field(default_factory=list)
    responsibilities: list = field(default_factory=list)
    requirements: list = field(default_factory=list)
    keywords: list = field(default_factory=list)  # ATS keywords
    years_experience: str = ""
    education_req: str = ""
    industry: str = ""
    summary: str = ""
    raw_text: str = ""

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


def fetch_jd_from_url(url: str) -> str:
    """Fetch job description text from a URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script/style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Try common job description containers
        selectors = [
            ".job-description", ".description", "#job-description",
            "[data-testid='jobDescription']",  # LinkedIn
            ".posting-page",  # Lever
            "#content",  # Greenhouse
            "article", "main", ".content"
        ]
        for sel in selectors:
            container = soup.select_one(sel)
            if container and len(container.get_text(strip=True)) > 200:
                return container.get_text(separator="\n", strip=True)

        # Fallback: get body text
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)[:8000]

        return soup.get_text(separator="\n", strip=True)[:8000]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch JD from URL: {e}")


def parse_jd(text: str = None, url: str = None, api_key: str = None) -> ParsedJD:
    """
    Parse a job description into structured data.
    Provide either text or url.
    """
    if not text and not url:
        raise ValueError("Provide either text or url")

    if url and not text:
        text = fetch_jd_from_url(url)

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY environment variable or pass api_key")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Analyze this job description and extract structured information.
Return ONLY a valid JSON object with these fields:

{{
  "title": "exact job title",
  "company": "company name",
  "location": "location",
  "remote_policy": "remote|hybrid|onsite|unclear",
  "seniority": "junior|mid|senior|staff|unclear",
  "salary_range": "if mentioned, else empty string",
  "required_skills": ["list of explicitly required skills"],
  "preferred_skills": ["list of nice-to-have/preferred skills"],
  "tech_stack": ["specific technologies, frameworks, tools mentioned"],
  "responsibilities": ["key job responsibilities, max 5"],
  "requirements": ["key requirements like education, years experience"],
  "keywords": ["important ATS keywords - technical terms, tools, methodologies that should appear in a resume"],
  "years_experience": "years of experience required or preferred",
  "education_req": "education requirements",
  "industry": "industry/domain (e.g., healthcare, fintech, etc.)",
  "summary": "2-3 sentence summary of what this role actually involves"
}}

JOB DESCRIPTION:
{text[:6000]}"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text

    # Extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        raise ValueError("Failed to parse JD - no JSON in response")

    data = json.loads(json_match.group())

    parsed = ParsedJD(raw_text=text)
    for key, value in data.items():
        if hasattr(parsed, key):
            setattr(parsed, key, value)

    return parsed


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python jd_parser.py <url_or_text_file>")
        sys.exit(1)

    input_arg = sys.argv[1]
    if input_arg.startswith("http"):
        result = parse_jd(url=input_arg)
    else:
        with open(input_arg) as f:
            result = parse_jd(text=f.read())

    print(result.to_json())
