"""
Job Application Assistance System

- Stage 5: Application Assistance (browser_handler, application_autofill, application_tracker)
- Stage 6: Tracking & Follow-ups (followup_manager)
"""

from .browser_handler import BrowserHandler, FormField, ApplicationResult
from .application_autofill import ApplicationAutofiller, UserProfile
from .application_tracker import ApplicationTracker, Application, ApplicationStatus, StatusChange
from .followup_manager import FollowupManager

__all__ = [
    "BrowserHandler",
    "FormField",
    "ApplicationResult",
    "ApplicationAutofiller",
    "UserProfile",
    "ApplicationTracker",
    "Application",
    "ApplicationStatus",
    "StatusChange",
    "FollowupManager"
]
