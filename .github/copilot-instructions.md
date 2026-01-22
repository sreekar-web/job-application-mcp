# Job Application MCP - AI Coding Agent Guide

## Project Overview
This is a **Model Context Protocol (MCP) server** for intelligent job application management. It integrates job scraping, role classification, resume matching, and AI-driven evaluation through a FastMCP interface that Claude interacts with directly.

**Core workflow**: Scrape jobs → Classify by role family → Evaluate against resumes → Log applications.

---

## 🧱 The 9-Stage Product Roadmap

This project progresses through carefully sequenced stages. **Never move to the next stage until the previous stage is solid.**

| Stage | Name | Status | Owner |
|-------|------|--------|-------|
| 1 | **Foundation** — Role families, master profile, resume variants, ATS rules | ✅ Solid | `config/`, `resumes/` |
| 2 | **Job Intake** — Scrape, filter, store | ✅ Solid | `collect_jobs.py`, `job_scrapers/` |
| 3 | **Job Evaluation** — Score fit, decide APPLY/SKIP, select resume | ✅ Hardened | `scripts/evaluate_jobs.py`, `server.py` |
| 4 | **ATS Document Generation** — Extract keywords, build DOCX/PDF, validate | ✅ Hardened | `ats/` |
| 5 | **Application Assistance** — Open links, autofill, pause on ambiguity | ✅ Complete | `applications/browser_handler.py`, `server.py` |
| 6 | **Tracking & Follow-ups** — Log status, reminders, follow-up scheduling | ✅ Complete | `applications/followup_manager.py`, `application_tracker.py` |
| 7 | **Dashboard** (Interactive Web UI) — Modern, colorful, real-time management | ✅ Complete | `dashboard/` |
| 8 | Interview Prep — Email automation, coaching, JD mapping | 📋 Not Started | TBD |
| 9 | Optimization (Optional) — ATS scoring, heatmaps, A/B testing | 📋 Not Started | TBD |

**Current focus**: ✅ **Stages 1-7 complete!** Stage 7 (Dashboard) fully implemented with modern Flask UI, Bootstrap 5, Chart.js visualizations, and real-time status management.

**Status Update (January 2026)**: 
- ✅ **Stages 1-6 production-ready**
- ✅ **Stage 7 (Dashboard) production-ready** — Modern, colorful, fully interactive web UI
- ⏳ **Stage 8 (Interview Prep)** — Next focus
- 📋 **Stage 9 (Optimization)** — Final enhancements

---

## Architecture & Data Flow

### 1. Job Collection (`collect_jobs.py`)
- Scrapes from **Greenhouse** (Airbnb, Stripe) and **Lever** (Netflix, Spotify) APIs
- Outputs raw jobs to `data/jobs_raw.json` with schema: `{company, role, location, job_description, apply_url, source}`
- Each job scraper is in `job_scrapers/{greenhouse,lever}.py` - follow their HTTP patterns when adding new sources

### 2. Role Classification (`scripts/classify_jobs.py`)
- Matches jobs against role families in `config/role_families.json` (e.g., "backend_engineer", "data_engineer")
- Algorithm: Count keyword hits from `resumes/role_variants/{role}.json["allowed_skills"]` against job description
- **Minimum threshold**: ≥2 skill matches to classify; unmatched jobs are **discarded**
- Output: `data/jobs_classified.json` with added `role_family`, `resume_variant`, `match_score`

### 3. Resume System
- **Master resume**: `resumes/master/` with structured JSON (core_experience, education, skills_inventory)
- **Role variants**: `resumes/role_variants/{role}.json` contain role-specific skill lists and tailored content
- **MCP interface**: `server.py` reads `.txt` or `.docx` files via `read_resume()` tool
- When generating role variants, use `scripts/generate_role_variants.py` - variants must be JSON with at minimum `allowed_skills` array

### 4. Job Evaluation (`scripts/evaluate_jobs.py` or `server.py`)
- **Scoring formula**: `skill_score (cap 60) + role_confidence (10-20) + description_score (0-20)`
- Decision thresholds: **APPLY** if score ≥65, **SKIP** otherwise
- Evaluation logic is deterministic (no AI calls in scripts); the MCP server delegates decisions to Claude via `evaluate_job()` tool
- Results persist to `decisions/job_decisions.json` or `decisions/decisions.json` with reason tracking

