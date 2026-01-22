import re

def extract_keywords(job_description: str, allowed_skills: list):
    jd = job_description.lower()
    keywords = []

    for skill in allowed_skills:
        if skill.lower() in jd:
            keywords.append(skill)

    # light noun phrase extraction (safe)
    phrases = re.findall(r"\b[a-zA-Z]{4,}\b", jd)
    keywords.extend(list(set(phrases)))

    return sorted(set(keywords))
