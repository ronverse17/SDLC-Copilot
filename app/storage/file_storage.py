from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Project root:
# ai-sdlc-copilot/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Storage directory:
STORAGE_DIR = PROJECT_ROOT / "data" / "runs"


def _ensure_storage_dir() -> None:
    """Create the storage directory if it does not exist."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _make_run_id() -> str:
    """Generate a unique ID for each pipeline run."""
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    return f"RUN-{timestamp}"


def save_pipeline_result(
    result: dict[str, Any],
) -> str:
    """
    Save one complete pipeline execution as a JSON file.

    Returns:
        The generated run ID.
    """

    _ensure_storage_dir()

    run_id = _make_run_id()

    file_path = STORAGE_DIR / f"{run_id}.json"

    data = {
        "run_id": run_id,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "business_requirement": result[
            "business_requirement"
        ],

        "epics": result["epics"],

        "user_stories": result[
            "user_stories"
        ],

        "acceptance_criteria": result[
            "acceptance_criteria"
        ],

        "test_cases": result[
            "test_cases"
        ],
    }

    # TraceabilityReport is a Pydantic object,
    # so convert it into a dictionary.
    traceability = result.get(
        "traceability"
    )

    if traceability is not None:

        if hasattr(
            traceability,
            "model_dump"
        ):
            data["traceability"] = (
                traceability.model_dump()
            )

        else:
            data["traceability"] = traceability

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return run_id

def save_failed_pipeline_run(
    requirement_text: str,
    error_message: str,
    business_requirement_id: str = "BR-001",
) -> str:
    """
    Save a failed pipeline attempt, so it shows up in History with
    the requirement text and the error that stopped it.
    """

    _ensure_storage_dir()

    run_id = _make_run_id()

    file_path = STORAGE_DIR / f"{run_id}.json"

    data = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "error": error_message,
        "business_requirement": {
            "id": business_requirement_id,
            "text": requirement_text,
        },
    }

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    return run_id

def load_pipeline_result(
    run_id: str,
) -> dict[str, Any] | None:
    """
    Load a previously saved pipeline execution.
    """

    file_path = STORAGE_DIR / f"{run_id}.json"

    if not file_path.exists():
        return None

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def list_pipeline_runs() -> list[dict[str, Any]]:
    """
    Return basic information about all saved runs.
    """

    _ensure_storage_dir()

    runs = []

    for file_path in sorted(
        STORAGE_DIR.glob("RUN-*.json"),
        reverse=True,
    ):

        try:

            with file_path.open(
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            runs.append(
                {
                    "run_id": data.get(
                        "run_id"
                    ),

                    "created_at": data.get(
                        "created_at"
                    ),

                    "business_requirement": data.get(
                        "business_requirement",
                        {},
                    ).get(
                        "text",
                        "",
                    ),

                    "status": data.get("status", "success"),
                    "error": data.get("error"),
                }
            )

        except (
            json.JSONDecodeError,
            OSError,
        ):
            # Ignore corrupted/unreadable files.
            continue

    return runs


def delete_pipeline_run(
    run_id: str,
) -> bool:
    """
    Delete one saved pipeline execution.

    Returns:
        True if deleted, otherwise False.
    """

    file_path = STORAGE_DIR / f"{run_id}.json"

    if not file_path.exists():
        return False

    file_path.unlink()

    return True