"""
Interview Prep Manager - Core Module (Stage 8)
Manages interview preparation, scheduling, and follow-ups
"""

from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional
from enum import Enum


class InterviewType(Enum):
    """Types of interviews"""
    PHONE_SCREEN = "phone_screen"
    VIDEO_INTERVIEW = "video_interview"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    ON_SITE = "on_site"
    PANEL = "panel"
    FINAL_ROUND = "final_round"
    DEBRIEF = "debrief"


class InterviewStatus(Enum):
    """Interview statuses"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    REMINDER_SENT = "reminder_sent"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class InterviewPrep:
    """Main interview preparation manager"""
    
    def __init__(self, interviews_dir: str = "interviews"):
        """Initialize interview prep manager"""
        self.interviews_dir = Path(interviews_dir)
        self.interviews_file = self.interviews_dir / "interviews.json"
        self.prep_notes_dir = self.interviews_dir / "prep_notes"
        self.prep_notes_dir.mkdir(parents=True, exist_ok=True)
        self.interviews_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.interviews_file.exists():
            self._init_interviews_file()
    
    def _init_interviews_file(self):
        """Initialize empty interviews JSON file"""
        data = {
            "interviews": [],
            "templates": {
                "interview_questions": [],
                "company_research": [],
                "preparation_checklist": []
            },
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        with open(self.interviews_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _read_interviews(self) -> Dict:
        """Read interviews from JSON file"""
        if not self.interviews_file.exists():
            self._init_interviews_file()
        
        with open(self.interviews_file, 'r') as f:
            return json.load(f)
    
    def _write_interviews(self, data: Dict):
        """Write interviews to JSON file"""
        data['metadata']['last_updated'] = datetime.now().isoformat()
        with open(self.interviews_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def schedule_interview(
        self,
        job_id: str,
        company: str,
        role: str,
        interview_type: str,
        scheduled_at: str,
        interviewer: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """Schedule a new interview"""
        data = self._read_interviews()
        
        interview = {
            "id": f"int_{job_id}_{len(data['interviews'])}",
            "job_id": job_id,
            "company": company,
            "role": role,
            "interview_type": interview_type,
            "scheduled_at": scheduled_at,
            "interviewer": interviewer or "TBD",
            "location": location or "Virtual (TBD)",
            "status": InterviewStatus.SCHEDULED.value,
            "notes": notes or "",
            "created_at": datetime.now().isoformat(),
            "reminders_sent": [],
            "feedback": None,
            "preparation_complete": False
        }
        
        data['interviews'].append(interview)
        self._write_interviews(data)
        
        return interview
    
    def get_interviews_by_job(self, job_id: str) -> List[Dict]:
        """Get all interviews for a job"""
        data = self._read_interviews()
        return [i for i in data['interviews'] if i['job_id'] == job_id]
    
    def get_upcoming_interviews(self, days: int = 7) -> List[Dict]:
        """Get upcoming interviews within N days"""
        data = self._read_interviews()
        interviews = []
        
        for interview in data['interviews']:
            if interview['status'] == InterviewStatus.CANCELLED.value:
                continue
            
            scheduled = datetime.fromisoformat(interview['scheduled_at'])
            now = datetime.now()
            
            if now <= scheduled <= now + timedelta(days=days):
                interviews.append(interview)
        
        return sorted(interviews, key=lambda x: x['scheduled_at'])
    
    def update_interview_status(
        self,
        interview_id: str,
        new_status: str,
        feedback: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """Update interview status"""
        data = self._read_interviews()
        
        for interview in data['interviews']:
            if interview['id'] == interview_id:
                interview['status'] = new_status
                if feedback:
                    interview['feedback'] = feedback
                if notes:
                    interview['notes'] = notes
                self._write_interviews(data)
                return interview
        
        raise ValueError(f"Interview {interview_id} not found")
    
    def log_interview_reminder(self, interview_id: str, reminder_type: str = "email"):
        """Log that a reminder was sent"""
        data = self._read_interviews()
        
        for interview in data['interviews']:
            if interview['id'] == interview_id:
                interview['reminders_sent'].append({
                    "type": reminder_type,
                    "sent_at": datetime.now().isoformat()
                })
                self._write_interviews(data)
                return interview
        
        raise ValueError(f"Interview {interview_id} not found")
    
    def mark_prep_complete(self, interview_id: str) -> Dict:
        """Mark interview preparation as complete"""
        data = self._read_interviews()
        
        for interview in data['interviews']:
            if interview['id'] == interview_id:
                interview['preparation_complete'] = True
                self._write_interviews(data)
                return interview
        
        raise ValueError(f"Interview {interview_id} not found")
    
    def save_prep_notes(self, interview_id: str, notes: str) -> str:
        """Save preparation notes for an interview"""
        notes_file = self.prep_notes_dir / f"{interview_id}_prep.md"
        
        content = f"""# Interview Prep Notes - {interview_id}

**Prepared At**: {datetime.now().isoformat()}

## Notes

{notes}

---

## Resources Used
- company_research.md
- role_skills.md
- technical_prep.md
- behavioral_questions.md
"""
        
        with open(notes_file, 'w') as f:
            f.write(content)
        
        return str(notes_file)
    
    def get_prep_notes(self, interview_id: str) -> Optional[str]:
        """Get preparation notes for an interview"""
        notes_file = self.prep_notes_dir / f"{interview_id}_prep.md"
        
        if notes_file.exists():
            with open(notes_file, 'r') as f:
                return f.read()
        
        return None
    
    def get_all_interviews(self, status: Optional[str] = None) -> List[Dict]:
        """Get all interviews, optionally filtered by status"""
        data = self._read_interviews()
        interviews = data['interviews']
        
        if status:
            interviews = [i for i in interviews if i['status'] == status]
        
        return sorted(interviews, key=lambda x: x['scheduled_at'], reverse=True)
    
    def get_interview_stats(self) -> Dict:
        """Get interview statistics"""
        data = self._read_interviews()
        interviews = data['interviews']
        
        stats = {
            "total_interviews": len(interviews),
            "by_type": {},
            "by_status": {},
            "by_company": {},
            "upcoming_count": len(self.get_upcoming_interviews(7)),
            "completed": 0,
            "cancelled": 0,
            "preparation_complete": 0
        }
        
        for interview in interviews:
            # By type
            itype = interview['interview_type']
            stats['by_type'][itype] = stats['by_type'].get(itype, 0) + 1
            
            # By status
            status = interview['status']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # By company
            company = interview['company']
            stats['by_company'][company] = stats['by_company'].get(company, 0) + 1
            
            # Counters
            if status == InterviewStatus.COMPLETED.value:
                stats['completed'] += 1
            if status == InterviewStatus.CANCELLED.value:
                stats['cancelled'] += 1
            if interview['preparation_complete']:
                stats['preparation_complete'] += 1
        
        return stats
