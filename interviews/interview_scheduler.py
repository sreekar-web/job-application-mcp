"""
Interview Scheduler Module (Stage 8)
Manages interview scheduling, reminders, and calendar integration
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class InterviewScheduler:
    """Interview scheduling and reminder management"""
    
    # Default reminder timings (in hours before interview)
    DEFAULT_REMINDERS = {
        "phone_screen": [24, 2],          # 1 day and 2 hours before
        "video_interview": [24, 2],
        "technical": [48, 24, 2],         # 2 days, 1 day, 2 hours before
        "behavioral": [48, 24, 2],
        "on_site": [72, 24, 2],           # 3 days, 1 day, 2 hours before
        "panel": [48, 24, 2],
        "final_round": [72, 24],
        "debrief": [24]
    }
    
    def __init__(self):
        """Initialize interview scheduler"""
        self.scheduled_reminders = {}
        self.reminder_history = []
    
    def calculate_reminder_times(
        self,
        interview_id: str,
        scheduled_at: str,
        interview_type: str
    ) -> List[Dict]:
        """Calculate when reminders should be sent
        
        Returns:
            List of reminder times with dates
        """
        
        try:
            scheduled = datetime.fromisoformat(scheduled_at)
            reminders = []
            
            # Get default reminders for this interview type
            hours_list = self.DEFAULT_REMINDERS.get(
                interview_type,
                self.DEFAULT_REMINDERS['phone_screen']
            )
            
            for hours_before in hours_list:
                reminder_time = scheduled - timedelta(hours=hours_before)
                
                # Don't schedule reminders in the past
                if reminder_time > datetime.now():
                    reminders.append({
                        "interview_id": interview_id,
                        "reminder_type": self._get_reminder_type(hours_before),
                        "hours_before": hours_before,
                        "scheduled_for": reminder_time.isoformat(),
                        "status": "pending"
                    })
            
            return reminders
        
        except Exception as e:
            return []
    
    def _get_reminder_type(self, hours_before: int) -> str:
        """Get human-readable reminder type"""
        if hours_before >= 48:
            return f"{hours_before // 24} day reminder"
        elif hours_before > 24:
            return f"{hours_before - 24} hours before"
        elif hours_before >= 2:
            return f"{hours_before} hour reminder"
        else:
            return "last minute reminder"
    
    def schedule_reminders(
        self,
        interview_id: str,
        reminders: List[Dict]
    ) -> List[Dict]:
        """Schedule reminders for an interview"""
        self.scheduled_reminders[interview_id] = reminders
        return reminders
    
    def get_pending_reminders(self) -> List[Dict]:
        """Get all reminders that should be sent now"""
        pending = []
        now = datetime.now()
        
        for interview_id, reminders in self.scheduled_reminders.items():
            for reminder in reminders:
                if reminder['status'] == 'pending':
                    reminder_time = datetime.fromisoformat(reminder['scheduled_for'])
                    
                    # Send if we're within 5 minutes of scheduled time
                    time_diff = (reminder_time - now).total_seconds() / 60
                    if -5 <= time_diff <= 5:
                        pending.append({
                            **reminder,
                            "should_send": True
                        })
        
        return pending
    
    def mark_reminder_sent(self, interview_id: str, reminder_type: str):
        """Mark a reminder as sent"""
        if interview_id in self.scheduled_reminders:
            for reminder in self.scheduled_reminders[interview_id]:
                if reminder['reminder_type'] == reminder_type:
                    reminder['status'] = 'sent'
                    reminder['sent_at'] = datetime.now().isoformat()
    
    def get_calendar_events(self, days: int = 30) -> List[Dict]:
        """Get upcoming interviews for calendar display
        
        Format compatible with calendar integrations
        """
        # This would be populated from interview_prep.get_upcoming_interviews()
        # Returning structure for reference
        return [
            {
                "title": "{company} - {role} ({type})",
                "description": "Interview with {interviewer}",
                "start": "{scheduled_at}",
                "end": "{scheduled_at + 1 hour}",
                "location": "{location}",
                "reminder": 30,  # minutes
                "type": "interview"
            }
        ]
    
    def reschedule_interview(
        self,
        interview_id: str,
        new_scheduled_at: str,
        reason: Optional[str] = None
    ) -> Dict:
        """Reschedule an interview to a new time"""
        
        return {
            "interview_id": interview_id,
            "old_time": "original_time",
            "new_time": new_scheduled_at,
            "reason": reason or "Rescheduled",
            "rescheduled_at": datetime.now().isoformat(),
            "new_reminders": "calculated"
        }
    
    def get_interview_prep_checklist(self, interview_type: str) -> List[Dict]:
        """Get pre-interview preparation checklist"""
        
        base_checklist = [
            {"task": "Research the company", "priority": "high"},
            {"task": "Review job description", "priority": "high"},
            {"task": "Prepare STAR examples", "priority": "high"},
            {"task": "Test technology setup", "priority": "high"},
            {"task": "Prepare questions for interviewer", "priority": "medium"},
            {"task": "Review past projects", "priority": "medium"},
            {"task": "Prepare elevator pitch", "priority": "medium"},
            {"task": "Get good sleep night before", "priority": "high"},
            {"task": "Plan route/timing", "priority": "medium"},
            {"task": "Dress appropriately", "priority": "high"}
        ]
        
        # Add type-specific items
        type_specific = {
            "technical": [
                {"task": "Practice coding problems", "priority": "high"},
                {"task": "Review algorithms and data structures", "priority": "high"},
                {"task": "Test online coding environment", "priority": "high"}
            ],
            "behavioral": [
                {"task": "Prepare conflict resolution examples", "priority": "high"},
                {"task": "Prepare leadership examples", "priority": "medium"},
                {"task": "Prepare failure/learning examples", "priority": "high"}
            ],
            "on_site": [
                {"task": "Plan transportation", "priority": "high"},
                {"task": "Check building directions", "priority": "medium"},
                {"task": "Plan outfit (professional attire)", "priority": "high"},
                {"task": "Prepare portfolio/samples", "priority": "medium"}
            ]
        }
        
        checklist = base_checklist.copy()
        if interview_type in type_specific:
            checklist.extend(type_specific[interview_type])
        
        return checklist
    
    def get_interview_tips(self, interview_type: str) -> Dict:
        """Get tips and best practices for interview type"""
        
        tips = {
            "phone_screen": {
                "duration": "15-30 minutes",
                "tips": [
                    "Find a quiet location",
                    "Have your resume visible",
                    "Take notes during the call",
                    "Speak clearly and at moderate pace",
                    "Ask about next steps before hanging up"
                ]
            },
            "video_interview": {
                "duration": "30-60 minutes",
                "tips": [
                    "Test video/audio before the call",
                    "Use professional background or blur",
                    "Make eye contact with camera",
                    "Sit up straight and look engaged",
                    "Good lighting is important"
                ]
            },
            "technical": {
                "duration": "45-90 minutes",
                "tips": [
                    "Code clearly and explain your approach",
                    "Ask clarifying questions",
                    "Think out loud",
                    "Test your code",
                    "Discuss trade-offs and optimization"
                ]
            },
            "behavioral": {
                "duration": "30-60 minutes",
                "tips": [
                    "Use STAR method (Situation, Task, Action, Result)",
                    "Provide specific examples",
                    "Show enthusiasm for the role",
                    "Ask thoughtful questions",
                    "Connect your experience to the role"
                ]
            },
            "on_site": {
                "duration": "4-8 hours",
                "tips": [
                    "Arrive 10-15 minutes early",
                    "Bring multiple copies of resume",
                    "Bring a portfolio/samples if relevant",
                    "Build rapport with each interviewer",
                    "Ask about team dynamics and culture"
                ]
            }
        }
        
        return tips.get(interview_type, tips['phone_screen'])
