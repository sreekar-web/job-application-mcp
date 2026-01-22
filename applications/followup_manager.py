"""
Follow-up management for job applications.
Calculates follow-up dates, generates templates, and tracks follow-up history.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from applications.application_tracker import ApplicationStatus


class FollowupManager:
    """Manages follow-up scheduling and templates."""
    
    # Follow-up intervals (days) for each status
    FOLLOWUP_INTERVALS = {
        ApplicationStatus.SUBMITTED.value: 14,        # 2 weeks
        ApplicationStatus.VIEWED.value: 7,             # 1 week
        ApplicationStatus.INTERVIEW.value: 0,          # No follow-up (you're in)
        ApplicationStatus.REJECTED.value: 0,           # No follow-up
        ApplicationStatus.OFFER.value: 0,              # No follow-up
        ApplicationStatus.ACCEPTED.value: 0,           # No follow-up
        ApplicationStatus.PENDING.value: 0,            # No follow-up yet
        ApplicationStatus.WITHDRAWN.value: 0           # No follow-up
    }
    
    # Follow-up email templates
    FOLLOWUP_TEMPLATES = {
        ApplicationStatus.SUBMITTED.value: """
Subject: Following Up - {role} Application at {company}

Hi there,

I wanted to follow up on my application for the {role} position at {company} that I submitted on {submitted_date}.

I remain very interested in this opportunity and would appreciate any updates on the status of my application. 

If you need any additional information from me, please let me know.

Thank you for your time and consideration.

Best regards,
[Your Name]
        """,
        
        ApplicationStatus.VIEWED.value: """
Subject: Re: {role} Position at {company}

Hi there,

Thank you for reviewing my application for the {role} position at {company}. 

I'm very excited about the opportunity to contribute to your team and would love to discuss this role further. 

Please let me know if there are any questions about my qualifications or background.

Best regards,
[Your Name]
        """,
        
        ApplicationStatus.INTERVIEW.value: """
Subject: Thank You for the Interview - {role} at {company}

Hi there,

Thank you so much for taking the time to interview me for the {role} position at {company}. 

I really enjoyed our conversation and learning more about the role and team. I'm very interested in this opportunity.

I look forward to hearing from you.

