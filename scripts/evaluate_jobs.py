import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

CLASSIFIED_JOBS = Path("data/jobs_classified.json")
ROLE_VARIANTS_DIR = Path("resumes/role_variants")
DECISIONS_DIR = Path("decisions")
DECISIONS_FILE = DECISIONS_DIR / "decisions.json"
LOG_FILE = DECISIONS_DIR / "decisions.log"

DECISIONS_DIR.mkdir(exist_ok=True)

# ===========================
# Data Models
# ===========================

@dataclass
class ScoredJob:
    """Represents a job with computed scores and keyword matches."""
    company: str
    role: str
    location: str
    role_family: str
    match_score: int  # Raw count of matched allowed_skills
    matched_skills: List[str]  # Which allowed_skills were found
    primary_skill_hits: List[str]  # Which primary_focus skills were found
    skill_score: int
    role_confidence: int
    description_score: int
    final_score: int
    decision: str
    reason: str
    apply_url: str
    evaluated_at: str
    resume_variant: str = None

# ===========================
# Scoring Engine
# ===========================

def compute_matched_keywords(job_text: str, allowed_skills: List[str]) -> List[str]:
    """Extract which allowed_skills appear in the job description."""
    job_lower = job_text.lower()
    return [skill for skill in allowed_skills if skill.lower() in job_lower]

def compute_primary_focus_hits(job_text: str, primary_focus: List[str]) -> List[str]:
    """Extract which primary_focus skills appear in the job description."""
    job_lower = job_text.lower()
    return [skill for skill in primary_focus if skill.lower() in job_lower]

def score_job(job: Dict[str, Any], role_variant: Dict[str, Any]) -> ScoredJob:
    """
    Compute comprehensive job score with detailed keyword breakdown.
    
    Scoring formula:
    - skill_score: min(matched_skills_count * 15, 60) [weight: 60% of max]
    - role_confidence: 20 if role_family in role text, else 10 [weight: 20% of max]
    - description_score: 20 if JD > 800 chars, 10 if > 300, else 0 [weight: 20% of max]
    
    Decision: APPLY if final_score >= 65, SKIP otherwise
    """
    role_family = job["role_family"]
    role_text = str(job.get("role") or "").lower()
    description_text = str(job.get("job_description") or "")
    description_lower = description_text.lower()
    
    # --- Keyword Matching ---
    allowed_skills = role_variant.get("allowed_skills", [])
    primary_focus = role_variant.get("primary_focus", [])
    
    matched_skills = compute_matched_keywords(description_lower, allowed_skills)
    primary_skill_hits = compute_primary_focus_hits(description_lower, primary_focus)
    
    match_count = len(matched_skills)
    
    # --- Scoring ---
    skill_score = min(match_count * 15, 60)  # Cap at 60
    
    # Role confidence: +20 if role_family name appears in role text, +10 otherwise
    role_confidence = 20 if role_family.replace("_", " ") in role_text else 10
    
    # Description quality: +20 if detailed (800+ chars), +10 if moderate (300+), +0 if sparse
    description_length = len(description_text)
    description_score = 20 if description_length > 800 else 10 if description_length > 300 else 0
    
    final_score = skill_score + role_confidence + description_score
    
    # --- Decision ---
    decision = "APPLY" if final_score >= 65 else "SKIP"
    
    # --- Detailed Reason ---
    reason_parts = [
        f"{match_count}/{len(allowed_skills)} skills matched",
        f"{len(primary_skill_hits)} primary skills",
        "clear role alignment" if role_confidence == 20 else "partial role alignment",
        "detailed JD" if description_score == 20 else "moderate JD" if description_score == 10 else "sparse JD"
    ]
    reason = "; ".join(reason_parts)
    
    evaluated_at = datetime.utcnow().isoformat() + "Z"
    
    return ScoredJob(
        company=job.get("company"),
        role=job.get("role"),
        location=job.get("location"),
        role_family=role_family,
        match_score=match_count,
        matched_skills=matched_skills,
        primary_skill_hits=primary_skill_hits,
        skill_score=skill_score,
        role_confidence=role_confidence,
        description_score=description_score,
        final_score=final_score,
        decision=decision,
        reason=reason,
        apply_url=job.get("apply_url"),
        evaluated_at=evaluated_at,
        resume_variant=job.get("resume_variant", role_family)
    )

# ===========================
# Pipeline
# ===========================

def main():
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
        
        if not rules:
            # Fallback if variant missing
            log(f"[{datetime.utcnow().isoformat()}Z] ERROR | {job.get('company')} | {job.get('role')} | Missing role variant: {role_family}\n")
            continue
        
        # Score the job
        scored = score_job(job, rules)
        
        # Convert to dict for JSON serialization
        decision_record = asdict(scored)
        decisions.append(decision_record)
        
        # Log to file
        log(f"[{scored.evaluated_at}] {scored.decision} | {scored.company} | {scored.role} | Score: {scored.final_score}")
        log(f"  Matched skills: {', '.join(scored.matched_skills) if scored.matched_skills else 'none'}")
        log(f"  Primary focus hits: {', '.join(scored.primary_skill_hits) if scored.primary_skill_hits else 'none'}")
        log(f"  Reason: {scored.reason}\n")
    
    # Persist decisions
    DECISIONS_FILE.write_text(json.dumps(decisions, indent=2))
    print(f"✅ Evaluated {len(decisions)} jobs → {DECISIONS_FILE}")
    print(f"📋 Logs written to {LOG_FILE}")

if __name__ == "__main__":
    main()
