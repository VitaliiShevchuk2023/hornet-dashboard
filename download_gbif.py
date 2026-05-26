"""
GBIF Data Pipeline for NABU Hornet Dashboard.
Downloads occurrence data from GBIF API and uploads to Azure Blob Storage.
Rate limit protection: exponential backoff on 429 errors.
"""

import os
import time
import pandas as pd
from pygbif import species, occurrences as occ

os.makedirs("data", exist_ok=True)

SPECIES_MAP = {
    "European hornet": "Vespa crabro",
    "Asian hornet":    "Vespa velutina",
}

MAX_PER_YEAR = 20000
REQUESTS_PER_SECOND = 0.5  # 1 запит кожні 2 секунди


def gbif_search_with_retry(max_retries: int = 5, **kwargs) -> dict:
    """GBIF API call with exponential backoff on rate limit errors."""
    for attempt in range(max_retries):
        try:
            return occ.search(**kwargs)
        except Exception as e:
            if "429" in str(e):
                wait = 2 ** attempt * 10  # 10, 20, 40, 80, 160 секунд
                print(f"  ⚠️  Rate limit hit — waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
    raise Exception(f"GBIF API failed after {max_retries} retries")


def upload_to_azure(file_path: str, blob_name: str) -> None:
    """Upload CSV file to Azure Blob Storage."""
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    account_key  = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    container    = os.environ.get("AZURE_STORAGE_CONTAINER", "gbif-data")

    if not account_name or not account_key:
        print("Azure Storage credentials not set — skipping upload")
        return

    from azure.storage.blob import BlobServiceClient
    client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=account_key,
    )
    blob = client.get_blob_client(container=container, blob=blob_name)
    with open(file_path, "rb") as f:
        blob.upload_blob(f, overwrite=True)
    print(f"✅ Uploaded {blob_name} to Azure Blob Storage")


def download_species(label: str, name: str) -> str:
    """Download all occurrences for one species from GBIF API."""
    result = species.name_suggest(q=name)[0]
    key    = result["key"]
    print(f"\n📥 Loading {label} (taxonKey={key})")
    all_records = []

    for year in range(2000, 2026):
        # Перевіряємо скільки записів є за цей рік
        res   = gbif_search_with_retry(taxonKey=key, country="DE",
                                       year=year, limit=1)
        total = res["count"]
        time.sleep(1 / REQUESTS_PER_SECOND)  # rate limit

        if total == 0:
            print(f"  {year}: 0 [skip]")
            continue

        year_records = []
        offset, limit = 0, 300

        while offset < min(total, MAX_PER_YEAR):
            res   = gbif_search_with_retry(taxonKey=key, country="DE",
                                           year=year, limit=limit,
                                           offset=offset)
            batch = res["results"]
            if not batch:
                break
            year_records.extend(batch)
            offset += len(batch)
            time.sleep(1 / REQUESTS_PER_SECOND)  # rate limit

        all_records.extend(year_records)
        flag = "TRUNCATED" if total > MAX_PER_YEAR else "ok"
        print(f"  {year}: {total} total, loaded {len(year_records)} [{flag}]")

    df    = pd.DataFrame(all_records)
    fname = f"/tmp/{label.lower().replace(' ', '_')}_DE.csv"
    df.to_csv(fname, index=False)
    print(f"  💾 Saved {len(df):,} records to {fname}")
    return fname


# ── Entry point ───────────────────────────────────────
print("=== GBIF → Azure Blob Storage Pipeline ===")
print(f"Rate limit: {REQUESTS_PER_SECOND} requests/second")

for label, name in SPECIES_MAP.items():
    fname     = download_species(label, name)
    blob_name = f"{label.lower().replace(' ', '_')}_DE.csv"

    if os.environ.get("UPLOAD_TO_AZURE") == "true":
        print(f"📤 Uploading {blob_name}...")
        upload_to_azure(fname, blob_name)

    # Пауза між видами щоб не перевищити rate limit
    print("⏳ Waiting 60s before next species...")
    time.sleep(60)

print("\n✅ Pipeline complete!")