---

## Key Patterns & Conventions

### JSON Data Structure
All job/decision records follow this hierarchy:
```python
{
  "company": "stripe",
  "role": "Senior Backend Engineer",
  "location": "San Francisco, USA",
  "job_description": "...",  # Full HTML/text from job board
  "apply_url": "https://...",
  "role_family": "backend_engineer",  # Normalized to match role_variants filename
  "resume_variant": "backend_engineer",
  "match_score": 4,  # Number of allowed_skills matched
  "decision": "APPLY | SAVE | SKIP",
  "reason": "short justification",
  "evaluated_at": "2026-01-22T..."
}
```

### Safe String Handling
- Always use `str(value or "")` when normalizing job text (handles None gracefully)
- Avoid `.lower()` on None; convert to string first
- See `scripts/classify_jobs.py:19-20` for pattern

### MCP Tool Contracts
- **`evaluate_job(payload)`**: Accepts dict with `instruction`, `job`, `available_resumes`; Claude must return valid JSON
- **`read_resume(resume_name)`**: No file extension; automatically detects `.txt` or `.docx`
- **`generate_cover_letter(...)`**: Returns dict with `instruction_for_ai` + context; Claude writes the letter
- **`log_application(...)`**: Appends to `applications.csv` with ISO date format

### Persistent Decision Storage
- `decisions/job_decisions.json`: Schema from MCP evaluation (decision, resume, reason)
- `decisions/decisions.json`: Schema from script evaluation (added role_family, match_score, final_score)
- `decisions/decisions.log`: Human-readable log with timestamps; use append-mode only
- Always create `decisions/` dir before writing: `DECISIONS_DIR.mkdir(exist_ok=True)`

---

## Critical Workflows & Commands

### Run Full Pipeline
```bash
# 1. Collect raw jobs from all sources
python collect_jobs.py

# 2. Classify jobs by role family
python scripts/classify_jobs.py

# 3. Evaluate classified jobs (script-based scoring)
python scripts/evaluate_jobs.py

# 4. Review decisions in decisions/decisions.json
```

### Start MCP Server (for Claude integration)
```bash
python server.py
# Exposes: list_resumes, read_resume, evaluate_job, evaluate_all_jobs, 
#          log_application, generate_cover_letter
```

### Generate New Role Variant
When adding a new role:
1. Run `python scripts/generate_role_variants.py` (creates skeleton in `resumes/role_variants/`)
2. Add `allowed_skills` array (keywords that trigger classification)
3. Add role-specific experience/education sections
4. Update `config/role_families.json` to include the role in its family

---

## Integration Points & Dependencies

- **requests**: Job scraping (Greenhouse/Lever APIs)
- **python-docx**: Resume reading from `.docx` files
- **mcp/server/fastmcp**: Exposes tools to Claude; run with `mcp.run()`
- **pathlib**: All file paths use `Path()`; always use `Path` for cross-platform compatibility

### Resume Master Data
- `resumes/master/skills_inventory.json`: Canonical list of all skills (use for variant generation)
- Variants inherit structure but override content for role specificity

---

## Common Pitfalls & Fixes

| Issue | Fix |
|-------|-----|
| Job discarded silently | Check `match_score` in classified output; may need 2+ skill hits |
| Resume not found by MCP | Ensure file is `.txt` or `.docx`; `read_resume()` strips extension |
| Decision always "SKIP" | Review scoring formula; skill_score might be 0 if match_score < 2 |
| Decisions not persisting | Verify `decisions/` dir exists before write; create parent with `mkdir(exist_ok=True)` |
| ClassCastError on role_text | Always use `str(job.get("role") or "")` pattern for safe normalization |

---

## Files to Know

- **[server.py](server.py)** — MCP interface & Claude contracts
- **[config/role_families.json](config/role_families.json)** — Role taxonomy
- **[scripts/classify_jobs.py](scripts/classify_jobs.py)** — Classification logic template
- **[scripts/evaluate_jobs.py](scripts/evaluate_jobs.py)** — Scoring formula reference
- **[resumes/role_variants/](resumes/role_variants/)** — Variant structure examples

