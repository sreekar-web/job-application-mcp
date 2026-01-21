import json
from pathlib import Path

JOBS_FILE = Path("jobs/jobs.json")
DECISIONS_FILE = Path("decisions/job_decisions.json")

def load_jobs():
    return json.loads(JOBS_FILE.read_text(encoding="utf-8"))

def save_decisions(decisions):
    DECISIONS_FILE.parent.mkdir(exist_ok=True)
    DECISIONS_FILE.write_text(
        json.dumps(decisions, indent=2),
        encoding="utf-8"
    )

if __name__ == "__main__":
    jobs = load_jobs()
    print(f"Loaded {len(jobs)} jobs")

    decisions = []

    for job in jobs:
        # Placeholder for MCP decision
        decisions.append({
            "company": job.get("company"),
            "role": job.get("role"),
            "decision": "PENDING",
            "recommended_resume": None,
            "apply_url": job.get("apply_url")
        })

    save_decisions(decisions)
    print("Job decision placeholders written")
