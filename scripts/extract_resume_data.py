from docx import Document
import json
from pathlib import Path

SOURCE_DIR = Path("resumes/source_docs")
MASTER_DIR = Path("resumes/master")
MASTER_DIR.mkdir(parents=True, exist_ok=True)

skills = set()
experience = []
education = []

def extract_text(docx_path):
    doc = Document(docx_path)
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]

for docx_file in SOURCE_DIR.glob("*.docx"):
    lines = extract_text(docx_file)

    current_section = None
    current_job = None

    for line in lines:
        upper = line.upper()

        if "SKILL" in upper:
            current_section = "skills"
            continue
        elif "EXPERIENCE" in upper:
            current_section = "experience"
            continue
        elif "EDUCATION" in upper:
            current_section = "education"
            continue

        if current_section == "skills":
            for item in line.replace(",", " ").split():
                skills.add(item)

        elif current_section == "experience":
            if line.isupper():
                current_job = {
                    "title": line,
                    "company": "",
                    "duration": "",
                    "responsibilities": []
                }
                experience.append(current_job)
            elif current_job:
                current_job["responsibilities"].append(line)

        elif current_section == "education":
            education.append(line)

# Write outputs
(MASTER_DIR / "skills_inventory.json").write_text(
    json.dumps(sorted(skills), indent=2)
)

(MASTER_DIR / "core_experience.json").write_text(
    json.dumps(experience, indent=2)
)

(MASTER_DIR / "education.json").write_text(
    json.dumps(education, indent=2)
)

print("Extraction complete. Review JSON files manually.")
