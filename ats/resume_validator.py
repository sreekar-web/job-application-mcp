FORBIDDEN = ["table", "<w:tbl", "column", "header", "footer"]

ALLOWED_SECTIONS = [
    "SUMMARY",
    "SKILLS",
    "EXPERIENCE",
    "EDUCATION"
]

def validate_resume(text: str):
    upper = text.upper()

    for section in ALLOWED_SECTIONS:
        if section not in upper:
            raise ValueError(f"Missing required section: {section}")

    for bad in FORBIDDEN:
        if bad in text.lower():
            raise ValueError(f"ATS violation detected: {bad}")

    return True
