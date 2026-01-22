"""
Coaching Materials Module (Stage 8)
Generates role-specific interview prep materials, questions, and guides
"""

from typing import Dict, List, Optional
import json
from pathlib import Path


class CoachingMaterials:
    """Interview coaching materials generator"""
    
    def __init__(self, materials_dir: str = "interviews/materials"):
        """Initialize coaching materials"""
        self.materials_dir = Path(materials_dir)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
    
    def get_star_method_guide(self) -> Dict:
        """Get STAR method guide for behavioral interviews"""
        return {
            "name": "STAR Method Guide",
            "full_name": "Situation, Task, Action, Result",
            "description": "Framework for answering behavioral interview questions",
            "steps": [
                {
                    "letter": "S",
                    "word": "Situation",
                    "description": "Set the scene - What was the context? When did it happen?",
                    "tips": [
                        "Be specific about the context",
                        "Keep it relevant to the job",
                        "Limit to 20-30 seconds"
                    ]
                },
                {
                    "letter": "T",
                    "word": "Task",
                    "description": "Describe the challenge or goal",
                    "tips": [
                        "Explain your role and responsibility",
                        "Describe what needed to be accomplished",
                        "15-20 seconds maximum"
                    ]
                },
                {
                    "letter": "A",
                    "word": "Action",
                    "description": "Tell what YOU did to address it",
                    "tips": [
                        "Focus on your specific actions",
                        "Explain your thinking and approach",
                        "Highlight skills relevant to the job",
                        "30-45 seconds - longest part"
                    ]
                },
                {
                    "letter": "R",
                    "word": "Result",
                    "description": "Share the outcome and what you learned",
                    "tips": [
                        "Quantify results when possible",
                        "Explain the impact",
                        "What did you learn?",
                        "15-20 seconds"
                    ]
                }
            ],
            "total_time": "2-3 minutes per example",
            "example": {
                "question": "Tell me about a time you overcame a challenge",
                "situation": "At my previous company, we had a tight deadline for a feature release",
                "task": "I was responsible for leading the backend API development",
                "action": "I identified bottlenecks, optimized queries, and coordinated with the frontend team. I wrote clear documentation to reduce integration issues.",
                "result": "Delivered 2 weeks early, reduced load time by 40%, improved team communication"
            }
        }
    
    def get_common_interview_questions(self, role_family: str) -> List[Dict]:
        """Get common interview questions for a role"""
        
        questions = {
            "backend_engineer": [
                {
                    "question": "Design a system that...",
                    "category": "System Design",
                    "difficulty": "hard",
                    "prep_tips": [
                        "Break down requirements",
                        "Discuss trade-offs",
                        "Consider scalability"
                    ]
                },
                {
                    "question": "Explain your approach to testing",
                    "category": "Technical",
                    "difficulty": "medium",
                    "prep_tips": [
                        "Unit tests vs integration tests",
                        "Test coverage goals",
                        "Testing pyramid"
                    ]
                },
                {
                    "question": "Tell me about a bug you fixed",
                    "category": "Behavioral",
                    "difficulty": "medium",
                    "prep_tips": [
                        "Use STAR method",
                        "Discuss debugging process",
                        "What did you learn?"
                    ]
                }
            ],
            "data_engineer": [
                {
                    "question": "How would you optimize a slow query?",
                    "category": "Technical",
                    "difficulty": "hard",
                    "prep_tips": [
                        "Profiling and analysis",
                        "Indexing strategies",
                        "Query optimization techniques"
                    ]
                },
                {
                    "question": "Design a data pipeline for...",
                    "category": "System Design",
                    "difficulty": "hard",
                    "prep_tips": [
                        "Scalability considerations",
                        "Data quality",
                        "Latency vs throughput trade-offs"
                    ]
                },
                {
                    "question": "What's your approach to data quality?",
                    "category": "Technical",
                    "difficulty": "medium",
                    "prep_tips": [
                        "Validation techniques",
                        "Error handling",
                        "Monitoring and alerting"
                    ]
                }
            ],
            "integration_engineer": [
                {
                    "question": "How do you handle API compatibility?",
                    "category": "Technical",
                    "difficulty": "medium",
                    "prep_tips": [
                        "Versioning strategies",
                        "Backward compatibility",
                        "Deprecation planning"
                    ]
                },
                {
                    "question": "Describe an integration you built",
                    "category": "Behavioral",
                    "difficulty": "medium",
                    "prep_tips": [
                        "Use STAR method",
                        "Technical challenges faced",
                        "Solutions implemented"
                    ]
                },
                {
                    "question": "How do you ensure system reliability?",
                    "category": "Technical",
                    "difficulty": "medium",
                    "prep_tips": [
                        "Monitoring and logging",
                        "Error handling",
                        "Graceful degradation"
                    ]
                }
            ]
        }
        
        # Return generic questions if role not found
        default = [
            {"question": "Tell me about yourself", "category": "Behavioral"},
            {"question": "Why are you interested in this role?", "category": "Motivation"},
            {"question": "What are your strengths?", "category": "Self-assessment"},
            {"question": "What is an area for improvement?", "category": "Self-assessment"},
            {"question": "Tell me about a conflict with a teammate", "category": "Behavioral"},
            {"question": "How do you stay updated with technology?", "category": "Learning"}
        ]
        
        return questions.get(role_family, default)
    
    def get_company_research_template(self, company: str) -> Dict:
        """Get company research template"""
        return {
            "company": company,
            "research_areas": {
                "overview": {
                    "description": "What does the company do?",
                    "sources": ["Company website", "LinkedIn", "Crunchbase"],
                    "questions": [
                        "What products/services do they offer?",
                        "Who are their customers?",
                        "What's their business model?",
                        "Size and stage (startup, scale-up, enterprise)?"
                    ]
                },
                "culture": {
                    "description": "What's the company culture like?",
                    "sources": ["Glassdoor", "LinkedIn", "Company blog", "Employee interviews"],
                    "questions": [
                        "What are their core values?",
                        "What's the team dynamic like?",
                        "Work-life balance?",
                        "Growth opportunities?"
                    ]
                },
                "financials": {
                    "description": "How is the company doing financially?",
                    "sources": ["Company reports", "News articles", "Crunchbase"],
                    "questions": [
                        "Revenue and growth rate?",
                        "Funding history (if startup)?",
                        "Profitable or burning cash?",
                        "Recent funding or IPO?"
                    ]
                },
                "recent_news": {
                    "description": "What's new with the company?",
                    "sources": ["Google News", "Company blog", "LinkedIn news"],
                    "questions": [
                        "Recent product launches?",
                        "New partnerships or acquisitions?",
                        "Leadership changes?",
                        "Industry recognition or awards?"
                    ]
                },
                "competitive_landscape": {
                    "description": "Who are the competitors?",
                    "sources": ["Company website", "Industry reports", "News"],
                    "questions": [
                        "Who are main competitors?",
                        "What's their competitive advantage?",
                        "Market position?",
                        "Differentiation strategy?"
                    ]
                },
                "team": {
                    "description": "Who will you be working with?",
                    "sources": ["LinkedIn", "Company website", "Interview"],
                    "questions": [
                        "Who's your potential manager?",
                        "Team size and composition?",
                        "Team members' backgrounds?",
                        "Manager's management style?"
                    ]
                }
            },
            "notes": "Fill in your findings here. Reference these during the interview!"
        }
    
    def get_strength_weaknesses_framework(self) -> Dict:
        """Get framework for discussing strengths and weaknesses"""
        return {
            "strengths": {
                "guidance": "Pick 3-4 real strengths that are relevant to the job",
                "structure": "Strength + Example + Impact",
                "tips": [
                    "Pick strengths listed in the job description",
                    "Back them up with concrete examples",
                    "Show impact and results",
                    "Be authentic and specific",
                    "Avoid generic strengths"
                ],
                "good_examples": [
                    "Problem-solving with attention to detail",
                    "Clear communication in complex projects",
                    "Taking initiative and ownership",
                    "Learning new technologies quickly",
                    "Collaborating across teams"
                ]
            },
            "weaknesses": {
                "guidance": "Pick a real weakness, but frame it positively with improvements",
                "structure": "Weakness + Why it matters + Action taken + Results",
                "tips": [
                    "Never say 'I have no weaknesses'",
                    "Pick something real and relevant",
                    "Show self-awareness",
                    "Demonstrate growth and improvement",
                    "Frame as learning opportunity"
                ],
                "good_examples": [
                    "Initially struggled with delegation, now mentor junior developers",
                    "Used to rush through documentation, now prioritize clarity",
                    "Was hesitant public speaking, joined Toastmasters and now lead design reviews"
                ],
                "avoid": [
                    "Strengths disguised as weaknesses",
                    "Unrelated to the job",
                    "Critical flaws (dishonesty, lack of teamwork)",
                    "Unrealistic weaknesses"
                ]
            }
        }
    
    def get_questions_to_ask_interviewer(self, role: str, company: str) -> List[str]:
        """Get suggested questions to ask the interviewer"""
        return [
            # Team and Role
            "What does a typical day look like in this role?",
            "What are the key projects the team is working on right now?",
            "What are you looking for in an ideal candidate for this position?",
            
            # Company Culture and Growth
            "How does the company support professional development?",
            "What's the team's approach to work-life balance?",
            "Can you tell me about the team structure and reporting lines?",
            
            # Challenges and Opportunities
            "What are the biggest challenges the team is facing?",
            "What would you consider success in this role after 6 months?",
            "How does this role contribute to the company's goals?",
            
            # Technical and Process
            "What's your tech stack and why did you choose it?",
            "How does the team handle code reviews and quality assurance?",
            "What's your deployment process and release cycle?",
            
            # Management and Leadership
            "What's your management philosophy?",
            "How do you handle disagreements within the team?",
            "What opportunities are there for growth and advancement?",
            
            # Company Future
            "What's the company's vision for the next 2-3 years?",
            "Are there any upcoming changes to the team or department?",
            "How is the company adapting to industry trends?"
        ]
    
    def generate_elevator_pitch(
        self,
        name: str,
        current_role: str,
        key_achievements: List[str],
        career_goal: str
    ) -> Dict:
        """Generate a 2-minute elevator pitch"""
        
        pitch = f"""
Hi, I'm {name}. I'm a {current_role} with {len(key_achievements)} years of experience.

In my career, I've focused on:
{chr(10).join(f"• {achievement}" for achievement in key_achievements)}

I'm passionate about {career_goal} and looking for opportunities to make a meaningful impact in that area. 

I'd love to learn more about how I might contribute to your team. Do you have a few minutes to chat?
"""
        
        return {
            "pitch": pitch,
            "duration": "2 minutes",
            "tips": [
                "Practice until it feels natural",
                "Adjust based on audience",
                "End with a question",
                "Be enthusiastic but not overly energetic",
                "Memorize but don't sound robotic"
            ]
        }
    
    def save_materials_to_file(self, interview_id: str, materials: Dict) -> str:
        """Save coaching materials to file"""
        file_path = self.materials_dir / f"{interview_id}_coaching.json"
        with open(file_path, 'w') as f:
            json.dump(materials, f, indent=2)
        return str(file_path)
