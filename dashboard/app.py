"""
Job Application Dashboard - Flask Web Application
Interactive dashboard for viewing and managing job applications
"""

import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# Import tracker and followup manager
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from applications.application_tracker import ApplicationTracker, ApplicationStatus
from applications.followup_manager import FollowupManager

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Initialize tracker
tracker = ApplicationTracker()

# -------------------------
# Routes
# -------------------------

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/applications')
def applications():
    """Applications list page"""
    return render_template('applications.html')


@app.route('/interview-prep')
def interview_prep():
    """Interview preparation page"""
    return render_template('interview_prep.html')


# -------------------------
# API Endpoints
# -------------------------

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    summary = tracker.get_summary()
    
    # Get additional stats
    apps = tracker.applications.values()
    
    # Count by status
    status_counts = {}
    for app in apps:
        status = app.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Get company diversity
    companies = set(app.company for app in apps)
    
    return jsonify({
        "success": True,
        "summary": summary,
        "status_counts": status_counts,
        "company_count": len(companies),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/applications')
def get_applications():
    """Get all applications with optional filtering"""
    status_filter = request.args.get('status')
    search = request.args.get('search', '').lower()
    
    apps = []
    for job_id, app in tracker.applications.items():
        # Apply filters
        if status_filter and app.status != status_filter:
            continue
        
        if search and not (search in app.company.lower() or search in app.role.lower()):
            continue
        
        # Build app dict
        app_dict = {
            "job_id": job_id,
            "company": app.company,
            "role": app.role,
            "status": app.status,
            "apply_url": app.apply_url,
            "submitted_at": app.submitted_at,
            "next_followup_at": app.next_followup_at,
            "notes": app.notes,
            "status_history_count": len(app.status_history) if app.status_history else 0
        }
        
        # Check if needs follow-up
        if app.next_followup_at:
            followup_date = datetime.fromisoformat(app.next_followup_at).date()
            today = datetime.now().date()
            app_dict["days_overdue"] = (today - followup_date).days if followup_date <= today else 0
        else:
            app_dict["days_overdue"] = 0
        
        apps.append(app_dict)
    
    # Sort by submitted date (newest first)
    apps.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    
    return jsonify({
        "success": True,
        "applications": apps,
        "count": len(apps),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/update-status', methods=['POST'])
def update_status():
    """Update application status"""
    data = request.get_json()
    job_id = data.get('job_id')
    new_status = data.get('status')
    notes = data.get('notes', '')
    
    if not job_id or not new_status:
        return jsonify({
            "success": False,
            "message": "Missing job_id or status"
        }), 400
    
    # Validate transition
    app = tracker.get_application(job_id)
    if not app:
        return jsonify({
            "success": False,
            "message": "Application not found"
        }), 404
    
    if not FollowupManager.is_valid_transition(app.status, new_status):
        return jsonify({
            "success": False,
            "message": f"Invalid transition: {app.status} → {new_status}"
        }), 400
    
    # Update application
    next_followup = FollowupManager.calculate_next_followup(
        new_status,
        app.submitted_at,
        app.last_followup_at
    )
    
    tracker.update_application(
        job_id=job_id,
        status=new_status,
        notes=notes,
        next_followup_at=next_followup
    )
    
    # Get updated app
    updated_app = tracker.get_application(job_id)
    
    return jsonify({
        "success": True,
        "message": f"Status updated to {new_status}",
        "app": {
            "job_id": job_id,
            "status": updated_app.status,
            "next_followup_at": updated_app.next_followup_at,
            "notes": notes
        }
    })


@app.route('/api/followups')
def get_followups():
    """Get applications needing follow-up"""
    followups = FollowupManager.get_followups_needed(tracker.applications)
    
    # Add template to each
    for followup in followups:
        if not followup.get('template'):
            followup['template'] = FollowupManager.get_followup_template(
                followup['status'],
                followup['company'],
                followup['role']
            )
    
    return jsonify({
        "success": True,
        "followups": followups,
        "count": len(followups),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/timeline/<job_id>')
def get_timeline(job_id):
    """Get status timeline for an application"""
    app = tracker.get_application(job_id)
    
    if not app:
        return jsonify({
            "success": False,
            "message": "Application not found"
        }), 404
    
    timeline = []
    if app.status_history:
        for change in app.status_history:
            try:
                timestamp = datetime.fromisoformat(change.get("timestamp", ""))
                timeline.append({
                    "status": change.get("status"),
                    "timestamp": change.get("timestamp"),
                    "date": timestamp.strftime("%b %d, %H:%M"),
                    "notes": change.get("notes", "")
                })
            except (ValueError, TypeError):
                timeline.append(change)
    
    return jsonify({
        "success": True,
        "job_id": job_id,
        "company": app.company,
        "role": app.role,
        "current_status": app.status,
        "timeline": timeline,
        "total_changes": len(timeline)
    })


@app.route('/api/valid-transitions/<current_status>')
def get_valid_transitions(current_status):
    """Get valid next statuses for current status"""
    transitions = FollowupManager.get_status_transitions()
    valid_next = transitions.get(current_status, [])
    
    return jsonify({
        "success": True,
        "current_status": current_status,
        "valid_transitions": valid_next
    })


# -------------------------
# Interview Prep API Endpoints (Stage 8)
# -------------------------

@app.route('/api/interviews', methods=['GET'])
def get_interviews():
    """Get interviews (upcoming or all)"""
    try:
        # Import here to avoid circular imports
        from interviews.interview_prep import InterviewPrep
        from interviews.interview_scheduler import InterviewScheduler
        
        interview_prep = InterviewPrep(str(Path(__file__).parent.parent / "interviews"))
        scheduler = InterviewScheduler()
        
        upcoming_only = request.args.get('upcoming', 'true').lower() == 'true'
        days = int(request.args.get('days', 7))
        
        if upcoming_only:
            interviews = interview_prep.get_upcoming_interviews(days)
        else:
            interviews = interview_prep.get_all_interviews()
        
        return jsonify({
            "success": True,
            "count": len(interviews),
            "interviews": interviews
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interviews', methods=['POST'])
def schedule_interview():
    """Schedule a new interview"""
    try:
        from interviews.interview_prep import InterviewPrep
        from interviews.interview_scheduler import InterviewScheduler
        
        interview_prep = InterviewPrep(str(Path(__file__).parent.parent / "interviews"))
        scheduler = InterviewScheduler()
        
        data = request.get_json()
        
        interview = interview_prep.schedule_interview(
            job_id=data.get('job_id', f'job_{datetime.now().timestamp()}'),
            company=data.get('company', ''),
            role=data.get('role', ''),
            interview_type=data.get('interview_type', ''),
            scheduled_at=data.get('scheduled_at', ''),
            interviewer=data.get('interviewer', 'TBD'),
            location=data.get('location', 'Virtual'),
            notes=data.get('notes', '')
        )
        
        # Schedule reminders
        reminders = scheduler.calculate_reminder_times(
            interview['id'],
            data.get('scheduled_at'),
            data.get('interview_type')
        )
        scheduler.schedule_reminders(interview['id'], reminders)
        
        return jsonify({
            "success": True,
            "interview_id": interview['id'],
            "message": f"Interview scheduled for {data.get('company')} - {data.get('role')}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interviews/<interview_id>', methods=['GET'])
def get_interview(interview_id):
    """Get interview details"""
    try:
        from interviews.interview_prep import InterviewPrep
        
        interview_prep = InterviewPrep(str(Path(__file__).parent.parent / "interviews"))
        interviews = interview_prep.get_all_interviews()
        
        interview = next((i for i in interviews if i['id'] == interview_id), None)
        
        if not interview:
            return jsonify({"success": False, "message": "Interview not found"}), 404
        
        return jsonify({
            "success": True,
            "interview": interview
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interviews/<interview_id>/status', methods=['POST'])
def update_interview_status(interview_id):
    """Update interview status"""
    try:
        from interviews.interview_prep import InterviewPrep
        
        interview_prep = InterviewPrep(str(Path(__file__).parent.parent / "interviews"))
        data = request.get_json()
        
        interview = interview_prep.update_interview_status(
            interview_id,
            new_status=data.get('status', ''),
            feedback=data.get('feedback', ''),
            notes=data.get('notes', '')
        )
        
        return jsonify({
            "success": True,
            "interview": interview,
            "message": f"Status updated to {data.get('status')}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interviews/<interview_id>/prep-materials', methods=['GET'])
def get_prep_materials(interview_id):
    """Get prep materials for interview"""
    try:
        from interviews.coaching_materials import CoachingMaterials
        
        role_family = request.args.get('role_family', 'backend_engineer')
        interview_type = request.args.get('interview_type', 'technical')
        
        coaching = CoachingMaterials(str(Path(__file__).parent.parent / "interviews" / "materials"))
        
        return jsonify({
            "success": True,
            "materials": {
                "star_method": coaching.get_star_method_guide(),
                "common_questions": coaching.get_common_interview_questions(role_family),
                "strength_weaknesses": coaching.get_strength_weaknesses_framework(),
                "questions_to_ask": coaching.get_questions_to_ask_interviewer(role_family, "Company"),
                "interview_type": interview_type
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interviews/email-template', methods=['GET'])
def get_email_template():
    """Get email template"""
    try:
        from interviews.email_automation import EmailAutomation
        
        email_auto = EmailAutomation()
        template_type = request.args.get('type', 'reminder')
        
        if template_type == 'thank_you':
            template = email_auto.get_thank_you_email_template(
                company=request.args.get('company', 'Company'),
                role=request.args.get('role', 'Role'),
                interviewer_name=request.args.get('interviewer', 'Interviewer'),
                interview_date=request.args.get('date', ''),
                talking_points=request.args.get('talking_points', '')
            )
        elif template_type == 'follow_up':
            template = email_auto.get_follow_up_email_template(
                company=request.args.get('company', 'Company'),
                role=request.args.get('role', 'Role'),
                status=request.args.get('status', 'pending')
            )
        else:  # reminder
            template = email_auto.get_interview_reminder_template(
                company=request.args.get('company', 'Company'),
                role=request.args.get('role', 'Role'),
                interview_type=request.args.get('type', 'technical'),
                scheduled_at=request.args.get('scheduled_at', ''),
                interviewer=request.args.get('interviewer', 'Interviewer'),
                location=request.args.get('location', 'Virtual')
            )
        
        return jsonify({
            "success": True,
            "template": template
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interviews/stats', methods=['GET'])
def get_interview_stats():
    """Get interview statistics"""
    try:
        from interviews.interview_prep import InterviewPrep
        
        interview_prep = InterviewPrep(str(Path(__file__).parent.parent / "interviews"))
        stats = interview_prep.get_interview_stats()
        
        return jsonify({
            "success": True,
            "statistics": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------
# Error Handlers
# -------------------------

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------
# Run
# -------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("JOB APPLICATION DASHBOARD")
    print("=" * 60)
    print("Starting Flask dashboard on http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
