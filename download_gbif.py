from pygbif import species, occurrences as occ
import pandas as pd
import os

# Create the output directory if it doesn't exist.
# exist_ok=True prevents an error if the directory is already present.
os.makedirs("data", exist_ok=True)

# ── Species registry ──────────────────────────────────
# Maps human-readable labels to scientific names used in GBIF queries.
# Add additional species here to extend the download without changing
# the rest of the script.
SPECIES_MAP = {
    "European hornet": "Vespa crabro",
    "Asian hornet":    "Vespa velutina",
}

# Maximum records to download per year per species.
# GBIF can return hundreds of thousands of records for common species;
# this cap prevents extremely large files while keeping the dataset
# representative. Years exceeding this limit are flagged as TRUNCATED.
MAX_PER_YEAR = 20000

# ── Main download loop ────────────────────────────────
# Iterates over each species and downloads all available German occurrence
# records year by year (2000–2025). Yearly iteration avoids hitting the
# GBIF API's hard limit of 100,000 records per single request.
for label, name in SPECIES_MAP.items():

    # Resolve scientific name to a GBIF taxon key.
    # name_suggest() returns ranked candidates — [0] is the best match.
    result = species.name_suggest(q=name)[0]
    key = result["key"]
    print(f"\nLoading {label}, key={key}")

    all_records = []

    for year in range(2000, 2026):

        # Probe request: fetch just 1 record to get the total count for
        # this year without downloading the full dataset upfront.
        # This avoids unnecessary pagination when a year has zero records.
        res   = occ.search(taxonKey=key, country="DE", year=year, limit=1)
        total = res["count"]

        if total == 0:
            print(f"  {year}: 0 total [skip]")
            continue

        # ── Offset-based pagination ───────────────────
        # GBIF API returns at most 300 records per request.
        # We page through results by incrementing the offset until we
        # either exhaust all records or reach MAX_PER_YEAR.
        year_records = []
        offset = 0
        limit  = 300   # maximum page size supported by the GBIF API

        while offset < min(total, MAX_PER_YEAR):
            res = occ.search(
                taxonKey=key,
                country="DE",
                year=year,
                limit=limit,
                offset=offset
            )
            batch = res["results"]

            # Empty batch means no more records are available — exit the loop
            if not batch:
                break

            year_records.extend(batch)
            offset += len(batch)   # advance by actual batch size, not limit

        all_records.extend(year_records)

        # Flag years where GBIF has more records than MAX_PER_YEAR so
        # downstream analysis can account for potential under-sampling
        flag = "TRUNCATED" if total > MAX_PER_YEAR else "ok"
        print(f"  {year}: {total} total, loaded {len(year_records)} [{flag}]")

    # ── Save to CSV ───────────────────────────────────
    # One CSV file per species, named after the label in snake_case.
    # index=False omits the pandas row index from the output file.
    # These CSVs are uploaded to Google Drive and consumed by gbif_loader.py
    # as the primary data source for the Germany dashboard.
    df    = pd.DataFrame(all_records)
    fname = f"data/{label.lower().replace(' ', '_')}_DE.csv"
    df.to_csv(fname, index=False)
    print(f"Saved {len(df)} to {fname}")

print("\nDone!")


# ── Azure Blob Storage upload (опційно) ───────────────
def upload_to_azure(file_path: str, blob_name: str) -> None:
    """Upload CSV file to Azure Blob Storage if credentials are set."""
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    account_key  = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    container    = os.environ.get("AZURE_STORAGE_CONTAINER", "gbif-data")

    if not account_name or not account_key:
        print("Azure Storage credentials not set — skipping upload")
        return

    try:
        from azure.storage.blob import BlobServiceClient
        client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=account_key,
        )
        blob = client.get_blob_client(container=container, blob=blob_name)
        with open(file_path, "rb") as f:
            blob.upload_blob(f, overwrite=True)
        print(f"Uploaded {blob_name} to Azure Blob Storage")
    except Exception as e:
        print(f"Azure upload failed: {e}")


if os.environ.get("UPLOAD_TO_AZURE") == "true":
    for label in SPECIES_MAP:
        fname     = f"data/{label.lower().replace(' ', '_')}_DE.csv"
        blob_name = f"{label.lower().replace(' ', '_')}_DE.csv"
        if os.path.exists(fname):
            upload_to_azure(fname, blob_name)
