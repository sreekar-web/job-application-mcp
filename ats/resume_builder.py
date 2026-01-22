from docx import Document

def build_resume_docx(
    output_path,
    summary,
    skills,
    experience,
    education
):
    doc = Document()

    doc.add_heading("SUMMARY", level=1)
    doc.add_paragraph(summary)

    doc.add_heading("SKILLS", level=1)
    doc.add_paragraph(", ".join(skills))

    doc.add_heading("EXPERIENCE", level=1)
    for job in experience:
        doc.add_paragraph(f"{job['title']} – {job['company']} ({job['duration']})")
        for bullet in job["responsibilities"]:
            doc.add_paragraph(f"- {bullet}")

    doc.add_heading("EDUCATION", level=1)
    doc.add_paragraph(
        f"{education['degree']} in {education['field']}, "
        f"{education['institution']} ({education['year']})"
    )

    doc.save(output_path)
