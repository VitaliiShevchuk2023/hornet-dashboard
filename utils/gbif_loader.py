import streamlit as st
import pandas as pd
from pygbif import species, occurrences as occ

SPECIES = {
    "European hornet": "Vespa crabro",
    "Asian hornet":    "Vespa velutina",
}

COLORS = {
    "European hornet": "#f5a623",
    "Asian hornet":    "#d0021b",
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
    key = get_species_key(species_name)
    res = occ.search(taxonKey=key, country=country, limit=limit, year="2000,2025")
    total = res["count"]

    if not res["results"]:
        return pd.DataFrame(), total

    df = pd.DataFrame(res["results"])
    df["eventDate"] = pd.to_datetime(df["eventDate"], errors="coerce")
    df["year"] = df["eventDate"].dt.year.astype("Int64")
    df["year"] = df["year"].astype("int", errors="ignore")
    label = next(
        (k for k, v in SPECIES.items() if v == species_name),
        species_name
    )
    df["species_label"] = label
    df["color"] = COLORS.get(label, "#999")

    keep = [
        "species", "species_label", "color",
        "decimalLatitude", "decimalLongitude",
        "eventDate", "year",
        "stateProvince", "basisOfRecord",
        "gbifID",
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