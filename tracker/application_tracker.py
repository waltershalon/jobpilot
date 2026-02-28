"""
Application Tracker
JSON-based tracker for job applications.
Tracks: company, role, resume version, status, dates, notes.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import threading

TRACKER_PATH = os.path.join(os.path.dirname(__file__), "applications.json")
_lock = threading.Lock()


def _load_data(db_path: str = None) -> dict:
    """Load tracker data from JSON file."""
    path = db_path or TRACKER_PATH
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"next_id": 1, "applications": []}


def _save_data(data: dict, db_path: str = None):
    """Save tracker data to JSON file."""
    path = db_path or TRACKER_PATH
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def add_application(
    company: str,
    title: str,
    location: str = "",
    url: str = "",
    source: str = "",
    status: str = "discovered",
    resume_path: str = "",
    cover_letter_path: str = "",
    ats_score: float = 0.0,
    keywords_matched: list = None,
    keywords_missing: list = None,
    notes: str = "",
    db_path: str = None
) -> int:
    """Add a new application to the tracker. Returns the application ID."""
    with _lock:
        data = _load_data(db_path)
        now = datetime.now().isoformat()
        app_id = data["next_id"]
        data["next_id"] += 1

        app = {
            "id": app_id,
            "company": company,
            "title": title,
            "location": location,
            "url": url,
            "source": source,
            "status": status,
            "resume_path": resume_path,
            "cover_letter_path": cover_letter_path,
            "ats_score": ats_score,
            "keywords_matched": keywords_matched or [],
            "keywords_missing": keywords_missing or [],
            "notes": notes,
            "date_discovered": now,
            "date_applied": "",
            "date_response": "",
            "date_interview": "",
            "follow_up_date": "",
            "created_at": now,
            "updated_at": now
        }
        data["applications"].append(app)
        _save_data(data, db_path)
        return app_id


def update_status(app_id: int, status: str, notes: str = None, db_path: str = None):
    """Update application status."""
    with _lock:
        data = _load_data(db_path)
        now = datetime.now().isoformat()

        for app in data["applications"]:
            if app["id"] == app_id:
                app["status"] = status
                app["updated_at"] = now

                if status == "applied":
                    app["date_applied"] = now
                elif status == "response":
                    app["date_response"] = now
                elif status == "interview":
                    app["date_interview"] = now

                if notes:
                    existing = app.get("notes", "")
                    app["notes"] = f"{existing}\n[{now[:10]}] {notes}".strip()
                break

        _save_data(data, db_path)


def set_follow_up(app_id: int, days: int = 7, db_path: str = None):
    """Set a follow-up reminder."""
    with _lock:
        data = _load_data(db_path)
        follow_up = (datetime.now() + timedelta(days=days)).isoformat()

        for app in data["applications"]:
            if app["id"] == app_id:
                app["follow_up_date"] = follow_up
                app["updated_at"] = datetime.now().isoformat()
                break

        _save_data(data, db_path)


def get_applications(status: str = None, db_path: str = None) -> list[dict]:
    """Get all applications, optionally filtered by status."""
    data = _load_data(db_path)
    apps = data["applications"]
    if status:
        apps = [a for a in apps if a["status"] == status]
    return sorted(apps, key=lambda x: x.get("created_at", ""), reverse=True)


def get_follow_ups(db_path: str = None) -> list[dict]:
    """Get applications with pending follow-ups."""
    data = _load_data(db_path)
    now = datetime.now().isoformat()
    excluded = {"rejected", "withdrawn", "offer"}
    return [
        a for a in data["applications"]
        if a.get("follow_up_date") and a["follow_up_date"] <= now
        and a["status"] not in excluded
    ]


def check_duplicate(company: str, title: str, db_path: str = None) -> bool:
    """Check if we already have this application."""
    data = _load_data(db_path)
    return any(
        a["company"] == company and a["title"] == title
        for a in data["applications"]
    )


def get_stats(db_path: str = None) -> dict:
    """Get application statistics."""
    data = _load_data(db_path)
    apps = data["applications"]
    total = len(apps)

    by_status = {}
    for app in apps:
        s = app["status"]
        by_status[s] = by_status.get(s, 0) + 1

    scores = [a["ats_score"] for a in apps if a.get("ats_score", 0) > 0]
    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "total": total,
        "by_status": by_status,
        "avg_ats_score": round(avg_score, 2)
    }


def print_dashboard(db_path: str = None):
    """Print a dashboard summary."""
    stats = get_stats(db_path)
    apps = get_applications(db_path=db_path)
    follow_ups = get_follow_ups(db_path)

    print("\n" + "=" * 70)
    print("JOBPILOT APPLICATION DASHBOARD")
    print("=" * 70)

    print(f"\nTotal Applications: {stats['total']}")
    if stats['avg_ats_score']:
        print(f"Average ATS Score: {stats['avg_ats_score']:.0%}")
    print("\nBy Status:")
    for status, count in stats.get("by_status", {}).items():
        print(f"  {status}: {count}")

    if follow_ups:
        print(f"\nPending Follow-ups ({len(follow_ups)}):")
        for app in follow_ups:
            print(f"  - {app['title']} @ {app['company']} (applied: {app.get('date_applied', 'N/A')[:10]})")

    if apps:
        print("\nRecent Applications:")
        for app in apps[:10]:
            score_str = f"{app['ats_score']:.0%}" if app.get('ats_score') else "N/A"
            print(f"  [{app['status']:12s}] {app['title'][:30]:30s} @ {app['company'][:25]:25s} ATS: {score_str}")

    print("=" * 70)


if __name__ == "__main__":
    print_dashboard()
