from pathlib import Path

from backend.storage import (
    DATA_DIR,
    load_jsonl,
    overwrite_jsonl
)


# =========================================================
# 경로
# =========================================================

SETTINGS_DIR = (
    DATA_DIR
    / "settings"
)

SETTINGS_FILE = (
    SETTINGS_DIR
    / "project_settings.jsonl"
)


# =========================================================
# 기본 설정
# =========================================================

DEFAULT_SETTINGS = {
    "vision_enabled": False,
    "vision_detail": "low",
}


# =========================================================
# 설정 조회
# =========================================================

def get_project_settings() -> dict:

    rows = load_jsonl(
        SETTINGS_FILE
    )

    settings = (
        DEFAULT_SETTINGS.copy()
    )

    if rows:

        settings.update(
            rows[0]
        )

    return settings


# =========================================================
# 설정 저장
# =========================================================

def save_project_settings(
    settings: dict
):

    current = (
        get_project_settings()
    )

    current.update(
        settings
    )

    overwrite_jsonl(
        SETTINGS_FILE,
        [current]
    )

    return current


# =========================================================
# Vision 설정
# =========================================================

def set_vision_settings(
    enabled: bool,
    detail: str = "low"
):

    if detail not in [
        "low",
        "high"
    ]:

        detail = "low"

    return save_project_settings({
        "vision_enabled":
            bool(enabled),

        "vision_detail":
            detail,
    })


def is_vision_enabled() -> bool:

    settings = (
        get_project_settings()
    )

    return bool(
        settings.get(
            "vision_enabled",
            False
        )
    )