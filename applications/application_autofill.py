"""
Application autofill logic.
Extracts user data from master profile and applies to job applications.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class UserProfile:
    """User profile extracted from master resume data."""
    first_name: str
    last_name: str
    user_email: str
    phone_number: str
    linkedin_url: str
    portfolio_url: Optional[str] = None
    preferred_location: str = "Remote"
    years_experience: int = 0
    core_skills: List[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ApplicationAutofiller:
    """Handles autofill logic for job applications."""
    
    def __init__(self, master_resume_path: Path = None):
        self.master_resume_path = master_resume_path or Path(__file__).parent.parent / "resumes" / "master"
        self.user_profile = self._extract_user_profile()
    
    def _extract_user_profile(self) -> UserProfile:
        """Extract user contact info from master resume."""
        # Load master resume data
        core_exp_path = self.master_resume_path / "core_experience.json"
        skills_path = self.master_resume_path / "skills_inventory.json"
        
        user_data = {}
        
        try:
            if core_exp_path.exists():
                core_exp = json.loads(core_exp_path.read_text())
                # Handle both array and object formats
                if isinstance(core_exp, list) and len(core_exp) > 0:
                    user_data = core_exp[0].get("contact_info", {})
                elif isinstance(core_exp, dict):
                    user_data = core_exp.get("contact_info", {})
        except Exception as e:
            pass  # Silently continue if no contact info
        
        # Extract years of experience from core experience
        years_exp = 0
        try:
            if core_exp_path.exists():
                core_exp = json.loads(core_exp_path.read_text())
                # Count job experiences
                if isinstance(core_exp, list) and len(core_exp) > 0:
                    years_exp = len(core_exp[0].get("job_experience", []))
                elif isinstance(core_exp, dict):
                    years_exp = len(core_exp.get("experience", []))
        except Exception:
            pass
        
        # Extract core skills
        core_skills = []
        try:
            if skills_path.exists():
                skills = json.loads(skills_path.read_text())
                core_skills = list(skills.get("core_skills", {}).keys())[:10]  # Top 10
        except Exception:
            pass
        
        return UserProfile(
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            user_email=user_data.get("email", ""),
            phone_number=user_data.get("phone", ""),
            linkedin_url=user_data.get("linkedin", ""),
            portfolio_url=user_data.get("portfolio", ""),
            preferred_location=user_data.get("location", "Remote"),
            years_experience=years_exp,
            core_skills=core_skills or []
        )
    
    def get_autofill_data(self) -> Dict[str, str]:
        """Get autofill data dictionary ready for form filling."""
        profile = self.user_profile
        return {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "user_email": profile.user_email,
            "phone_number": profile.phone_number,
            "linkedin_url": profile.linkedin_url,
            "portfolio_url": profile.portfolio_url or "",
            "preferred_location": profile.preferred_location,
            "years_experience": str(profile.years_experience),
        }
    
    def map_job_requirements_to_profile(
        self,
        job_description: str,
        role_family: str
    ) -> Dict[str, Optional[str]]:
        """
        Analyze job requirements and suggest autofill values.
        Returns mapping of potential ambiguous fields to suggested values.
        """
        suggestions = {}
        
        jd_lower = job_description.lower()
        
        # Check for visa sponsorship question
        if any(keyword in jd_lower for keyword in ["visa", "sponsorship", "work authorization", "eligible to work"]):
            suggestions["visa_sponsorship"] = None  # Requires user input
        
        # Check for relocation question
        if any(keyword in jd_lower for keyword in ["relocation", "willing to relocate", "remote", "on-site"]):
            suggestions["willing_to_relocate"] = None  # Requires user input
        
        # Check for salary expectations
        if any(keyword in jd_lower for keyword in ["salary", "compensation", "salary range"]):
            suggestions["salary_expectations"] = None  # Requires user input
        
        # Check for contract type
        if any(keyword in jd_lower for keyword in ["contract", "permanent", "temp", "freelance"]):
            suggestions["contract_type"] = None  # Requires user input
        
        # Check for notice period
        if any(keyword in jd_lower for keyword in ["notice", "availability", "start date"]):
            suggestions["notice_period"] = None  # Requires user input
        
        return suggestions
    
    def extract_resume_file_path(self, role_variant: Dict) -> str:
        """Get resume file path for attachment. Returns path to generated DOCX."""
        # For now, return a placeholder - in real use, would point to Stage 4 output
        return str(self.master_resume_path.parent / f"{role_variant.get('role_family', 'resume')}.docx")
    
    def validate_autofill_data(self, data: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate that autofill data is complete and valid.
        Returns (is_valid, list_of_missing_fields).
        """
        required_fields = ["first_name", "last_name", "user_email", "phone_number"]
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        # Validate email format
        if data.get("user_email"):
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, data["user_email"]):
                missing_fields.append("user_email (invalid format)")
        
        # Validate phone format
        if data.get("phone_number"):
            phone_pattern = r"^[\d\s\-\+\(\)]{10,}$"
            if not re.match(phone_pattern, data["phone_number"]):
                missing_fields.append("phone_number (invalid format)")
        
        return len(missing_fields) == 0, missing_fields
    
    def prepare_application_payload(
        self,
        job: Dict,
        role_variant: Dict,
        additional_data: Dict = None
    ) -> Dict:
        """
        Prepare complete payload for application submission.
        Combines autofill data with job-specific and user-provided data.
        """
        autofill_data = self.get_autofill_data()
        
        # Add job-specific resume
        autofill_data["resume_path"] = self.extract_resume_file_path(role_variant)
        
        # Merge with additional user-provided data
        if additional_data:
            autofill_data.update(additional_data)
        
        return {
            "job_id": job.get("id"),
            "company": job.get("company"),
            "role": job.get("role"),
            "apply_url": job.get("apply_url"),
            "autofill_data": autofill_data,
            "ambiguous_fields": self.map_job_requirements_to_profile(
                job.get("job_description", ""),
                role_variant.get("role_family", "")
            ),
            "prepared_at": datetime.now().isoformat()
        }


def test_autofiller():
    """Test autofill logic."""
    filler = ApplicationAutofiller()
    
    print("=== User Profile ===")
    profile = filler.user_profile
    print(f"Name: {profile.first_name} {profile.last_name}")
    print(f"Email: {profile.user_email}")
    print(f"Phone: {profile.phone_number}")
    print(f"Experience: {profile.years_experience} years")
    print(f"Skills: {', '.join(profile.core_skills[:5])}")
    
    print("\n=== Autofill Data ===")
    autofill = filler.get_autofill_data()
    print(json.dumps(autofill, indent=2))
    
    print("\n=== Sample Job ===")
    sample_job = {
        "id": "test-123",
        "company": "TechCorp",
        "role": "Backend Engineer",
        "job_description": "We are looking for a backend engineer. Visa sponsorship available. Must be willing to relocate to San Francisco.",
    }
    
    requirements = filler.map_job_requirements_to_profile(sample_job["job_description"], "backend_engineer")
    print(f"Detected requirements: {list(requirements.keys())}")
    
    print("\n=== Validation ===")
    is_valid, missing = filler.validate_autofill_data(autofill)
    print(f"Valid: {is_valid}")
    if missing:
        print(f"Missing: {missing}")


if __name__ == "__main__":
    test_autofiller()
