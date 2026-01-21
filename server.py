import os
import json
import csv
from datetime import datetime
from pathlib import Path
from docx import Document

from mcp.server.fastmcp import FastMCP

# -------------------------
# Paths
# -------------------------

BASE_DIR = Path(__file__).parent

RESUME_DIR = BASE_DIR / "resumes"
JOBS_FILE = BASE_DIR / "jobs" / "jobs.json"
DECISIONS_FILE = BASE_DIR / "decisions" / "job_decisions.json"
APPLICATIONS_FILE = BASE_DIR / "applications.csv"

# -------------------------
# MCP Init
# -------------------------

mcp = FastMCP("Job Application MCP")

# -------------------------
# Resume Discovery
# -------------------------

@mcp.tool()
def list_resumes():
    """
    List available resumes (without extensions)
    """
    if not RESUME_DIR.exists():
        return []

    names = set()
    for file in os.listdir(RESUME_DIR):
        if file.endswith(".txt") or file.endswith(".docx"):
            names.add(os.path.splitext(file)[0])

    return sorted(list(names))


# -------------------------
# Resume Reading
# -------------------------

@mcp.tool()
def read_resume(resume_name: str):
    """
    Read a resume by name (supports .txt and .docx)
    """
    base_path = RESUME_DIR / resume_name

    txt_path = base_path.with_suffix(".txt")
    docx_path = base_path.with_suffix(".docx")

    if txt_path.exists():
        return txt_path.read_text(encoding="utf-8")

    if docx_path.exists():
        doc = Document(docx_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return f"Resume '{resume_name}' not found."


# -------------------------
# Job Evaluation (single job)
# -------------------------

@mcp.tool()
def evaluate_job(payload: dict):
    """
    Claude-facing evaluation tool.
    Claude MUST return JSON:
    {
      "decision": "APPLY | SAVE | SKIP",
      "resume": "resume_name_or_null",
      "reason": "short justification"
    }
    """
    return payload


# -------------------------
# Evaluate ALL jobs (PERSISTENT)
# -------------------------

@mcp.tool()
def evaluate_all_jobs():
    """
    Evaluate all jobs and persist decisions to decisions/job_decisions.json
    """

    if not JOBS_FILE.exists():
        return "jobs.json not found. Run collect_jobs.py first."

    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    resumes = list_resumes()
    results = []

    for job in jobs:
        location_raw = (job.get("location") or "").lower()

        # Location filter: USA + India only
        allowed = any(
            kw in location_raw
            for kw in ["united states", "usa", "india"]
        )

        if not allowed:
            results.append({
                **job,
                "decision": "SKIP",
                "resume": None,
                "reason": "Location not in USA or India"
            })
            continue

        # Ask Claude to decide
        ai_request = {
            "instruction": (
                "You are an ATS-style evaluator.\n"
                "Return ONLY valid JSON with this schema:\n"
                "{"
                "\"decision\": \"APPLY | SAVE | SKIP\", "
                "\"resume\": \"resume_name_or_null\", "
                "\"reason\": \"short justification\""
                "}\n\n"
                "Rules:\n"
                "- APPLY only for strong matches\n"
                "- SAVE for partial matches\n"
                "- SKIP for weak or senior mismatch\n"
                "- Resume must come from the provided list\n"
                "- Do NOT invent experience"
            ),
            "job": job,
            "available_resumes": resumes
        }

        response = evaluate_job(ai_request)

        # Defensive parsing
        decision = response.get("decision", "SKIP")
        resume = response.get("resume")
        reason = response.get("reason", "No reason provided")

        results.append({
            **job,
            "decision": decision,
            "resume": resume,
            "reason": reason
        })

    # Persist results
    DECISIONS_FILE.parent.mkdir(exist_ok=True)
    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return f"Evaluated {len(results)} jobs. Decisions saved to {DECISIONS_FILE}"


# -------------------------
# Application Logging
# -------------------------

@mcp.tool()
def log_application(
    company: str,
    role: str,
    resume_name: str,
    status: str = "Applied",
    notes: str = ""
):
    """
    Log a job application to applications.csv
    """
    write_header = not APPLICATIONS_FILE.exists()

    with open(APPLICATIONS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if write_header:
            writer.writerow([
                "date", "company", "role",
                "resume", "status", "notes"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d"),
            company,
            role,
            resume_name,
            status,
            notes
        ])

    return "Application logged successfully."


# -------------------------
# Cover Letter
# -------------------------

@mcp.tool()
def generate_cover_letter(
    resume_name: str,
    company: str,
    role: str,
    job_description: str
):
    resume = read_resume(resume_name)

    return {
        "instruction_for_ai": (
            "Write a concise, professional cover letter using ONLY the resume content. "
            "Align experience with the job description. "
            "Do not invent experience."
        ),
        "company": company,
        "role": role,
        "resume": resume,
        "job_description": job_description
    }


# -------------------------
# Server Start
# -------------------------

if __name__ == "__main__":
    mcp.run()
