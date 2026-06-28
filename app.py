"""Streamlit UI for Intelligent Candidate Discovery."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import streamlit as st

from src.pipeline import CandidateDiscoveryPipeline
from src.inspection import DatasetInspector
from src.reporting import AnalyticsService


def _write_uploaded_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile, destination: Path) -> Path:
    """Persist an uploaded Streamlit file to disk for the file-based pipeline."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def _load_from_sources(pipeline: CandidateDiscoveryPipeline, jd_path: Path, candidates_path: Path):
    """Load, rank, and enrich candidate results from the selected files."""

    jd_profile, candidates = pipeline.load_inputs(jd_path, candidates_path)
    results = pipeline.rank(jd_profile, candidates)
    return jd_profile, candidates, results


def main() -> None:
    """Render the multi-page Streamlit application."""

    st.set_page_config(page_title="Intelligent Candidate Discovery", layout="wide")
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.8rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    pipeline = CandidateDiscoveryPipeline()
    inspector = DatasetInspector()
    analytics = AnalyticsService()

    st.title("Intelligent Candidate Discovery")
    st.caption("Upload a job description and candidate data to rank and explain the best matches.")

    page = st.sidebar.radio(
        "Navigate",
        [
            "Home",
            "Upload JD",
            "Candidate Ranking",
            "Top Candidates",
            "Candidate Details",
            "Analytics Dashboard",
            "Download Submission",
        ],
    )

    with st.sidebar:
        st.subheader("Data Inputs")
        jd_upload = st.file_uploader("Job Description (.docx)", type=["docx"], key="jd_upload")
        candidates_upload = st.file_uploader("Candidates (.jsonl)", type=["jsonl"], key="candidates_upload")
        run_button = st.button("Run Ranking")

    jd_default = pipeline.config.raw_data_dir / "job_description.docx"
    candidates_default = pipeline.config.raw_data_dir / "candidates.jsonl"
    jd_path = jd_default
    candidates_path = candidates_default
    reports: list[tuple[str, object]] = []
    results = None
    candidates = None

    if jd_upload and candidates_upload:
        upload_dir = pipeline.config.output_dir / "uploads"
        jd_path = _write_uploaded_file(jd_upload, upload_dir / jd_upload.name)
        candidates_path = _write_uploaded_file(candidates_upload, upload_dir / candidates_upload.name)

        if run_button or page in {"Candidate Ranking", "Top Candidates", "Candidate Details", "Analytics Dashboard", "Download Submission"}:
            jd_profile, candidates, results = _load_from_sources(pipeline, jd_path, candidates_path)
            reports = [
                ("Job Description", inspector.inspect(pipeline.loader.load(jd_path))),
                ("Candidates", inspector.inspect(pipeline.loader.load(candidates_path))),
            ]
            st.session_state["jd_profile"] = jd_profile
            st.session_state["candidates"] = candidates
            st.session_state["results"] = results
            submission_path = pipeline.generate_submission(results)
            st.session_state["submission_path"] = submission_path
    elif jd_default.exists() and candidates_default.exists():
        if run_button or page in {"Candidate Ranking", "Top Candidates", "Candidate Details", "Analytics Dashboard", "Download Submission"}:
            jd_profile, candidates, results = _load_from_sources(pipeline, jd_default, candidates_default)
            reports = [
                ("Job Description", inspector.inspect(pipeline.loader.load(jd_default))),
                ("Candidates", inspector.inspect(pipeline.loader.load(candidates_default))),
            ]
            st.session_state["jd_profile"] = jd_profile
            st.session_state["candidates"] = candidates
            st.session_state["results"] = results
            submission_path = pipeline.generate_submission(results)
            st.session_state["submission_path"] = submission_path

    if page == "Home":
        st.markdown(
            """
            ### Workflow
            1. Upload the job description and candidate dataset.
            2. Inspect the source structure before ranking.
            3. Generate semantic, skill, and experience based rankings.
            4. Export a validated submission workbook.
            """
        )
        st.info("The repository currently ships with the production pipeline, but the hackathon source files must be uploaded to rank real candidates.")
    elif page == "Upload JD":
        st.markdown("Use the sidebar uploaders to provide the DOCX job description and JSONL candidate set.")
        if jd_upload is None or candidates_upload is None:
            st.warning("Both files are required before ranking can run.")
        if reports:
            for title, report in reports:
                with st.expander(title, expanded=True):
                    st.write(report.notes)
                    if report.preview:
                        st.code(report.preview)
    elif page == "Candidate Ranking":
        if results is None:
            st.info("Upload the source files and click Run Ranking to generate scored candidates.")
        else:
            results_df = analytics.results_dataframe(results)
            st.dataframe(results_df, use_container_width=True)
    elif page == "Top Candidates":
        if results is None:
            st.info("No ranking has been generated yet.")
        else:
            top_results = results[:10]
            top_df = pd.DataFrame(
                [
                    {
                        "Rank": result.rank,
                        "Candidate ID": result.candidate_id,
                        "Score": result.overall_score,
                        "Matched Skills": ", ".join(result.matched_skills),
                    }
                    for result in top_results
                ]
            )
            st.dataframe(top_df, use_container_width=True)
    elif page == "Candidate Details":
        if results is None:
            st.info("Candidate explanations will appear after running the ranking pipeline.")
        else:
            selected_candidate = st.selectbox("Select candidate", [result.candidate_id for result in results])
            selected_result = next(result for result in results if result.candidate_id == selected_candidate)
            st.subheader(f"Candidate {selected_result.candidate_id}")
            st.write(selected_result.explanation)
            st.json(selected_result.breakdown)
    elif page == "Analytics Dashboard":
        if results is None or candidates is None:
            st.info("Analytics will populate once the pipeline has been executed.")
        else:
            summary = analytics.score_summary(results)
            metric_columns = st.columns(4)
            metric_columns[0].metric("Candidates", int(summary["count"]))
            metric_columns[1].metric("Average Score", f"{summary['average_score']:.2f}")
            metric_columns[2].metric("Top Score", f"{summary['max_score']:.2f}")
            metric_columns[3].metric("Lowest Score", f"{summary['min_score']:.2f}")

            st.subheader("Score Distribution")
            score_df = analytics.results_dataframe(results)
            st.bar_chart(score_df.set_index("candidate_id")["score"])

            st.subheader("Top Skills")
            top_skills = analytics.skill_frequency(candidates)
            skill_df = pd.DataFrame(top_skills, columns=["Skill", "Count"])
            st.dataframe(skill_df, use_container_width=True)
    elif page == "Download Submission":
        submission_path = st.session_state.get("submission_path")
        if submission_path and Path(submission_path).exists():
            with open(submission_path, "rb") as file_handle:
                st.download_button(
                    "Download submission.xlsx",
                    data=file_handle,
                    file_name="submission.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            is_valid, message = pipeline.validator.validate(Path(submission_path))
            st.success(message if is_valid else message)
        else:
            st.info("Run the pipeline first to generate the submission workbook.")


if __name__ == "__main__":
    main()