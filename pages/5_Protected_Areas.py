import streamlit as st
import plotly.express as px
import pandas as pd
from utils.gbif_loader import load_both, COLORS

st.set_page_config(
    page_title="Q4 — Protected Areas",
    page_icon="🏞️",
    layout="wide"
)
st.title("Q4 — Do Asian hornets occur more in protected areas?")
st.markdown(
    "Hypothesis: protected areas offer abundant insect prey. "
    "If confirmed, this could guide management strategies for nature reserves."
)

country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

df = load_both(country=country, limit=limit)

if df.empty:
    st.error("No data loaded.")
    st.stop()

# ── Protected area keywords in locality ───────────────
PROTECTED_KEYWORDS = [
    "naturschutz", "schutzgebiet", "nationalpark", "national park",
    "naturpark", "biosphäre", "biosphere", "reservat", "reserve",
    "vogelschutz", "ffh", "natura 2000", "naturreservat",
]

if "locality" in df.columns:
    def is_protected(locality: str) -> str:
        if not isinstance(locality, str):
            return "Unknown"
        loc = locality.lower()
        return "Protected area" if any(kw in loc for kw in PROTECTED_KEYWORDS) else "Non-protected"

    df["area_type"] = df["locality"].apply(is_protected)

    col1, col2 = st.columns(2)

    with col1:
        area_counts = (
            df.groupby(["area_type", "species_label"])
            .size()
            .reset_index(name="count")
        )
        fig = px.bar(
            area_counts,
            x="area_type", y="count",
            color="species_label",
            color_discrete_map=COLORS,
            barmode="group",
            title="Protected vs non-protected areas",
            labels={"area_type": "Area type", "count": "Observations"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        protected_pct = (
            df.groupby(["species_label", "area_type"])
            .size()
            .reset_index(name="count")
        )
        fig2 = px.pie(
            protected_pct[protected_pct["area_type"] != "Unknown"],
            names="area_type",
            values="count",
            facet_col="species_label",
            title="Share of protected area sightings",
            color_discrete_sequence=["#2ecc71", "#e74c3c"],
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.info(
        "⚠️ Note: This analysis is based on locality text keywords. "
        "For precise protected area boundaries, integration with "
        "WDPA (World Database on Protected Areas) is recommended."
    )

    protected_df = df[df["area_type"] == "Protected area"]
    st.metric("Sightings in protected areas", len(protected_df))
    st.dataframe(
        protected_df[["species_label", "locality", "bundesland", "year"]]
        .head(30),
        use_container_width=True
    )
