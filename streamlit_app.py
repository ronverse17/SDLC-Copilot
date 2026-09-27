"""AI-Powered SDLC Copilot.

Enter one business requirement; review the generated Epic -> User Story ->
Acceptance Criteria -> Test Case chain; trace it end to end; export it as CSV.

Pipeline results are stored in the local file system under:
    data/runs/
"""

from __future__ import annotations

import streamlit as st

from ui import theme
from ui.shell import render_header, render_nav
from ui.views import artifacts as artifacts_view
from ui.views import export as export_view
from ui.views import generating as generating_view
from ui.views import history as history_view
from ui.views import new_requirement as new_requirement_view
from ui.views import traceability as traceability_view

from app.pipeline import run_pipeline
from app.bundle_adapter import build_bundle_from_pipeline
from app.storage.file_storage import save_pipeline_result, save_failed_pipeline_run


PAGES = {
    "New Requirement": (
        "New Requirement",
        "Turn one business requirement into a complete, reviewable and "
        "traceable SDLC artifact chain.",
    ),
    "Artifacts": (
        "Artifacts",
        "Review the generated epics, stories, acceptance criteria and test cases.",
    ),
    "Traceability": (
        "Traceability",
        "Follow every test case back to the requirement it came from.",
    ),
    "Export": (
        "Export",
        "Download all artifacts with their IDs and parent references.",
    ),
    "History": (
        "History",
        "Reload or delete artifacts generated in a previous run.",
    ),
}


# ============================================================
# SESSION STATE
# ============================================================

def _init_state() -> None:
    """Initialize Streamlit session state."""

    defaults = {
        "page": "New Requirement",
        "bundle": None,
        "requirement_text": "",
        "error": None,
        "pending": None,
        "run_id": None,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


# ============================================================
# START GENERATION
# ============================================================

def _generate(requirement: str) -> None:
    """Validate the requirement and start the generation process."""

    requirement = requirement.strip()

    if not requirement:

        st.session_state.error = (
            "Enter a business requirement before generating artifacts."
        )

        return

    st.session_state.error = None

    # Store requirement temporarily.
    # The next Streamlit run will execute the pipeline.
    st.session_state.pending = requirement

    st.rerun()


# ============================================================
# RUN PIPELINE + FILE STORAGE
# ============================================================

def _run_generation() -> None:
    """
    Run the complete SDLC pipeline.

    Flow:

        Requirement
            ↓
        run_pipeline()
            ↓
        save_pipeline_result()
            ↓
        build_bundle_from_pipeline()
            ↓
        Streamlit UI
    """

    requirement = st.session_state.pending

    if not requirement:
        return

    with st.spinner(
        "Calling the pipeline — this can take 30–90 seconds..."
    ):

        try:

            # =================================================
            # STEP 1 — RUN AI SDLC PIPELINE
            # =================================================

            result = run_pipeline(
                requirement,
                business_requirement_id="BR-001",
            )

            # =================================================
            # STEP 2 — SAVE RESULT TO FILE SYSTEM
            # =================================================

            run_id = save_pipeline_result(result)

            # Store the generated run ID.
            st.session_state.run_id = run_id

        except Exception as exc:

            save_failed_pipeline_run(
                requirement,
                str(exc),
                business_requirement_id="BR-001",
            )

            st.session_state.error = (
                f"Generation failed: {exc}"
            )

            st.session_state.pending = None
            st.session_state.page = "New Requirement"

            st.rerun()

            return

    # =========================================================
    # STEP 3 — CONVERT PIPELINE RESULT FOR UI
    # =========================================================

    bundle = build_bundle_from_pipeline(result)

    # =========================================================
    # STEP 4 — SHOW GENERATION RESULT
    # =========================================================

    generating_view.run(
        bundle,
        requirement,
    )

    # =========================================================
    # STEP 5 — STORE CURRENT RESULT IN SESSION
    # =========================================================

    st.session_state.bundle = bundle

    st.session_state.requirement_text = requirement

    st.session_state.pending = None

    st.session_state.page = "Artifacts"

    st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Streamlit configuration
    # --------------------------------------------------------

    st.set_page_config(
        page_title="SDLC Copilot",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # --------------------------------------------------------
    # Theme
    # --------------------------------------------------------

    theme.inject()

    # --------------------------------------------------------
    # Initialize session state
    # --------------------------------------------------------

    _init_state()

    bundle = st.session_state.bundle

    # ========================================================
    # PENDING GENERATION
    # ========================================================

    if st.session_state.pending:

        render_nav(
            st.session_state.page,
            bundle is not None,
        )

        _run_generation()

        return

    # ========================================================
    # NAVIGATION
    # ========================================================

    chosen = render_nav(
        st.session_state.page,
        bundle is not None,
    )

    if chosen != st.session_state.page:

        st.session_state.page = chosen

        st.rerun()

    page = st.session_state.page

    # ========================================================
    # NEW REQUIREMENT
    # ========================================================

    if page == "New Requirement":

        requirement, clicked = (
            new_requirement_view.render(
                st.session_state.error
            )
        )

        if clicked:

            _generate(requirement)

    # ========================================================
    # ARTIFACTS
    # ========================================================

    elif page == "Artifacts":

        title, subtitle = PAGES[page]

        render_header(
            title,
            subtitle,
        )

        artifacts_view.render(
            bundle,
            st.session_state.requirement_text,
        )

    # ========================================================
    # TRACEABILITY
    # ========================================================

    elif page == "Traceability":

        title, subtitle = PAGES[page]

        render_header(
            title,
            subtitle,
        )

        traceability_view.render(
            bundle
        )

    # ========================================================
    # EXPORT
    # ========================================================

    elif page == "Export":

        title, subtitle = PAGES[page]

        render_header(
            title,
            subtitle,
        )

        export_view.render(
            bundle
        )
    # ========================================================
    # HISTORY
    # ========================================================

    elif page == "History":

        title, subtitle = PAGES[page]

        render_header(
            title,
            subtitle,
        )

        history_view.render()

# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()