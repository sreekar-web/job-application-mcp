import os
import json
import csv
import asyncio
from datetime import datetime
from pathlib import Path
from docx import Document

from mcp.server.fastmcp import FastMCP
from applications.browser_handler import BrowserHandler, ApplicationResult
from applications.application_autofill import ApplicationAutofiller
from applications.application_tracker import ApplicationTracker, ApplicationStatus
from applications.followup_manager import FollowupManager
from interviews.interview_prep import InterviewPrep, InterviewType, InterviewStatus
from interviews.email_automation import EmailAutomation
from interviews.interview_scheduler import InterviewScheduler
from interviews.coaching_materials import CoachingMaterials

# -------------------------
# Paths
# -------------------------

BASE_DIR = Path(__file__).parent

RESUME_DIR = BASE_DIR / "resumes"
JOBS_FILE = BASE_DIR / "jobs" / "jobs.json"
DECISIONS_FILE = BASE_DIR / "decisions" / "job_decisions.json"
APPLICATIONS_FILE = BASE_DIR / "applications.csv"
ROLE_VARIANTS_DIR = BASE_DIR / "resumes" / "role_variants"
LOCATION_RULES_FILE = BASE_DIR / "config" / "location_rules.json"
FORM_RULES_FILE = BASE_DIR / "config" / "form_rules.json"
APPLICATIONS_DIR = BASE_DIR / "applications"

# Initialize Stage 5 components
APPLICATIONS_DIR.mkdir(exist_ok=True)
browser_handler = BrowserHandler(FORM_RULES_FILE)
autofiller = ApplicationAutofiller(RESUME_DIR / "master")
tracker = ApplicationTracker(APPLICATIONS_DIR)

# Initialize Stage 8 (Interview Prep) components
INTERVIEWS_DIR = BASE_DIR / "interviews"
interview_prep = InterviewPrep(str(INTERVIEWS_DIR))
email_automation = EmailAutomation()  # No SMTP configured in demo mode
interview_scheduler = InterviewScheduler()
coaching_materials = CoachingMaterials(str(INTERVIEWS_DIR / "materials"))

# -------------------------
# MCP Init
# -------------------------

mcp = FastMCP("Job Application MCP")

# -------------------------
# Configuration Loading
# -------------------------

def load_location_rules():
    """Load allowed locations from config, with sensible defaults."""
    if LOCATION_RULES_FILE.exists():
        return json.loads(LOCATION_RULES_FILE.read_text())
    return {
        "allowed_regions": ["united states", "usa", "canada", "india"],
        "excluded_regions": ["restricted"],
        "remote_ok": True
    }

def load_role_variants():
    """Load all role variant definitions for scoring context."""
    variants = {}
    if ROLE_VARIANTS_DIR.exists():
        for rv_file in ROLE_VARIANTS_DIR.glob("*.json"):
            variants[rv_file.stem] = json.loads(rv_file.read_text())
    return variants

LOCATION_RULES = load_location_rules()
ROLE_VARIANTS = load_role_variants()

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
# Location Validation
# -------------------------

def is_location_allowed(location_raw: str) -> bool:
    """Check if location matches allowed regions."""
    if not location_raw:
        return False
    
    location_lower = location_raw.lower()
    
    # Check excluded first
    for excluded in LOCATION_RULES.get("excluded_regions", []):
        if excluded.lower() in location_lower:
            return False
    
    # Check allowed
    for allowed in LOCATION_RULES.get("allowed_regions", []):
        if allowed.lower() in location_lower:
            return True
    
    # Check remote
    if LOCATION_RULES.get("remote_ok") and "remote" in location_lower:
        return True
    
    return False


# -------------------------
# Scoring & Keyword Extraction (Pre-computation)
# -------------------------

def compute_matched_keywords(job_text: str, allowed_skills: list) -> list:
    """Extract which allowed_skills appear in the job description."""
    job_lower = job_text.lower()
    return [skill for skill in allowed_skills if skill.lower() in job_lower]