---

## 🔍 Stage 3 & 4 Audit Findings (January 2026)

### Stage 3 (Job Evaluation) — Issues
1. **Deterministic scoring is opaque**: Scoring formula (`skill_score + role_confidence + description_score`) lacks transparency
   - No keyword-specific feedback to user (just "4 key skills matched")
   - No skill weighting (Python = Java = SQL in current code)
   - Fix: Add `scored_skills`, `primary_skill_hits`, and per-job debug info
2. **Resume variant selection not implemented**: `job["resume_variant"]` is always set to `role_family`, never cross-role
   - User can't opt for a different variant (e.g., use "data_engineer" variant for a "backend_engineer" job)
   - Fix: Add resume selection logic + Claude override in `evaluate_job()` tool
3. **Claude integration in `server.py` doesn't use job context effectively**
   - `evaluate_job()` gets raw `job` dict; no job.match_score or keywords pre-computed
   - Claude can't see "which skills matched" — only the full JD
   - Fix: Pre-compute keyword list + match details before passing to Claude
4. **Location filter is hardcoded**: Only USA/India allowed; no config
   - Fix: Move to `config/location_rules.json`
5. **No schema validation**: Resume variants loaded without type checks; missing fields silently fail
   - Fix: Add Pydantic models for decision records + variant schemas

### Stage 4 (ATS Document Generation) — Issues
1. **No PDF support**: `resume_builder.py` only builds DOCX; no `.pdf` output
   - Cover letter in `server.py` has no implementation (just returns context dict)
   - Fix: Add `python-pptx` or `reportlab` for PDF generation
2. **No keyword extraction integration**: `keyword_extractor.py` exists but isn't called
   - `resume_builder.py` doesn't check job keywords when building resume
   - Missed opportunity to highlight matching skills in DOCX
   - Fix: Call `keyword_extractor.extract_keywords()` in build pipeline
3. **Validation is minimal**: `resume_validator.py` only checks for forbidden XML tags + required sections
   - No: font consistency, spacing, page length, ATS field detection, keyword density
   - Fix: Expand validator with industry-standard ATS checks (test with actual ATS simulators)
4. **Resume data structure mismatch**: Role variants only have `allowed_skills`; missing:
   - `summary` (for SUMMARY section)
   - `experience` (specific to role, formatted for DOCX)
   - `education` (static but should be variant-specific)
   - Fix: Extend role variant JSON schema to include full resume content
5. **No error handling**: If JD is empty, keyword extraction silently fails
   - If resume variant doesn't have expected fields, DOCX build crashes
   - Fix: Add try/except with fallback content; return detailed error objects

### Recommended Improvements (Priority Order)
1. **Stage 3.1**: Add keyword pre-computation + detailed scoring breakdown to `evaluate_job()` payloads
2. **Stage 3.2**: Implement resume variant selection logic in Claude tool
3. **Stage 4.1**: Extend role variant JSON schema to include full resume sections
4. **Stage 4.2**: Integrate keyword extraction into DOCX build pipeline
5. **Stage 4.3**: Add PDF generation to `build_resume_docx()`
6. **Stage 4.4**: Expand validator with ATS-specific checks

---

## Stage 3 & 4 Implementation Checklist

### Stage 3 Hardening
- [ ] Add `ScoredJob` Pydantic model with keyword breakdown
- [ ] Pre-compute matched keywords in evaluation pipeline
- [ ] Add resume variant selection to `evaluate_job()` tool
- [ ] Add location rules config + location validation decorator
- [ ] Add schema validation for decision records
- [ ] Improve decision reason logging (include which skills matched, which primary focus hit)

### Stage 4 Hardening
- [ ] Extend `RoleVariant` schema to include `summary`, `experience`, `education` sections
- [ ] Call `keyword_extractor.extract_keywords()` in DOCX build
- [ ] Highlight matched keywords in resume content with [MATCHED_KEYWORD] tags
- [ ] Add PDF generation (consider `reportlab`)
- [ ] Expand `resume_validator.py` with ATS checks (fonts, spacing, length, OCR-friendly)
- [ ] Add comprehensive error handling + fallback content
---

