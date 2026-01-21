import requests

def fetch_lever_jobs(company_slug: str):
    """
    Fetch jobs from a Lever-powered career page.
    Example slug: 'netflix', 'spotify'
    """
    url = f"https://api.lever.co/v0/postings/{company_slug}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    jobs = response.json()

    results = []
    for job in jobs:
        results.append({
            "company": company_slug,
            "role": job.get("text"),
            "location": job.get("categories", {}).get("location"),
            "job_description": job.get("description"),
            "apply_url": job.get("hostedUrl"),
            "source": "lever"
        })

    return results
