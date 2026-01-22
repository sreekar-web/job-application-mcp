import json
from pathlib import Path
from datetime import datetime

CLASSIFIED_JOBS = Path("data/jobs_classified.json")
ROLE_VARIANTS_DIR = Path("resumes/role_variants")
DECISIONS_DIR = Path("decisions")
DECISIONS_FILE = DECISIONS_DIR / "decisions.json"
LOG_FILE = DECISIONS_DIR / "decisions.log"

DECISIONS_DIR.mkdir(exist_ok=True)

jobs = json.loads(CLASSIFIED_JOBS.read_text(encoding="utf-8"))

# Load role variants
role_variants = {}
for rv_file in ROLE_VARIANTS_DIR.glob("*.json"):
    role_variants[rv_file.stem] = json.loads(rv_file.read_text())

decisions = []

def log(line: str):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

for job in jobs:
    role_family = job["role_family"]
    rules = role_variants.get(role_family, {})

    # --- Scoring ---
    skill_hits = job.get("match_score", 0)
    skill_score = min(skill_hits * 15, 60)  # cap at 60

    role_text = str(job.get("role") or "").lower()
    role_confidence = 20 if role_family.replace("_", " ") in role_text else 10

    description_length = len(str(job.get("job_description") or ""))
    description_score = 20 if description_length > 800 else 10 if description_length > 300 else 0

    final_score = skill_score + role_confidence + description_score

    decision = "APPLY" if final_score >= 65 else "SKIP"

    reason_parts = []
    reason_parts.append(f"{skill_hits} key skills matched")
    reason_parts.append("clear role alignment" if role_confidence == 20 else "partial role alignment")
    reason_parts.append("detailed JD" if description_score == 20 else "limited JD detail")

    reason = "; ".join(reason_parts)

    evaluated_at = datetime.utcnow().isoformat() + "Z"

    decision_record = {
        "company": job.get("company"),
        "role": job.get("role"),
        "role_family": role_family,
        "resume_variant": job.get("resume_variant"),
        "match_score": skill_hits,
        "final_score": final_score,
        "decision": decision,
        "reason": reason,
        "apply_url": job.get("apply_url"),
        "evaluated_at": evaluated_at
    }

    decisions.append(decision_record)

    log(f"[{evaluated_at}] {decision} | {job.get('company')} | {job.get('role')} | Score: {final_score}")
    log(f"Reason: {reason}\n")

DECISIONS_FILE.write_text(json.dumps(decisions, indent=2))
print(f"✅ Evaluated {len(decisions)} jobs → {DECISIONS_FILE}")