def prepare_evaluation_context(job: dict) -> dict:
    """
    Pre-compute scoring details to pass to Claude.
    This gives Claude full context about why a job scored a certain way.
    """
    role_family = job.get("role_family", "")
    variant = ROLE_VARIANTS.get(role_family, {})
    
    description_text = str(job.get("job_description") or "")
    description_lower = description_text.lower()
    
    allowed_skills = variant.get("allowed_skills", [])
    primary_focus = variant.get("primary_focus", [])
    
    matched_skills = compute_matched_keywords(description_lower, allowed_skills)
    primary_skill_hits = compute_matched_keywords(description_lower, primary_focus)
    
    match_count = len(matched_skills)
    skill_score = min(match_count * 15, 60)
    
    role_text = str(job.get("role") or "").lower()
    role_confidence = 20 if role_family.replace("_", " ") in role_text else 10
    
    description_length = len(description_text)
    description_score = 20 if description_length > 800 else 10 if description_length > 300 else 0
    
    final_score = skill_score + role_confidence + description_score
    
    return {
        "matched_skills": matched_skills,
        "primary_skill_hits": primary_skill_hits,
        "match_count": match_count,
        "skill_score": skill_score,
        "role_confidence": role_confidence,
        "description_score": description_score,
        "final_score": final_score,
        "suggested_decision": "APPLY" if final_score >= 65 else "SKIP"
    }


# -------------------------
# Job Evaluation (single job)
# -------------------------

