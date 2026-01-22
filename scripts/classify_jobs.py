import json
from pathlib import Path

RAW_JOBS = Path("data/jobs_raw.json")
ROLE_VARIANTS_DIR = Path("resumes/role_variants")
OUTPUT_FILE = Path("data/jobs_classified.json")

# Ensure data directory exists
OUTPUT_FILE.parent.mkdir(exist_ok=True)

jobs = json.loads(RAW_JOBS.read_text(encoding="utf-8"))

# Load role variants
role_variants = {}
for rv_file in ROLE_VARIANTS_DIR.glob("*.json"):
    role_variants[rv_file.stem] = json.loads(rv_file.read_text())

classified_jobs = []

for job in jobs:
    # Safely normalize text fields (None-safe)
    role_text = str(job.get("role") or "")
    description_text = str(job.get("job_description") or "")

    jd_text = f"{role_text} {description_text}".lower()

    best_match = None
    best_score = 0

    for role_family, rules in role_variants.items():
        hits = sum(
            1 for skill in rules["allowed_skills"]
            if skill.lower() in jd_text
        )

        if hits >= 2 and hits > best_score:
            best_match = role_family
            best_score = hits

    if not best_match:
        continue  # Discard irrelevant job

    job["role_family"] = best_match
    job["resume_variant"] = best_match
    job["match_score"] = best_score

    classified_jobs.append(job)

OUTPUT_FILE.write_text(json.dumps(classified_jobs, indent=2))
print(f"✅ Classified {len(classified_jobs)} relevant jobs → {OUTPUT_FILE}")
