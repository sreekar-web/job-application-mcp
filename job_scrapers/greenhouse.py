import requests

def fetch_greenhouse_jobs(company_slug: str):
    """
    Fetch jobs from a Greenhouse-powered career page.
    Example slug: 'airbnb', 'stripe'
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    jobs = response.json().get("jobs", [])

    results = []
    for job in jobs:
        results.append({
            "company": company_slug,
            "role": job.get("title"),
            "location": job.get("location", {}).get("name"),
            "job_description": job.get("content"),
            "apply_url": job.get("absolute_url"),
            "source": "greenhouse"
        })

    return results