@mcp.tool()
def evaluate_job(payload: dict):
    """
    Claude-facing evaluation tool.
    Payload includes pre-computed scoring context + job details.
    
    Claude MUST return JSON:
    {
      "decision": "APPLY | SAVE | SKIP",
      "resume": "resume_name_or_null",
      "reason": "short justification"
    }
    
    Claude may override the suggested_decision if warranted.
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
        location_raw = job.get("location") or ""

        # Location filter
        if not is_location_allowed(location_raw):
            results.append({
                **job,
                "decision": "SKIP",
                "resume": None,
                "reason": f"Location not in allowed regions: {location_raw}"
            })
            continue

        # Pre-compute scoring context
        eval_context = prepare_evaluation_context(job)
        
        # Ask Claude to decide with full context
        ai_request = {
            "instruction": (
                "You are an ATS-style evaluator. Use the pre-computed scoring to inform your decision.\n"
                "Return ONLY valid JSON with this schema:\n"
                "{"
                "\"decision\": \"APPLY | SAVE | SKIP\", "
                "\"resume\": \"resume_name_or_null\", "
                "\"reason\": \"short justification\""
                "}\n\n"
                "Rules:\n"
                "- APPLY only for strong matches (final_score >= 65 is a good signal)\n"
                "- SAVE for partial matches (candidate but not perfect fit)\n"
                "- SKIP for weak matches or seniority mismatch\n"
                "- Resume must come from the provided list\n"
                "- Do NOT invent experience\n"
                "- You may override the suggested_decision if you see red flags\n"
            ),
            "job": job,
            "scoring_context": eval_context,
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
            "reason": reason,
            "scoring_context": eval_context  # Persist for audit trail
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
# Stage 5: Application Assistance
# -------------------------

@mcp.tool()
def apply_to_job(
    job_id: str,
    job_url: str,
    company: str,
    role: str,
    role_family: str,
    job_description: str = ""
):
    """
    Fully automate job application: open link, detect form, autofill, submit.
    
    Args:
        job_id: Unique job identifier
        job_url: URL to job application
        company: Company name
        role: Job role/title
        role_family: Role family (e.g., 'backend_engineer')
        job_description: Job description text (optional, for requirement mapping)
    
    Returns:
        Dict with success status, filled fields, and submission confirmation
    """
    try:
        # Check if already applied
        existing = tracker.get_application(job_id)
        if existing and existing.status == ApplicationStatus.SUBMITTED.value:
            return {
                "success": False,
                "status": "already_applied",
                "message": f"Already applied to {company} - {role}",
                "submitted_at": existing.submitted_at
            }
        
        # Load role variant for autofill context
        role_variants = load_role_variants()
        role_variant = role_variants.get(role_family, {})
        
        # Prepare autofill payload
        payload = autofiller.prepare_application_payload(
            {"id": job_id, "company": company, "role": role, "job_description": job_description},
            role_variant
        )
        
        # Check autofill data validity
        is_valid, missing = autofiller.validate_autofill_data(payload["autofill_data"])
        if not is_valid:
            return {
                "success": False,
                "status": "insufficient_data",
                "message": f"Missing required fields: {', '.join(missing)}",
                "missing_fields": missing
            }
        
        # Run async browser automation
        result = asyncio.run(_apply_async(job_url, payload, job_id, company, role))
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "message": str(e),
            "job_id": job_id
        }


async def _apply_async(job_url: str, payload: dict, job_id: str, company: str, role: str):
    """Async implementation of job application flow."""
    try:
        await browser_handler.init()
        
        # Open job application
        page = await browser_handler.open_job_link(job_url)
        
        # Detect form fields
        detected_fields = await browser_handler.detect_form_fields(page)
        
        if not detected_fields:
            await browser_handler.close()
            return {
                "success": False,
                "status": "no_form_detected",
                "message": "Could not detect application form"
            }
        
        # Autofill form
        filled_fields, ambiguous = await browser_handler.autofill_form(
            page,
            payload["autofill_data"],
            detected_fields
        )
        
        # Check for ambiguous fields that need user input
        if payload["ambiguous_fields"]:
            await browser_handler.close()
            return {
                "success": False,
                "status": "pending_user_input",
                "job_id": job_id,
                "company": company,
                "role": role,
                "filled_fields": filled_fields,
                "ambiguous_fields": payload["ambiguous_fields"],
                "message": "Application ready but requires user input for ambiguous fields"
            }
        
        # Submit application
        submit_success = await browser_handler.submit_application(page)
        
        await browser_handler.close()
        
        if submit_success:
            # Track successful application
            tracker.add_application(
                job_id=job_id,
                company=company,
                role=role,
                apply_url=job_url,
                status=ApplicationStatus.SUBMITTED.value
            )
            tracker.update_application(
                job_id=job_id,
                filled_fields=filled_fields,
                notes=f"Auto-submitted to {company}"
            )
            
            return {
                "success": True,
                "status": "submitted",
                "job_id": job_id,
                "company": company,
                "role": role,
                "filled_fields": filled_fields,
                "submitted_at": datetime.now().isoformat(),
                "message": f"Successfully applied to {company} - {role}"
            }
        else:
            return {
                "success": False,
                "status": "submission_failed",
                "message": "Form detected but submission failed",
                "filled_fields": filled_fields
            }
    
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def autofill_application(
    job_id: str,
    job_url: str,
    company: str,
    role: str,
    role_family: str,
    additional_data: dict = None
):
    """
    Manual application assistance: open job, show fields, await user input on ambiguous fields.
    
    Args:
        job_id: Unique job identifier
        job_url: URL to job application
        company: Company name
        role: Job role/title
        role_family: Role family (e.g., 'backend_engineer')
        additional_data: Dict of user-provided answers to ambiguous questions
    
    Returns:
        Dict with form fields detected and ready for submission
    """
    try:
        # Prepare payload with user-provided data
        role_variants = load_role_variants()
        role_variant = role_variants.get(role_family, {})
        
        autofill_data = autofiller.get_autofill_data()
        if additional_data:
            autofill_data.update(additional_data)
        
        # Track application as pending
        tracker.add_application(
            job_id=job_id,
            company=company,
            role=role,
            apply_url=job_url,
            status=ApplicationStatus.PENDING.value
        )
        
        if additional_data:
            tracker.update_application(
                job_id=job_id,
                ambiguous_fields_filled=additional_data
            )
        
        return {
            "success": True,
            "status": "ready_for_submission",
            "job_id": job_id,
            "company": company,
            "role": role,
            "autofill_data": autofill_data,
            "user_provided_data": additional_data or {},
            "message": "Application form ready. User can now submit manually or call apply_to_job() with additional_data."
        }
    
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def get_application_status(job_id: str):
    """Get status of submitted application."""
    app = tracker.get_application(job_id)
    
    if not app:
        return {"success": False, "message": f"No application found for job_id: {job_id}"}
    
    return {
        "success": True,
        "job_id": job_id,
        "company": app.company,
        "role": app.role,
        "status": app.status,
        "submitted_at": app.submitted_at,
        "notes": app.notes
    }


@mcp.tool()
def get_application_summary():
    """Get summary of all applications."""
    summary = tracker.get_summary()
    
    return {
        "success": True,
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }


# -------------------------
# Stage 6: Tracking & Follow-ups
# -------------------------

@mcp.tool()
def update_application_status(
    job_id: str,
    new_status: str,
    notes: str = ""
):
    """
    Update application status and track follow-up date.
    
    Args:
        job_id: Application ID
        new_status: New status (submitted, viewed, interview, offer, rejected, accepted)
        notes: Optional notes about the status change
    
    Returns:
        Dict with updated application and follow-up template (if applicable)
    """
    # Validate status transition
    app = tracker.get_application(job_id)
    if not app:
        return {
            "success": False,
            "status": "not_found",
            "message": f"Application not found: {job_id}"
        }
    
    # Check valid transition
    if not FollowupManager.is_valid_transition(app.status, new_status):
        return {
            "success": False,
            "status": "invalid_transition",
            "message": f"Cannot transition from {app.status} to {new_status}",
            "current_status": app.status,
            "attempted_status": new_status
        }
    
    # Calculate next follow-up date
    next_followup = FollowupManager.calculate_next_followup(
        new_status,
        app.submitted_at,
        app.last_followup_at
    )
    
    # Update application
    tracker.update_application(
        job_id=job_id,
        status=new_status,
        notes=notes,
        last_followup_at=datetime.now().isoformat() if new_status in [ApplicationStatus.VIEWED.value] else None,
        next_followup_at=next_followup
    )
    
    # Get updated app
    updated_app = tracker.get_application(job_id)
    
    # Get follow-up template if applicable
    followup_template = FollowupManager.get_followup_template(
        new_status,
        updated_app.company,
        updated_app.role,
        updated_app.submitted_at
    )
    
    return {
        "success": True,
        "job_id": job_id,
        "company": updated_app.company,
        "role": updated_app.role,
        "previous_status": app.status,
        "new_status": new_status,
        "status_history": updated_app.status_history[-5:] if updated_app.status_history else [],  # Last 5 changes
        "next_followup_at": next_followup,
        "followup_template": followup_template,
        "notes": notes
    }


@mcp.tool()
def get_applications_needing_followup():
    """
    Get list of applications that need follow-up today or overdue.
    
    Returns:
        List of applications with follow-up templates ready to send
    """
    followups = FollowupManager.get_followups_needed(tracker.applications)
    
    return {
        "success": True,
        "count": len(followups),
        "applications": followups,
        "timestamp": datetime.now().isoformat()
    }


@mcp.tool()
def get_application_timeline(job_id: str):
    """
    Get full status history and timeline for an application.
    
    Args:
        job_id: Application ID
    
    Returns:
        Timeline of all status changes with timestamps
    """
    app = tracker.get_application(job_id)
    
    if not app:
        return {
            "success": False,
            "message": f"Application not found: {job_id}"
        }
    
    timeline = []
    if app.status_history:
        for change in app.status_history:
            try:
                timestamp = datetime.fromisoformat(change.get("timestamp", ""))
                timeline.append({
                    "status": change.get("status"),
                    "timestamp": change.get("timestamp"),
                    "date": timestamp.strftime("%Y-%m-%d %H:%M"),
                    "notes": change.get("notes", "")
                })
            except (ValueError, TypeError):
                timeline.append(change)
    
    return {
        "success": True,
        "job_id": job_id,
        "company": app.company,
        "role": app.role,
        "current_status": app.status,
        "submitted_at": app.submitted_at,
        "timeline": timeline,
        "total_status_changes": len(timeline)
    }


# -------------------------
# Interview Prep Tools (Stage 8)
# -------------------------

@mcp.tool()
def schedule_interview(
    job_id: str,
    company: str,
    role: str,
    interview_type: str,
    scheduled_at: str,
    interviewer: str = "TBD",
    location: str = "Virtual (TBD)",
    notes: str = ""
):
    """
    Schedule a new interview for a job application.
    
    Args:
        job_id: Unique job identifier
        company: Company name
        role: Position title
        interview_type: phone_screen, video_interview, technical, behavioral, on_site, panel, final_round, debrief
        scheduled_at: Interview date/time (ISO format: 2026-01-22T14:00:00)
        interviewer: Name of interviewer
        location: Interview location (virtual or physical address)
        notes: Additional notes about the interview
    
    Returns:
        Interview record with ID and status
    """
    try:
        interview = interview_prep.schedule_interview(
            job_id=job_id,
            company=company,
            role=role,
            interview_type=interview_type,
            scheduled_at=scheduled_at,
            interviewer=interviewer,
            location=location,
            notes=notes
        )
        
        # Calculate and schedule reminders
        reminders = interview_scheduler.calculate_reminder_times(
            interview['id'],
            scheduled_at,
            interview_type
        )
        interview_scheduler.schedule_reminders(interview['id'], reminders)
        
        return {
            "success": True,
            "interview_id": interview['id'],
            "company": company,
            "role": role,
            "scheduled_at": scheduled_at,
            "reminders_scheduled": len(reminders),
            "message": f"Interview scheduled for {company} - {role}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_upcoming_interviews(days: int = 7):
    """
    Get all upcoming interviews in the next N days.
    
    Args:
        days: Number of days to look ahead (default: 7)
    
    Returns:
        List of upcoming interviews with details
    """
    interviews = interview_prep.get_upcoming_interviews(days)
    
    return {
        "success": True,
        "count": len(interviews),
        "days": days,
        "interviews": [
            {
                "id": i['id'],
                "company": i['company'],
                "role": i['role'],
                "type": i['interview_type'],
                "scheduled_at": i['scheduled_at'],
                "interviewer": i['interviewer'],
                "location": i['location'],
                "status": i['status'],
                "preparation_complete": i['preparation_complete']
            }
            for i in interviews
        ]
    }


@mcp.tool()
def get_interview_prep_materials(job_id: str, interview_type: str, role_family: str):
    """
    Get comprehensive interview preparation materials.
    
    Args:
        job_id: Job ID for reference
        interview_type: Type of interview (affects preparation focus)
        role_family: Role family (backend_engineer, data_engineer, etc.)
    
    Returns:
        Complete preparation package with guides, questions, and tips
    """
    
    materials = {
        "interview_id": f"int_{job_id}",
        "interview_type": interview_type,
        "role_family": role_family,
        "generated_at": datetime.now().isoformat(),
        
        # STAR Method Guide
        "star_method": coaching_materials.get_star_method_guide(),
        
        # Common Questions
        "common_questions": coaching_materials.get_common_interview_questions(role_family),
        
        # Prep Checklist
        "prep_checklist": interview_scheduler.get_interview_prep_checklist(interview_type),
        
        # Interview Tips
        "interview_tips": interview_scheduler.get_interview_tips(interview_type),
        
        # Strength/Weakness Framework
        "strength_weaknesses": coaching_materials.get_strength_weaknesses_framework(),
        
        # Questions to Ask
        "questions_to_ask": coaching_materials.get_questions_to_ask_interviewer(
            role_family,
            "Company Name"
        )
    }
    
    return materials


@mcp.tool()
def get_company_research_template(company: str):
    """
    Get a research template for company deep-dive preparation.
    
    Args:
        company: Company name
    
    Returns:
        Research template with guided questions and sources
    """
    return coaching_materials.get_company_research_template(company)


@mcp.tool()
def generate_elevator_pitch(
    name: str,
    current_role: str,
    key_achievements: list,
    career_goal: str
):
    """
    Generate a professional elevator pitch (2-minute introduction).
    
    Args:
        name: Your name
        current_role: Current job title
        key_achievements: List of 3-4 key accomplishments
        career_goal: What you're looking to achieve
    
    Returns:
        Elevator pitch with delivery tips
    """
    return coaching_materials.generate_elevator_pitch(
        name,
        current_role,
        key_achievements,
        career_goal
    )


@mcp.tool()
def send_interview_reminder_email(
    company: str,
    role: str,
    interview_type: str,
    scheduled_at: str,
    interviewer: str,
    location: str,
    recipient_email: str = ""
):
    """
    Generate and optionally send an interview reminder email.
    
    Args:
        company: Company name
        role: Position title
        interview_type: Type of interview
        scheduled_at: Interview date/time
        interviewer: Interviewer name
        location: Interview location
        recipient_email: Email address to send to (optional - demo mode returns template)
    
    Returns:
        Email template (in demo mode) or send confirmation
    """
    
    email_template = email_automation.get_interview_reminder_template(
        company=company,
        role=role,
        interview_type=interview_type,
        scheduled_at=scheduled_at,
        interviewer=interviewer,
        location=location
    )
    
    if recipient_email:
        result = email_automation.send_email(
            to_email=recipient_email,
            subject=email_template['subject'],
            body=email_template['body']
        )
        return result
    
    return {
        "success": True,
        "mode": "template",
        "subject": email_template['subject'],
        "body": email_template['body'],
        "note": "Email template generated. Provide recipient_email to send."
    }


@mcp.tool()
def send_thank_you_email(
    company: str,
    role: str,
    interviewer_name: str,
    interview_date: str,
    talking_points: str = "",
    recipient_email: str = ""
):
    """
    Generate and optionally send a thank you email after an interview.
    
    Args:
        company: Company name
        role: Position title
        interviewer_name: Name of the interviewer
        interview_date: Date of the interview
        talking_points: Key discussion points to reference (optional)
        recipient_email: Email to send to (optional - demo mode returns template)
    
    Returns:
        Email template or send confirmation
    """
    
    email_template = email_automation.get_thank_you_email_template(
        company=company,
        role=role,
        interviewer_name=interviewer_name,
        interview_date=interview_date,
        talking_points=talking_points
    )
    
    if recipient_email:
        result = email_automation.send_email(
            to_email=recipient_email,
            subject=email_template['subject'],
            body=email_template['body']
        )
        return result
    
    return {
        "success": True,
        "mode": "template",
        "subject": email_template['subject'],
        "body": email_template['body'],
        "note": "Email template generated. Provide recipient_email to send."
    }


@mcp.tool()
def update_interview_status(
    interview_id: str,
    new_status: str,
    feedback: str = "",
    notes: str = ""
):
    """
    Update interview status and log feedback.
    
    Args:
        interview_id: Interview ID to update
        new_status: New status (scheduled, confirmed, in_progress, completed, cancelled, rescheduled)
        feedback: Interview feedback or feedback from interviewer
        notes: Additional notes
    
    Returns:
        Updated interview record
    """
    try:
        updated = interview_prep.update_interview_status(
            interview_id,
            new_status,
            feedback=feedback,
            notes=notes
        )
        
        return {
            "success": True,
            "interview_id": updated['id'],
            "status": updated['status'],
            "company": updated['company'],
            "role": updated['role'],
            "feedback": updated['feedback'],
            "message": f"Interview status updated to {new_status}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_interview_statistics():
    """
    Get comprehensive interview statistics and metrics.
    
    Returns:
        Interview statistics including totals by type, status, and company
    """
    stats = interview_prep.get_interview_stats()
    
    return {
        "success": True,
        "statistics": stats,
        "generated_at": datetime.now().isoformat()
    }


@mcp.tool()
def save_interview_prep_notes(interview_id: str, notes: str):
    """
    Save preparation notes for an interview.
    
    Args:
        interview_id: Interview ID
        notes: Preparation notes (markdown format recommended)
    
    Returns:
        File path where notes were saved
    """
    try:
        file_path = interview_prep.save_prep_notes(interview_id, notes)
        
        return {
            "success": True,
            "interview_id": interview_id,
            "file_path": file_path,
            "message": "Preparation notes saved successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def mark_interview_prep_complete(interview_id: str):
    """
    Mark interview preparation as complete and ready.
    
    Args:
        interview_id: Interview ID
    
    Returns:
        Updated interview record with prep_complete flag set
    """
    try:
        updated = interview_prep.mark_prep_complete(interview_id)
        
        return {
            "success": True,
            "interview_id": updated['id'],
            "preparation_complete": updated['preparation_complete'],
            "company": updated['company'],
            "role": updated['role'],
            "message": "Interview preparation marked as complete"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# -------------------------
# Server Start
# -------------------------

if __name__ == "__main__":
    mcp.run()
