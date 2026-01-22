import json
from pathlib import Path
from job_scrapers.greenhouse import fetch_greenhouse_jobs
from job_scrapers.lever import fetch_lever_jobs

COMPANIES = {
    "greenhouse": ["airbnb", "stripe"],
    "lever": ["netflix", "spotify"]
}

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = DATA_DIR / "jobs_raw.json"


def collect_all_jobs():
    all_jobs = []

    for company in COMPANIES.get("greenhouse", []):
        try:
            jobs = fetch_greenhouse_jobs(company)
            all_jobs.extend(jobs)
            print(f"[OK] Greenhouse: {company} ({len(jobs)} jobs)")
        except Exception as e:
            print(f"[ERROR] Greenhouse failed for {company}: {e}")

    for company in COMPANIES.get("lever", []):
        try:
            jobs = fetch_lever_jobs(company)
            all_jobs.extend(jobs)
            print(f"[OK] Lever: {company} ({len(jobs)} jobs)")
        except Exception as e:
            print(f"[ERROR] Lever failed for {company}: {e}")

    return all_jobs


if __name__ == "__main__":
    jobs = collect_all_jobs()

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)

    print(f"\n✅ Collected {len(jobs)} total jobs → {OUTPUT_FILE}")
