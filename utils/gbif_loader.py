import streamlit as st
import pandas as pd
import os
from pygbif import species, occurrences as occ

SPECIES = {
    "European hornet": "Vespa crabro",
    "Asian hornet":    "Vespa velutina",
}

COLORS = {
    "European hornet": "#f5a623",
    "Asian hornet":    "#d0021b",
}

CSV_FILES = {
    "European hornet": "data/european_hornet_DE.csv",
    "Asian hornet":    "data/asian_hornet_DE.csv",
}

@st.cache_data(ttl=3600, show_spinner="Loading GBIF data...")
def get_species_key(name: str) -> int:
    result = species.name_suggest(q=name)[0]
    return result["key"]

@st.cache_data(ttl=3600, show_spinner="Fetching observations...")
def load_observations(
    species_name: str,
    country: str = "DE",
    limit: int = 300,
) -> tuple[pd.DataFrame, int]:

    # Пробуємо завантажити з CSV якщо country=DE
    label = next(
        (k for k, v in SPECIES.items() if v == species_name),
        species_name
    )
    csv_path = CSV_FILES.get(label)

    if country == "DE" and csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        total = len(df)
    else:
        # Fallback: API
        key = get_species_key(species_name)
        records_per_year = max(10, limit // 25)
        all_results = []
        for year in range(2000, 2026):
            res = occ.search(
                taxonKey=key,
                country=country,
                year=year,
                limit=records_per_year,
            )
            if res["results"]:
                all_results.extend(res["results"])
        total = len(all_results)
        df = pd.DataFrame(all_results) if all_results else pd.DataFrame()

    if df.empty:
        return pd.DataFrame(), 0

    # Обробка дат
    df["eventDate"] = pd.to_datetime(df["eventDate"], errors="coerce")
    # Використовуємо year з CSV якщо є, інакше парсимо з eventDate
    if "year" not in df.columns or df["year"].isna().sum() > len(df) * 0.3:
        df["year"] = df["eventDate"].dt.year.astype("Int64")
    else:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = df["eventDate"].dt.month.astype("Int64")

    # GADM поля
    if "gadm" in df.columns:
        def safe_gadm(x, level):
            try:
                if isinstance(x, dict):
                    return x.get(level, {}).get("name", "")
                import ast
                d = ast.literal_eval(str(x))
                return d.get(level, {}).get("name", "")
            except Exception:
                return ""
        df["bundesland"] = df["gadm"].apply(lambda x: safe_gadm(x, "level1"))
        df["landkreis"]  = df["gadm"].apply(lambda x: safe_gadm(x, "level2"))
    else:
        df["bundesland"] = df.get("stateProvince", "")
        df["landkreis"]  = ""

    df["species_label"] = label
    df["color"]         = COLORS.get(label, "#999")

    keep = [
        "species", "species_label", "color",
        "decimalLatitude", "decimalLongitude",
        "eventDate", "year", "month",
        "stateProvince", "bundesland", "landkreis",
        "locality", "basisOfRecord", "gbifID",
    ]
    cols = [c for c in keep if c in df.columns]
    return df[cols], total

@st.cache_data(ttl=3600, show_spinner="Loading both species...")
def load_both(country: str = "DE", limit: int = 300) -> pd.DataFrame:
    frames = []
    for label, name in SPECIES.items():
        df, _ = load_observations(name, country, limit)
        if not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
