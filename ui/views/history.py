"""History: browse, reload or delete previously generated pipeline runs.

Every generation is already persisted as JSON under ``data/runs/`` by
``app.storage.file_storage.save_pipeline_result``. This view just lists
those files, and lets the user bring one back into the app (as if it had
just been generated) or remove it.
"""

from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from app.bundle_adapter import build_bundle_from_pipeline
from app.storage.file_storage import (
    delete_pipeline_run,
    list_pipeline_runs,
    load_pipeline_result,
)


def _format_timestamp(raw: str | None) -> str:
    """'2026-09-27T07:21:23.830645+00:00' -> '27 Sep 2026, 07:21'."""
    if not raw:
        return "Unknown time"
    try:
        return datetime.fromisoformat(raw).strftime("%d %b %Y, %H:%M")
    except ValueError:
        return raw


def _load_run(run_id: str) -> None:
    """Bring a saved run back as the active bundle and jump to Artifacts."""
    result = load_pipeline_result(run_id)

    if result is None:
        st.session_state.history_error = f"Run {run_id} could not be found."
        return

    bundle = build_bundle_from_pipeline(result)

    st.session_state.bundle = bundle
    st.session_state.requirement_text = result["business_requirement"]["text"]
    st.session_state.run_id = run_id
    st.session_state.history_error = None
    st.session_state.page = "Artifacts"

    st.rerun()


def _delete_run(run_id: str) -> None:
    """Remove a saved run file, keeping the active bundle untouched."""
    delete_pipeline_run(run_id)

    if st.session_state.get("run_id") == run_id:
        st.session_state.run_id = None

    st.rerun()


def render() -> None:
    st.markdown(
        '<p class="sec">Past runs</p>'
        '<p class="sec-s">Every generated requirement is saved automatically. '
        "Reload one to bring its artifacts back into Artifacts, Traceability "
        "and Export, or remove it for good.</p>",
        unsafe_allow_html=True,
    )

    error = st.session_state.get("history_error")
    if error:
        st.markdown(f'<div class="note">{escape(error)}</div>', unsafe_allow_html=True)

    runs = list_pipeline_runs()

    if not runs:
        st.markdown(
            '<div class="note">No runs yet. Generate artifacts from '
            "New Requirement and they will show up here.</div>",
            unsafe_allow_html=True,
        )
        return

    active_run_id = st.session_state.get("run_id")

    for run in runs:
        run_id = run.get("run_id", "")
        requirement_text = run.get("business_requirement", "") or "(no requirement text)"
        preview = (
            requirement_text
            if len(requirement_text) <= 160
            else requirement_text[:157] + "..."
        )
        is_active = run_id == active_run_id
        is_failed = run.get("status") == "failed"

        with st.container(key=f"history_row_{run_id}"):
            status_tag = ""
            if is_failed:
                status_tag = ' <span class="sample-tag" style="background:#fdecea;color:#b3261e">Failed</span>'
            elif is_active:
                status_tag = ' <span class="sample-tag">Active</span>'

            error_html = ""
            if is_failed and run.get("error"):
                error_html = f'<p class="body" style="margin-top:6px;color:#b3261e">{escape(run["error"])}</p>'

            st.markdown(
                '<div class="child">'
                f'<div class="child-h">{escape(run_id)}{status_tag}</div>'
                f'<div class="lvl-d">{escape(_format_timestamp(run.get("created_at")))}</div>'
                f'<p class="body" style="margin-top:6px">{escape(preview)}</p>'
                f"{error_html}"
                "</div>",
                unsafe_allow_html=True,
            )

            load_col, delete_col, _spacer = st.columns([1, 1, 4], gap="small")
            if not is_failed:
                with load_col:
                    st.button(
                        "Load",
                        key=f"history_load_{run_id}",
                        type="primary",
                        width="stretch",
                        on_click=_load_run,
                        args=(run_id,),
                    )
            with delete_col:
                st.button(
                    "Delete",
                    key=f"history_delete_{run_id}",
                    width="stretch",
                    on_click=_delete_run,
                    args=(run_id,),
                )