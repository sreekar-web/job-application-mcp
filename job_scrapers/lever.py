import requests
import time

LEVER_API = "https://api.lever.co/v0/postings"
MAX_RETRIES = 3
TIMEOUT = 10


def fetch_lever_jobs(company_slug: str):
    url = f"{LEVER_API}/{company_slug}"
    attempts = 0

    while attempts < MAX_RETRIES:
        try:
            response = requests.get(url, timeout=TIMEOUT)
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

        except requests.exceptions.RequestException as e:
            attempts += 1
            print(f"[WARN] Lever fetch failed for {company_slug} (attempt {attempts}): {e}")
            time.sleep(2)

    print(f"[ERROR] Skipping Lever company after retries: {company_slug}")
    return []
