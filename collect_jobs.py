import json
from job_scrapers.greenhouse import fetch_greenhouse_jobs
from job_scrapers.lever import fetch_lever_jobs

COMPANIES = {
    "greenhouse": ["airbnb", "stripe"],
    "lever": ["netflix", "spotify"]
}

def collect_all_jobs():
    all_jobs = []

    for company in COMPANIES["greenhouse"]:
        all_jobs.extend(fetch_greenhouse_jobs(company))

    for company in COMPANIES["lever"]:
        all_jobs.extend(fetch_lever_jobs(company))

    return all_jobs

if __name__ == "__main__":
    jobs = collect_all_jobs()

    with open("jobs/jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)

    print(f"Collected {len(jobs)} jobs")