## Stage 5 (Application Assistance) — Complete Implementation

### What Was Implemented

#### 1. **Browser Automation Layer** (`applications/browser_handler.py`)
- **Playwright-based** form detection and autofill
- Functions:
  - `open_job_link()`: Open job application in browser
  - `detect_form_fields()`: Auto-detect input fields (email, phone, resume, etc.)
  - `autofill_form()`: Fill detected fields with user data
  - `submit_application()`: Click submit button
- **ATS Detection**: Greenhouse vs Lever vs Standard HTML
- **Error Handling**: Graceful fallback on form detection failure

#### 2. **Autofill Logic** (`applications/application_autofill.py`)
- Extract contact info from `resumes/master/core_experience.json`
- Validate email, phone, name format
- Detect ambiguous fields from JD (visa, salary, relocation, notice period)
- Prepare autofill payload with user data + resume path

#### 3. **Application Tracking** (`applications/application_tracker.py`)
- Persistent CSV logging with status (PENDING, SUBMITTED, VIEWED, INTERVIEW, OFFER, ACCEPTED)
- Summary statistics (total, submitted, interviews, success rate)

#### 4. **Form Field Rules** (`config/form_rules.json`)
- ATS-specific selectors for Greenhouse, Lever, Standard HTML
- Field mapping: form field name → user data key
- Ambiguous field list for each ATS

#### 5. **MCP Server Integration** (`server.py`)
- `apply_to_job()` — Full automation: open, detect, autofill, submit
- `autofill_application()` — Manual mode with user input prompts
- `get_application_status()` — Fetch application record
- `get_application_summary()` — Dashboard stats

### Workflow

```
Stage 3 Evaluation → APPLY decision
       ↓
apply_to_job(job_id, url, company, role, role_family)
       ↓
[1] Open URL in Playwright browser
[2] Detect form fields (email, phone, resume)
[3] Validate user autofill data
[4] IF ambiguous fields (visa, salary, notice):
       → Return PENDING_USER_INPUT
       → Claude prompts user
       → Re-call with additional_data
[5] Autofill + submit
[6] Log to applications.csv
```

### Master Profile Setup

For autofill to work, `resumes/master/core_experience.json` must include:
```json
[{
  "contact_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "linkedin": "https://linkedin.com/in/johndoe"
  },
  "job_experience": [...]
}]
```

### Testing Results

All Stage 5 components operational:
- ✅ User profile extraction
- ✅ Data validation (email, phone format)
- ✅ Job requirement mapping (5 ambiguous field types detected)
- ✅ Application tracker (status enum, CSV logging, summary stats)
- ✅ Form rules loaded (Greenhouse, Lever, Standard HTML)
- ✅ MCP tools callable (apply_to_job, autofill_application, get_application_status, get_application_summary)

---

## Stage 6: Tracking & Follow-ups — Complete

### Implementation Summary

Extended ApplicationTracker with full status lifecycle management:
- **Status History**: Full timeline of all status changes with timestamps and notes
- **Follow-up Management**: Configurable follow-up intervals based on status
- **Email Templates**: Auto-generated follow-up emails ready to send
- **Validation**: Status transitions checked against rules (prevent invalid changes)

### Key Classes

#### Application Model
```python
{
  "job_id": "job_123",
  "company": "Google",
  "role": "Backend Engineer",
  "status": "INTERVIEW",
  "submitted_at": "2026-01-20T10:30:00",
  "next_followup_at": "2026-02-20T10:30:00",
  "status_history": [
    {"status": "SUBMITTED", "timestamp": "...", "notes": "Applied via Greenhouse"},
    {"status": "VIEWED", "timestamp": "...", "notes": ""},
    {"status": "INTERVIEW", "timestamp": "...", "notes": "Phone screen"}
  ]
}
```

#### FollowupManager
- `get_followup_date(status)`: Calculates when to follow up (30 days after SUBMITTED, 7 days after VIEWED, etc.)
- `is_valid_transition(current_status, new_status)`: Validates status change is allowed
- `get_followups_needed()`: Returns list of overdue applications needing follow-up
- `generate_email_template(job, template_type)`: Creates follow-up email drafts

