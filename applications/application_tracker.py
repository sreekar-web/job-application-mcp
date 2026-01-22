"""
Application tracking and status management.
Tracks submitted applications, follow-ups, and application history.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ApplicationStatus(Enum):
    """Application status enum."""
    PENDING = "pending"  # Not yet submitted
    SUBMITTED = "submitted"  # Successfully applied
    VIEWED = "viewed"  # Recruiter viewed profile
    INTERVIEW = "interview"  # Offered interview
    REJECTED = "rejected"  # Application rejected
    OFFER = "offer"  # Job offer received
    ACCEPTED = "accepted"  # Offer accepted
    WITHDRAWN = "withdrawn"  # Application withdrawn


@dataclass
class StatusChange:
    """Record of a status change."""
    status: str
    timestamp: str
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Application:
    """Single application record with status tracking and follow-up dates."""
    job_id: str
    company: str
    role: str
    apply_url: str
    status: str = ApplicationStatus.PENDING.value
    submitted_at: Optional[str] = None
    filled_fields: Dict[str, str] = None
    ambiguous_fields_filled: Dict[str, str] = None
    notes: str = ""
    status_history: List = None  # List of StatusChange dicts
    last_followup_at: Optional[str] = None
    next_followup_at: Optional[str] = None
    
    def __post_init__(self):
        if self.filled_fields is None:
            self.filled_fields = {}
        if self.ambiguous_fields_filled is None:
            self.ambiguous_fields_filled = {}
        if self.status_history is None:
            self.status_history = []
        if not self.submitted_at and self.status == ApplicationStatus.SUBMITTED.value:
            self.submitted_at = datetime.now().isoformat()
    
    def add_status_change(self, new_status: str, notes: str = ""):
        """Record a status change in history."""
        change = {
            "status": new_status,
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        }
        self.status_history.append(change)
        self.status = new_status
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ApplicationTracker:
    """Manages application history and tracking."""
    
    def __init__(self, applications_dir: Path = None):
        self.applications_dir = applications_dir or Path(__file__).parent.parent / "applications"
        self.applications_dir.mkdir(exist_ok=True)
        
        self.csv_path = self.applications_dir / "applications.csv"
        self.json_path = self.applications_dir / "applications.json"
        
        self._ensure_csv_exists()
        self.applications: Dict[str, Application] = self._load_applications()
    
    def _ensure_csv_exists(self):
        """Ensure CSV file exists with headers."""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'job_id', 'company', 'role', 'apply_url', 'status',
                    'submitted_at', 'filled_fields', 'ambiguous_fields_filled', 
                    'status_history', 'last_followup_at', 'next_followup_at', 'notes'
                ])
                writer.writeheader()
    
    def _load_applications(self) -> Dict[str, Application]:
        """Load existing applications from CSV."""
        applications = {}
        
        if not self.csv_path.exists():
            return applications
        
        try:
            with open(self.csv_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row.get('job_id'):
                        continue
                    
                    # Parse JSON fields
                    filled_fields = {}
                    ambiguous_fields = {}
                    
                    try:
                        if row.get('filled_fields'):
                            filled_fields = json.loads(row['filled_fields'])
                    except json.JSONDecodeError:
                        pass
                    
                    try:
                        if row.get('ambiguous_fields_filled'):
                            ambiguous_fields = json.loads(row['ambiguous_fields_filled'])
                    except json.JSONDecodeError:
                        pass
                    
                    app = Application(
                        job_id=row['job_id'],
                        company=row['company'],
                        role=row['role'],
                        apply_url=row['apply_url'],
                        status=row.get('status', ApplicationStatus.PENDING.value),
                        submitted_at=row.get('submitted_at'),
                        filled_fields=filled_fields,
                        ambiguous_fields_filled=ambiguous_fields,
                        notes=row.get('notes', ''),
                        last_followup_at=row.get('last_followup_at'),
                        next_followup_at=row.get('next_followup_at')
                    )
                    
                    # Load status history
                    try:
                        if row.get('status_history'):
                            app.status_history = json.loads(row['status_history'])
                    except json.JSONDecodeError:
                        pass
                    
                    applications[row['job_id']] = app
        except Exception as e:
            print(f"Error loading applications: {e}")
        
        return applications
    
    def add_application(
        self,
        job_id: str,
        company: str,
        role: str,
        apply_url: str,
        status: str = ApplicationStatus.PENDING.value
    ) -> Application:
        """Add new application record."""
        app = Application(
            job_id=job_id,
            company=company,
            role=role,
            apply_url=apply_url,
            status=status,
            submitted_at=datetime.now().isoformat() if status == ApplicationStatus.SUBMITTED.value else None
        )
        self.applications[job_id] = app
        self._save_application(app)
        return app
    
    def update_application(
        self,
        job_id: str,
        status: Optional[str] = None,
        filled_fields: Optional[Dict] = None,
        ambiguous_fields_filled: Optional[Dict] = None,
        notes: Optional[str] = None,
        last_followup_at: Optional[str] = None,
        next_followup_at: Optional[str] = None
    ) -> Optional[Application]:
        """Update existing application."""
        if job_id not in self.applications:
            return None
        
        app = self.applications[job_id]
        
        if status:
            # Record status change in history
            status_notes = notes or f"Status changed to {status}"
            app.add_status_change(status, status_notes)
            
            if status == ApplicationStatus.SUBMITTED.value and not app.submitted_at:
                app.submitted_at = datetime.now().isoformat()
        
        if filled_fields:
            app.filled_fields.update(filled_fields)
        
        if ambiguous_fields_filled:
            app.ambiguous_fields_filled.update(ambiguous_fields_filled)
        
        if notes and not status:  # If notes provided without status change
            app.notes = notes
        
        if last_followup_at:
            app.last_followup_at = last_followup_at
        
        if next_followup_at:
            app.next_followup_at = next_followup_at
        
        self._save_application(app)
        return app
    
    def _save_application(self, app: Application):
        """Save single application to CSV."""
        try:
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'job_id', 'company', 'role', 'apply_url', 'status',
                    'submitted_at', 'filled_fields', 'ambiguous_fields_filled', 
                    'status_history', 'last_followup_at', 'next_followup_at', 'notes'
                ])
                
                # Check if this job_id already exists (update vs insert)
                existing_ids = {app_id for app_id in self.applications.keys()}
                
                if app.job_id not in existing_ids or not self.csv_path.stat().st_size > 100:
                    # Insert new row
                    writer.writerow({
                        'job_id': app.job_id,
                        'company': app.company,
                        'role': app.role,
                        'apply_url': app.apply_url,
                        'status': app.status,
                        'submitted_at': app.submitted_at or '',
                        'filled_fields': json.dumps(app.filled_fields),
                        'ambiguous_fields_filled': json.dumps(app.ambiguous_fields_filled),
                        'status_history': json.dumps(app.status_history),
                        'last_followup_at': app.last_followup_at or '',
                        'next_followup_at': app.next_followup_at or '',
                        'notes': app.notes
                    })
        except Exception as e:
            print(f"Error saving application: {e}")
    
    def get_application(self, job_id: str) -> Optional[Application]:
        """Get application by job ID."""
        return self.applications.get(job_id)
    
    def get_applications_by_status(self, status: str) -> List[Application]:
        """Get all applications with specific status."""
        return [app for app in self.applications.values() if app.status == status]
    
    def get_summary(self) -> Dict:
        """Get summary statistics."""
        total = len(self.applications)
        submitted = len(self.get_applications_by_status(ApplicationStatus.SUBMITTED.value))
        interviews = len(self.get_applications_by_status(ApplicationStatus.INTERVIEW.value))
        offers = len(self.get_applications_by_status(ApplicationStatus.OFFER.value))
        rejected = len(self.get_applications_by_status(ApplicationStatus.REJECTED.value))
        
        # Count applications needing follow-up
        today = datetime.now().date()
        needing_followup = 0
        for app in self.applications.values():
            if app.next_followup_at:
                followup_date = datetime.fromisoformat(app.next_followup_at).date()
                if followup_date <= today:
                    needing_followup += 1
        
        return {
            "total_applications": total,
            "submitted": submitted,
            "interviews": interviews,
            "offers": offers,
            "rejected": rejected,
            "pending": total - submitted,
            "success_rate": f"{(interviews / submitted * 100):.1f}%" if submitted > 0 else "N/A",
            "needing_followup": needing_followup
        }


def test_tracker():
    """Test application tracker."""
    tracker = ApplicationTracker()
    
    # Add sample applications
    app1 = tracker.add_application(
        job_id="job-001",
        company="TechCorp",
        role="Backend Engineer",
        apply_url="https://example.com/apply/001"
    )
    print(f"Added: {app1.company} - {app1.role}")
    
    # Update status
    tracker.update_application(
        job_id="job-001",
        status=ApplicationStatus.SUBMITTED.value,
        filled_fields={"email": "user@example.com"},
        notes="Application submitted successfully"
    )
    
    # Get summary
    summary = tracker.get_summary()
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    test_tracker()