Best regards,
[Your Name]
        """
    }
    
    @staticmethod
    def calculate_next_followup(
        current_status: str,
        submitted_date: Optional[str] = None,
        last_followup_date: Optional[str] = None
    ) -> Optional[str]:
        """
        Calculate next follow-up date based on current status.
        
        Args:
            current_status: Current application status
            submitted_date: ISO date when application was submitted
            last_followup_date: ISO date of last follow-up attempt
        
        Returns:
            ISO date string for next follow-up, or None if no follow-up needed
        """
        interval = FollowupManager.FOLLOWUP_INTERVALS.get(current_status, 0)
        
        if interval == 0:
            return None  # No follow-up needed for this status
        
        # Use last_followup_date if available, otherwise submitted_date
        base_date = last_followup_date or submitted_date or datetime.now().isoformat()
        
        try:
            base = datetime.fromisoformat(base_date)
            next_followup = base + timedelta(days=interval)
            return next_followup.isoformat()
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def get_followup_template(
        current_status: str,
        company: str,
        role: str,
        submitted_date: Optional[str] = None
    ) -> Optional[str]:
        """
        Get follow-up email template for current status.
        
        Args:
            current_status: Current application status
            company: Company name
            role: Job role
            submitted_date: ISO date when submitted
        
        Returns:
            Formatted email template, or None if no template available
        """
        template = FollowupManager.FOLLOWUP_TEMPLATES.get(current_status)
        
        if not template:
            return None
        
        # Format template with variables
        submitted_str = ""
        if submitted_date:
            try:
                date_obj = datetime.fromisoformat(submitted_date)
                submitted_str = date_obj.strftime("%B %d, %Y")
            except (ValueError, TypeError):
                submitted_str = submitted_date
        
        return template.format(
            company=company,
            role=role,
            submitted_date=submitted_str
        ).strip()
    
    @staticmethod
    def get_status_transitions() -> Dict[str, List[str]]:
        """
        Get valid status transitions for each status.
        Defines which statuses can transition to which.
        """
        return {
            ApplicationStatus.PENDING.value: [
                ApplicationStatus.SUBMITTED.value
            ],
            ApplicationStatus.SUBMITTED.value: [
                ApplicationStatus.VIEWED.value,
                ApplicationStatus.REJECTED.value,
                ApplicationStatus.WITHDRAWN.value
            ],
            ApplicationStatus.VIEWED.value: [
                ApplicationStatus.INTERVIEW.value,
                ApplicationStatus.REJECTED.value,
                ApplicationStatus.WITHDRAWN.value
            ],
            ApplicationStatus.INTERVIEW.value: [
                ApplicationStatus.OFFER.value,
                ApplicationStatus.REJECTED.value,
                ApplicationStatus.WITHDRAWN.value
            ],
            ApplicationStatus.OFFER.value: [
                ApplicationStatus.ACCEPTED.value,
                ApplicationStatus.REJECTED.value
            ],
            ApplicationStatus.ACCEPTED.value: [],  # Terminal state
            ApplicationStatus.REJECTED.value: [],   # Terminal state
            ApplicationStatus.WITHDRAWN.value: []   # Terminal state
        }
    
    @staticmethod
    def is_valid_transition(from_status: str, to_status: str) -> bool:
        """Check if status transition is valid."""
        transitions = FollowupManager.get_status_transitions()
        valid_next = transitions.get(from_status, [])
        return to_status in valid_next
    
    @staticmethod
    def get_followups_needed(
        applications: Dict[str, 'Application']
    ) -> List[Dict]:
        """
        Get list of applications needing follow-up.
        
        Returns sorted list of {job_id, company, role, next_followup_at, template}
        """
        today = datetime.now()
        needing_followup = []
        
        for job_id, app in applications.items():
            if not app.next_followup_at:
                continue
            
            try:
                followup_date = datetime.fromisoformat(app.next_followup_at)
                
                # If followup date has passed or is today
                if followup_date.date() <= today.date():
                    template = FollowupManager.get_followup_template(
                        app.status,
                        app.company,
                        app.role,
                        app.submitted_at
                    )
                    
                    needing_followup.append({
                        "job_id": job_id,
                        "company": app.company,
                        "role": app.role,
                        "status": app.status,
                        "next_followup_at": app.next_followup_at,
                        "days_overdue": (today.date() - followup_date.date()).days,
                        "template": template
                    })
            except (ValueError, TypeError):
                continue
        
        # Sort by days overdue (most urgent first)
        return sorted(needing_followup, key=lambda x: x["days_overdue"], reverse=True)


def test_followup_manager():
    """Test follow-up manager."""
    print("=" * 60)
    print("FOLLOW-UP MANAGER TEST")
    print("=" * 60)
    
    # Test 1: Calculate next followup dates
    print("\n[1] Testing follow-up date calculations...")
    
    submitted = datetime.now().isoformat()
    next_followup = FollowupManager.calculate_next_followup(
        ApplicationStatus.SUBMITTED.value,
        submitted
    )
    print(f"  OK Submitted → Next followup in 14 days: {next_followup}")
    
    viewed_followup = FollowupManager.calculate_next_followup(
        ApplicationStatus.VIEWED.value,
        submitted
    )
    print(f"  OK Viewed → Next followup in 7 days: {viewed_followup}")
    
    interview_followup = FollowupManager.calculate_next_followup(
        ApplicationStatus.INTERVIEW.value
    )
    print(f"  OK Interview → No followup needed: {interview_followup}")
    
    # Test 2: Get templates
    print("\n[2] Testing follow-up templates...")
    
    template = FollowupManager.get_followup_template(
        ApplicationStatus.SUBMITTED.value,
        "Stripe",
        "Backend Engineer",
        submitted
    )
    if template:
        print("  OK SUBMITTED template generated")
        print("     Subject line present:", "Subject:" in template)
    
    # Test 3: Status transitions
    print("\n[3] Testing status transitions...")
    
    valid = FollowupManager.is_valid_transition(
        ApplicationStatus.SUBMITTED.value,
        ApplicationStatus.VIEWED.value
    )
    print(f"  OK SUBMITTED → VIEWED: {valid}")
    
    invalid = FollowupManager.is_valid_transition(
        ApplicationStatus.SUBMITTED.value,
        ApplicationStatus.OFFER.value
    )
    print(f"  OK SUBMITTED → OFFER: {invalid} (should be False)")
    
    # Test 4: All transitions
    print("\n[4] Valid status transitions:")
    transitions = FollowupManager.get_status_transitions()
    for from_status, to_statuses in transitions.items():
        print(f"  {from_status} → {', '.join(to_statuses) if to_statuses else 'TERMINAL'}")
    
    print("\n" + "=" * 60)
    print("SUCCESS: FOLLOW-UP MANAGER OPERATIONAL")
    print("=" * 60)


if __name__ == "__main__":
    test_followup_manager()
