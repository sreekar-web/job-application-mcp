"""
Email Automation Module (Stage 8)
Handles interview follow-up emails, reminders, and thank you notes
"""

from datetime import datetime
from typing import Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailAutomation:
    """Email template and sending automation"""
    
    def __init__(self, smtp_config: Optional[Dict] = None):
        """Initialize email automation
        
        Args:
            smtp_config: Dict with smtp_server, port, email, password
                        Optional - for production use only
        """
        self.smtp_config = smtp_config or {}
        self.email_enabled = bool(smtp_config)
    
    def get_interview_reminder_template(
        self,
        company: str,
        role: str,
        interview_type: str,
        scheduled_at: str,
        interviewer: str,
        location: str
    ) -> Dict:
        """Generate interview reminder email template"""
        
        days_until = self._calculate_days(scheduled_at)
        
        subject = f"Interview Reminder: {company} - {role} ({interview_type})"
        
        body = f"""
Hi there!

This is a friendly reminder about your upcoming interview:

**Interview Details:**
- Company: {company}
- Position: {role}
- Interview Type: {interview_type}
- Scheduled For: {scheduled_at}
- Interviewer: {interviewer}
- Location: {location}
- Time Until Interview: {days_until} days

**Pre-Interview Checklist:**
□ Research the company (mission, recent news, products)
□ Review the job description and required skills
□ Prepare STAR method examples for behavioral questions
□ Mock interview practice (if technical)
□ Test your setup (camera, microphone, internet) if virtual
□ Prepare a list of questions to ask the interviewer
□ Get a good night's sleep
□ Plan your route and timing to arrive early

**Helpful Resources:**
- Check your Job Application Dashboard for preparation materials
- Review the company's website and recent news
- Practice common interview questions for this role
- Prepare a 2-minute elevator pitch about yourself

Good luck with your interview! You've got this! 🎯

---
Job Application MCP Dashboard
"""
        
        return {
            "subject": subject,
            "body": body,
            "template_name": "interview_reminder",
            "generated_at": datetime.now().isoformat()
        }
    
    def get_thank_you_email_template(
        self,
        company: str,
        role: str,
        interviewer_name: str,
        interview_date: str,
        talking_points: Optional[str] = None
    ) -> Dict:
        """Generate thank you email template"""
        
        subject = f"Thank You - {company} {role} Interview"
        
        talking_points_section = ""
        if talking_points:
            talking_points_section = f"""
**Key Points Discussed:**
{talking_points}

"""
        
        body = f"""
Hi {interviewer_name},

Thank you so much for taking the time to interview me for the {role} position at {company} on {interview_date}. 

I really enjoyed learning more about the team and the exciting projects you're working on. Our conversation reinforced my interest in this role and the company.

{talking_points_section}
I'm very enthusiastic about this opportunity and would welcome the chance to discuss how my skills and experience can contribute to your team.

Please don't hesitate to reach out if you need any additional information from my end. I look forward to hearing from you.

Best regards,
[Your Name]

---
Job Application MCP Dashboard
"""
        
        return {
            "subject": subject,
            "body": body,
            "template_name": "thank_you_email",
            "generated_at": datetime.now().isoformat()
        }
    
    def get_follow_up_email_template(
        self,
        company: str,
        role: str,
        interview_date: str,
        days_waited: int = 7
    ) -> Dict:
        """Generate follow-up email template"""
        
        subject = f"Following Up - {company} {role} Interview"
        
        body = f"""
Hi Hiring Manager,

I hope this email finds you well. I wanted to follow up on my interview for the {role} position at {company}, which took place on {interview_date}.

I remain very interested in this opportunity and would appreciate any updates on the status of my application. I'm excited about the possibility of joining your team and contributing to [specific project/goal mentioned in interview].

If you need any additional information or references, please let me know. I'm happy to provide whatever you need.

Thank you for your time and consideration.

Best regards,
[Your Name]

---
Job Application MCP Dashboard
"""
        
        return {
            "subject": subject,
            "body": body,
            "template_name": "follow_up_email",
            "generated_at": datetime.now().isoformat(),
            "recommended_timing": f"Send after {days_waited} days of no response"
        }
    
    def get_status_update_email_template(
        self,
        company: str,
        status: str,
        reason: Optional[str] = None
    ) -> Dict:
        """Generate status update email template"""
        
        status_messages = {
            "offer_received": f"🎉 Congratulations! {company} has made you an offer!",
            "rejected": f"Thank you for the update from {company}.",
            "next_round": f"Great news! You've been selected for the next round at {company}.",
            "pending": f"You're still in the interview process at {company}. Stay tuned!"
        }
        
        message = status_messages.get(status, f"Status update from {company}")
        
        body = f"""
{message}

**Status:** {status.replace('_', ' ').title()}
**Company:** {company}
**Timestamp:** {datetime.now().isoformat()}

{f'**Reason:** {reason}' if reason else ''}

---
Keep tracking your applications in the Job Application Dashboard!
"""
        
        return {
            "subject": f"Application Status Update - {company}",
            "body": body,
            "template_name": "status_update",
            "generated_at": datetime.now().isoformat()
        }
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> Dict:
        """Send an email (requires SMTP configuration)
        
        Returns mock success if SMTP not configured (for demo/testing)
        """
        
        if not self.email_enabled:
            # Demo mode - return success without sending
            return {
                "success": True,
                "mode": "demo",
                "message": "Email would be sent in production",
                "to": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            server = smtplib.SMTP(
                self.smtp_config['smtp_server'],
                self.smtp_config['port']
            )
            server.starttls()
            server.login(
                self.smtp_config['email'],
                self.smtp_config['password']
            )
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['email']
            msg['To'] = to_email
            
            mime_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_type))
            
            server.sendmail(
                self.smtp_config['email'],
                to_email,
                msg.as_string()
            )
            server.quit()
            
            return {
                "success": True,
                "mode": "production",
                "message": "Email sent successfully",
                "to": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "to": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_days(self, scheduled_at: str) -> int:
        """Calculate days until scheduled date"""
        try:
            scheduled = datetime.fromisoformat(scheduled_at)
            now = datetime.now()
            delta = (scheduled - now).days
            return max(delta, 0)
        except:
            return 0
