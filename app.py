"""Streamlit UI for Intelligent Candidate Discovery."""

from __future__ import annotations

import streamlit as st

from src.pipeline import CandidateDiscoveryPipeline


def main() -> None:
    """Render the multi-page Streamlit application."""

    st.set_page_config(page_title="Intelligent Candidate Discovery", layout="wide")
    st.title("Intelligent Candidate Discovery")
    st.caption("Upload a job description and candidate data to rank and explain the best matches.")

    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Upload JD", "Candidate Ranking", "Top Candidates", "Candidate Details", "Analytics Dashboard", "Download Submission"],
    )

    CandidateDiscoveryPipeline()

    if page == "Home":
        st.markdown("This app will load the hackathon files from `data/raw/` and generate ranked recommendations.")
    elif page == "Upload JD":
        st.info("Upload support will be connected to the parsed dataset once the source files are available.")
    elif page == "Candidate Ranking":
        st.info("Ranking view placeholder. The ranking engine is implemented in the backend pipeline.")
    elif page == "Top Candidates":
        st.info("Top candidate table will render here after the inputs are loaded.")
    elif page == "Candidate Details":
        st.info("Detailed candidate explanations will be shown here.")
    elif page == "Analytics Dashboard":
        st.info("Analytics charts will summarize skills, experience, and ranking distribution.")
    elif page == "Download Submission":
        st.info("Use the backend pipeline to export `submission.xlsx` into the output folder.")


if __name__ == "__main__":
    main()