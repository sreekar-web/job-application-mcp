import json
from pathlib import Path

SKILLS_FILE = Path("resumes/master/skills_inventory.json")
EXPERIENCE_FILE = Path("resumes/master/core_experience.json")
OUTPUT_DIR = Path("resumes/role_variants")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROLE_SKILL_MAP = {
    "backend_engineer": {
        "signals": ["Python", "Java", "SQL", "REST"],
        "exclude": ["Kubernetes", "Terraform", "Selenium"]
    },
    "devops_engineer": {
        "signals": ["Docker", "Kubernetes", "CI/CD", "Terraform", "AWS"],
        "exclude": ["Selenium", "EDI"]
    },
    "qa_engineer": {
        "signals": ["Selenium", "PyTest", "Testing"],
        "exclude": ["Terraform", "Kubernetes"]
    },
    "integration_engineer": {
        "signals": ["EDI", "X12", "AS2", "MFT"],
        "exclude": ["React", "Frontend"]
    },
    "data_engineer": {
        "signals": ["ETL", "Airflow", "Spark", "SQL"],
        "exclude": ["Selenium", "EDI"]
    }
}

skills_data = json.loads(SKILLS_FILE.read_text())
flat_skills = {skill for skill in skills_data}

experience_data = json.loads(EXPERIENCE_FILE.read_text())
experience_titles = set()

for job in experience_data:
    for key in ["title", "role", "position"]:
        if key in job and job[key]:
            experience_titles.add(job[key])
            break

for role, rules in ROLE_SKILL_MAP.items():
    matched_skills = sorted(
        skill for skill in flat_skills
        if any(sig.lower() in skill.lower() for sig in rules["signals"])
    )

    if len(matched_skills) < 2:
        continue  # Not qualified → do not create role

    variant = {
        "role_family": role,
        "allowed_skills": matched_skills,
        "primary_focus": rules["signals"],
        "allowed_experience_titles": sorted(experience_titles),
        "excluded_skills": rules["exclude"]
    }

    output_file = OUTPUT_DIR / f"{role}.json"
    output_file.write_text(json.dumps(variant, indent=2))

    print(f"✔ Created role variant: {role}")

print("Role variant generation complete.")
