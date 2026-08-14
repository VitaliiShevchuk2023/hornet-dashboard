"""
Normalizes NABU|naturgucker raw export (German schema, as downloaded from
the shared Google Sheet / Data_NABU_Hornet_Campaign_2025.xlsx) into the
flat CSV format expected by manage.py load_dashboard_csv.

Usage:
    python naturgucker_loader.py /tmp/nabu_raw.xlsx -o /tmp/dashboard_normalized.csv
    python naturgucker_loader.py /tmp/nabu_raw.csv  -o /tmp/dashboard_normalized.csv

Only pandas is required (no Django import) so this can run standalone,
before the normalized file gets handed to load_dashboard_csv inside the
Django container.

Key mapping decisions (documented here since they're not obvious from the
raw column names alone):

- Species: filtered to ONLY Vespa crabro / Vespa velutina (Gattung+Art).
  Everything else in the export (Vespula, Polistes, Volucella, Urocerus,
  Scoliidae, etc.) is bycatch from the same citizen-science campaign and
  is dropped here, out of scope for the hornet dashboard.
- Coordinates: uses Punktverortung E/N, NOT Koordinate E/N. The latter
  is a coarse TK25 map-sheet grid centroid (same value repeats across many
  rows in the same grid cell); Punktverortung is the actual per-observation
  point NABU shows on their map (already GDPR-precision-adjusted on their
  end, we don't further round it here).
- Bundesland: Provinz is NABU's own regional code, not a German state
  name. Mapped via BUNDESLAND_MAP below on a best-effort basis, the
  mapping was inferred from context, NOT confirmed against an official
  NABU code list. Flag any code that falls into "UNKNOWN:<code>" for
  manual review / confirmation with Theresa.
- photo_verified: Belegbildlink present AND Best.unsicher == "nein" AND
  Beob.gesperrt == "nein", mirrors Theresa's "photos only, that's the
  safe way" recommendation from the Q&A.
- Country scope: filtered to Land == "DE" by default. The raw export
  actually spans multiple European countries (Austria, France, etc.),
  those are NOT unmapped German codes, they're a different country
  entirely. Since the MVP scope decision so far has been "Germany-first"
  (mvp-draft.md), non-DE rows are dropped here. Pass --include-europe to
  keep them.
- gbif_id column in the output actually carries NABU's DatensatzID, not
  a real GBIF occurrence ID, reused as a unique external reference since
  this dataset never touches GBIF's API.
"""
import argparse
import sys

import pandas as pd

SPECIES_MAP = {
    ("Vespa", "crabro"): "European hornet",
    ("Vespa", "velutina"): "Asian hornet",
}

# Best-effort NABU Provinz-code -> Bundesland mapping, GERMANY ONLY.
# NOT officially confirmed, cross-check with Theresa/NABU docs before
# treating as authoritative. Codes seen in the sample export are covered;
# extend as new codes turn up.
BUNDESLAND_MAP = {
    "SHHH": "Schleswig-Holstein",
    "MeVo": "Mecklenburg-Vorpommern",
    "NiHB": "Niedersachsen",
    "BB": "Brandenburg",
    "NRW": "Nordrhein-Westfalen",
    "SAh": "Sachsen-Anhalt",
    "Sac": "Sachsen",
    "BaWü": "Baden-Wuerttemberg",
    "Bay": "Bayern",
    "Hes": "Hessen",
    "Rh-Pf": "Rheinland-Pfalz",
    "Saar": "Saarland",
    "Thür": "Thueringen",
}


def normalize(input_path: str, include_europe: bool = False) -> pd.DataFrame:
    if input_path.lower().endswith(".xlsx"):
        raw = pd.read_excel(input_path)
    else:
        raw = pd.read_csv(input_path)

    missing = {"Gattung", "Art", "Punktverortung E", "Punktverortung N", "Datum", "Provinz"} - set(raw.columns)
    if missing:
        raise SystemExit(f"Input is missing expected columns: {missing}")

    if not include_europe and "Land" in raw.columns:
        before = len(raw)
        raw = raw[raw["Land"] == "DE"].copy()
        print(f"Filtered to Land=='DE': {before} -> {len(raw)} rows "
              f"(pass --include-europe to keep other countries)", file=sys.stderr)

    raw["_species_key"] = list(zip(raw["Gattung"], raw["Art"]))
    df = raw[raw["_species_key"].isin(SPECIES_MAP.keys())].copy()

    if df.empty:
        print("WARNING: 0 rows matched Vespa crabro / Vespa velutina after filtering. "
              "Check that Gattung/Art columns are spelled as expected.", file=sys.stderr)

    out = pd.DataFrame()
    out["species"] = df["_species_key"].map(SPECIES_MAP)
    out["scientific_name"] = df["Gattung"] + " " + df["Art"]

    out["lat"] = df["Punktverortung N"]
    out["lon"] = df["Punktverortung E"]

    def map_bundesland(code):
        if pd.isna(code):
            return ""
        return BUNDESLAND_MAP.get(str(code).strip(), f"UNKNOWN:{code}")

    out["bundesland"] = df["Provinz"].apply(map_bundesland)
    out["landkreis"] = ""
    out["locality"] = df.get("Gebietsname", "")

    out["event_date"] = pd.to_datetime(df["Datum"], format="%d.%m.%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    out["year"] = pd.to_datetime(df["Datum"], format="%d.%m.%Y", errors="coerce").dt.year

    has_photo = df.get("Belegbildlink", pd.Series([""] * len(df))).fillna("").astype(str).str.strip() != ""
    not_uncertain = df.get("Best.unsicher", pd.Series(["nein"] * len(df))).fillna("nein").astype(str).str.strip().str.lower() == "nein"
    not_blocked = df.get("Beob.gesperrt", pd.Series(["nein"] * len(df))).fillna("nein").astype(str).str.strip().str.lower() == "nein"
    out["photo_verified"] = has_photo & not_uncertain & not_blocked

    out["basis_of_record"] = "HUMAN_OBSERVATION"
    out["gbif_id"] = df.get("DatensatzID", "").astype(str)

    unknown_bundesland = out[out["bundesland"].str.startswith("UNKNOWN:")]
    if not unknown_bundesland.empty:
        codes = sorted(unknown_bundesland["bundesland"].unique())
        print(f"WARNING: {len(unknown_bundesland)} rows have unmapped Provinz codes: {codes}. "
              f"Add them to BUNDESLAND_MAP and re-run, or confirm with Theresa first.", file=sys.stderr)

    return out[[
        "species", "scientific_name", "lat", "lon", "bundesland", "landkreis",
        "locality", "event_date", "year", "photo_verified", "basis_of_record", "gbif_id",
    ]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", help="Raw NABU export (.xlsx or .csv)")
    parser.add_argument("-o", "--output", default="dashboard_normalized.csv")
    parser.add_argument("--include-europe", action="store_true",
                         help="Keep non-German rows too")
    args = parser.parse_args()

    result = normalize(args.input_path, include_europe=args.include_europe)
    result.to_csv(args.output, index=False)

    print(f"Wrote {len(result)} normalized rows to {args.output}")
    print(result["species"].value_counts().to_string())
    print(f"Photo-verified: {result['photo_verified'].sum()} / {len(result)}")


if __name__ == "__main__":
    main()
