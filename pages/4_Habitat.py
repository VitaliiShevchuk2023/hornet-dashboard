import streamlit as st
import plotly.express as px
import pandas as pd
from utils.gbif_loader import load_both, COLORS

st.set_page_config(
    page_title="Q3 — Habitat Types",
    page_icon="🌿",
    layout="wide"
)
st.title("Q3 — Habitat types and hornet distribution")
st.markdown(
    "Germany has **93 recognised habitat types** — forests, meadows, moors etc. "
    "Where do hornets occur most frequently, and where are they absent?"
)

country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)
species_filter = st.sidebar.multiselect(
    "Species",
    ["European hornet", "Asian hornet"],
    default=["European hornet", "Asian hornet"]
)

df = load_both(country=country, limit=limit)

if df.empty:
    st.error("No data loaded.")
    st.stop()

# Filter species
df = df[df["species_label"].isin(species_filter)]

# ── Locality keyword analysis ─────────────────────────
st.subheader("🌍 Habitat keywords from locality field")
st.caption(
    "GBIF locality field often contains habitat descriptions "
    "like 'Feldflur', 'Waldstück', 'Garten' etc."
)

HABITAT_KEYWORDS = {
    "Forest / Wald":    ["wald", "forst", "forest", "gehölz", "baum"],
    "Field / Feld":     ["feld", "flur", "wiese", "meadow", "field"],
    "Garden / Garten":  ["garten", "garden", "park", "grün"],
    "Settlement":       ["stadt", "dorf", "ortschaft", "siedlung", "urban"],
    "Water / Wasser":   ["bach", "fluss", "see", "teich", "wasser", "river"],
    "Moor / Sumpf":     ["moor", "sumpf", "feucht", "wetland"],
    "Vineyard":         ["weinberg", "reben", "vineyard"],
}

if "locality" in df.columns:
    def classify_habitat(locality: str) -> str:
        if not isinstance(locality, str):
            return "Unknown"
        loc = locality.lower()
        for habitat, keywords in HABITAT_KEYWORDS.items():
            if any(kw in loc for kw in keywords):
                return habitat
        return "Other"

    df["habitat_type"] = df["locality"].apply(classify_habitat)

    col1, col2 = st.columns(2)

    with col1:
        habitat_counts = (
            df.groupby(["habitat_type", "species_label"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        fig = px.bar(
            habitat_counts,
            x="habitat_type", y="count",
            color="species_label",
            color_discrete_map=COLORS,
            barmode="group",
            title="Observations by habitat type",
            labels={"habitat_type": "Habitat", "count": "Observations"},
        )
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        total_by_habitat = (
            df.groupby("habitat_type")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        fig2 = px.pie(
            total_by_habitat,
            names="habitat_type",
            values="count",
            title="Habitat distribution (both species)",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Sample localities
    st.subheader("📋 Sample locality descriptions")
    sample = (
        df[df["locality"].notna()][["species_label", "locality", "habitat_type", "year"]]
        .drop_duplicates("locality")
        .head(20)
    )
    st.dataframe(sample, use_container_width=True)

else:
    st.warning("Locality field not available in current dataset.")

# ── Seasonal pattern ──────────────────────────────────
st.subheader("📅 Seasonal activity pattern")
if "month" in df.columns:
    monthly = (
        df.groupby(["month", "species_label"])
        .size()
        .reset_index(name="count")
    )
    month_names = {
        1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
        7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"
    }
    monthly["month_name"] = monthly["month"].map(month_names)
    fig3 = px.bar(
        monthly,
        x="month", y="count",
        color="species_label",
        color_discrete_map=COLORS,
        barmode="group",
        title="Monthly observation pattern",
        labels={"month": "Month", "count": "Observations"},
    )
    fig3.update_xaxes(
        tickvals=list(month_names.keys()),
        ticktext=list(month_names.values())
    )
    st.plotly_chart(fig3, use_container_width=True)
