"""Application shell: the floating pill nav fixed at the top of the page."""

from __future__ import annotations

import streamlit as st

# label -> (Material icon, requires a generated bundle)
NAV = [
    ("New Requirement", ":material/edit_note:", False),
    ("Artifacts", ":material/inventory_2:", True),
    ("Traceability", ":material/account_tree:", True),
    ("Export", ":material/download:", True),
    ("History", ":material/history:", False),
]


def _slug(label: str) -> str:
    return label.lower().replace(" ", "_")


def render_nav(current: str, has_bundle: bool) -> str:
    """The floating pill nav. Returns the page the user selected."""
    selected = current
    with st.container(key="navbar"):
        cols = st.columns([1.3] + [1] * len(NAV), gap="small")
        with cols[0]:
            st.markdown(
                '<div class="nav-brand"><b>SDLC Copilot</b></div>',
                unsafe_allow_html=True,
            )
        for col, (label, icon, needs_bundle) in zip(cols[1:], NAV):
            active = label == current
            disabled = needs_bundle and not has_bundle
            prefix = "navon_" if active else "navoff_"
            with col:
                with st.container(key=f"{prefix}{_slug(label)}"):
                    if st.button(
                        label,
                        icon=icon,
                        key=f"navbtn_{_slug(label)}",
                        disabled=disabled,
                        help=None if not disabled else "Generate artifacts first",
                    ):
                        selected = label
    return selected


def render_header(title: str, subtitle: str) -> None:
    """Plain heading for the non-entry pages (Artifacts/Traceability/Export)."""
    from html import escape

    st.markdown(
        f'<p class="page-title">{escape(title)}</p>'
        f'<p class="page-sub">{escape(subtitle)}</p>',
        unsafe_allow_html=True,
    )


def note(body: str, kind: str = "") -> None:
    st.markdown(f'<div class="note {kind}">{body}</div>', unsafe_allow_html=True)