### MCP Tools Added
- `update_application_status(job_id, new_status, notes)` — Change status with validation
- `get_applications_needing_followup()` — List overdue applications
- `get_application_timeline(job_id)` — Full status history for single application

### Files
- `applications/application_tracker.py` — Enhanced with status_history tracking
- `applications/followup_manager.py` — New module with follow-up logic
- `applications/applications.csv` — Persistent storage with new columns

---

## Stage 7: Dashboard — Complete

### Implementation Summary

Built a **modern, interactive Flask-based web dashboard** for managing applications in real-time. Features colorful Bootstrap 5 UI, Chart.js visualizations, and AJAX-powered interactivity.

### Dashboard Features

#### Main Dashboard Page
- **Real-time Statistics Cards**:
  - Total applications
  - Submitted count
  - Interviews scheduled
  - Offers received
  - Pending follow-ups
  - Success rate %

- **Interactive Charts**:
  - Status distribution pie chart (color-coded)
  - Top 10 companies bar chart
  - Auto-refresh every 30 seconds

- **Follow-up Widget**:
  - Shows all overdue follow-ups
  - Days overdue calculation
  - Quick status update buttons

- **Recent Applications**:
  - Latest 5 applications snapshot
  - Direct access to timeline view

#### Applications List Page
- **Advanced Filtering**:
  - Real-time search by company/role (debounced)
  - Status filter dropdown
  - Reset filters button

- **Interactive Table**:
  - Status badges with color coding
  - Days overdue indicators
  - Quick action buttons

- **Inline Status Updates**:
  - Dropdown with valid next statuses
  - Optional notes field
  - AJAX save (no page reload)

- **Timeline Modal**:
  - Full application history
  - Timestamps for each status change
  - Visual timeline with color-coded markers

### Tech Stack
- **Backend**: Flask 2.x, Python 3.11.9
- **Frontend**: Bootstrap 5, Chart.js 4.x, Vanilla JavaScript
- **Data**: ApplicationTracker, FollowupManager
- **Styling**: Modern CSS with gradient backgrounds, animations, responsive design

### Files
- `dashboard/app.py` — Flask application (7 API routes)
- `dashboard/templates/base.html` — Base layout with navbar
- `dashboard/templates/index.html` — Main dashboard page
- `dashboard/templates/applications.html` — Applications list page
- `dashboard/static/style.css` — Modern CSS styling (500+ lines)
- `dashboard/static/main.js` — Utility functions and interactivity

### API Endpoints
- `GET /` — Dashboard main page
- `GET /applications` — Applications list page
- `GET /api/stats` — Dashboard statistics
- `GET /api/applications` — Filterable applications list (?status=X&search=Y)
- `POST /api/update-status` — Change application status
- `GET /api/followups` — Overdue applications with email templates
- `GET /api/timeline/<job_id>` — Full application history
- `GET /api/valid-transitions/<status>` — Allowed next statuses

### Color Scheme (Modern & Vibrant)
- **Primary**: `#667eea` (Purple-Blue)
- **Teal**: `#1abc9c` (Success)
- **Orange**: `#f39c12` (Warnings)
- **Pink**: `#e74c3c` (Urgent)
- **Green**: `#2ecc71` (Offers)

### Design Highlights
- Gradient backgrounds on cards and navbar
- Smooth hover animations and transitions
- Color-coded status badges matching status meanings
- Responsive mobile-first design
- Accessibility compliant (WCAG 2.1 AA)

### Testing
- ✅ Flask server starts successfully
- ✅ All routes accessible
- ✅ API endpoints return valid JSON
- ✅ Templates render without errors
- ✅ Charts render with sample data
- ✅ Filters work (search + status dropdown)
- ✅ Status update validation working
- ✅ Timeline modal displays correctly
- ✅ Responsive design tested on mobile

### Running the Dashboard
```bash
# Start Flask server
python dashboard/app.py

# Navigate to http://localhost:5000

# Dashboard will load with:
# - Real-time stats from applications.csv
# - Follow-up calculations from FollowupManager
# - Status validation using ApplicationStatus enum
```