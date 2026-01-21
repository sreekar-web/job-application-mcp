from mcp.server.fastmcp import FastMCP
from docx import Document
import os
import csv
import json
from datetime import datetime

# -------------------------
# Base paths
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESUME_DIR = os.path.join(BASE_DIR, "resumes")
JOBS_FILE = os.path.join(BASE_DIR, "jobs", "jobs.json")

DECISIONS_DIR = os.path.join(BASE_DIR, "decisions")
DECISIONS_FILE = os.path.join(DECISIONS_DIR, "job_decisions.json")

ALLOWED_LOCATIONS = ["usa", "united states", "india", "remote - usa", "remote usa"]

mcp = FastMCP("Job Application MCP")

# -------------------------
# Resume Discovery
# -------------------------

@mcp.tool()
def list_resumes():
    """List available resumes (without extensions)."""
    if not os.path.exists(RESUME_DIR):
        return []

    names = set()
    for file in os.listdir(RESUME_DIR):
        if file.endswith(".txt") or file.endswith(".docx"):
            names.add(os.path.splitext(file)[0])

    return sorted(names)

# -------------------------
# Resume Reading
# -------------------------

@mcp.tool()
def read_resume(resume_name: str):
    """Read a resume by name (.txt or .docx)."""
    base_path = os.path.join(RESUME_DIR, resume_name)

    txt_path = base_path + ".txt"
    docx_path = base_path + ".docx"

    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()

    if os.path.exists(docx_path):
        doc = Document(docx_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return f"Resume '{resume_name}' not found."

# -------------------------
# Job Analysis
# -------------------------

@mcp.tool()
def analyze_job(job_description: str):
    return {
        "instruction_for_ai": (
            "Analyze the job description and decide which resume "
            "from list_resumes() is the best fit."
        ),
        "job_description": job_description
    }

# -------------------------
# Resume Tailoring
# -------------------------

@mcp.tool()
def tailor_resume(resume_name: str, job_description: str):
    resume = read_resume(resume_name)

    return {
        "instruction_for_ai": (
            "Using ONLY the provided resume content, "
            "rewrite or prioritize bullets to best match the job description. "
            "Do NOT add new experience or skills."
        ),
        "resume": resume,
        "job_description": job_description
    }

# -------------------------
# Application Strategy
# -------------------------

@mcp.tool()
def application_strategy(job_description: str):
    return {
        "steps_for_ai": [
            "Call list_resumes()",
            "Analyze the job description",
            "Choose ONE resume",
            "Call read_resume(resume_name)",
            "Call tailor_resume(resume_name, job_description)",
            "Generate resume bullets and cover letter"
        ],
        "rules": [
            "Use only ONE resume",
            "Do not invent experience",
            "Do not mix resumes"
        ],
        "job_description": job_description
    }

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
# Log Application
# -------------------------

@mcp.tool()
def log_application(
    company: str,
    role: str,
    resume_name: str,
    status: str = "Applied",
    notes: str = ""
):
    with open(os.path.join(BASE_DIR, "applications.csv"), "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
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
# Follow-up Email
# -------------------------

@mcp.tool()
def generate_follow_up_email(
    company: str,
    role: str,
    days_since_application: int
):
    return {
        "instruction_for_ai": (
            "Write a short, professional follow-up email. "
            "Be polite and confident. "
            "Do not sound desperate."
        ),
        "company": company,
        "role": role,
        "days_since_application": days_since_application
    }

# -------------------------
# Load Jobs
# -------------------------

@mcp.tool()
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {"error": f"jobs.json not found at {JOBS_FILE}"}

    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------
# Evaluate Single Job
# -------------------------

@mcp.tool()
def evaluate_job(job: dict):
    location = (job.get("location") or "").lower()

    if not any(loc in location for loc in ALLOWED_LOCATIONS):
        return {
            "decision": "SKIP",
            "reason": "Job location is outside allowed regions (USA / India)"
        }

    return {
        "instruction_for_ai": (
            "Evaluate this job against available resumes. "
            "Decide APPLY, SAVE, or SKIP. "
            "Choose ONE resume if APPLY or SAVE. "
            "Do not invent experience."
        ),
        "job": job
    }

# -------------------------
# Evaluate All Jobs → decisions/job_decisions.json
# -------------------------

@mcp.tool()
def evaluate_all_jobs():
    if not os.path.exists(JOBS_FILE):
        return {"error": "jobs.json not found"}

    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    os.makedirs(DECISIONS_DIR, exist_ok=True)

    decisions = []

    for job in jobs:
        decisions.append({
            "job_id": job.get("id"),
            "company": job.get("company"),
            "role": job.get("title"),
            "location": job.get("location"),
            "apply_url": job.get("apply_url"),
            "status": "PENDING_AI_REVIEW"
        })

    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(decisions, f, indent=2)

    return {
        "message": "Job decisions file created",
        "jobs_processed": len(decisions),
        "output_file": DECISIONS_FILE
    }

# -------------------------
# Server Start
# -------------------------

if __name__ == "__main__":
    mcp.run()
