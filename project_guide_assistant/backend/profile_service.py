from datetime import datetime
from pathlib import Path

from backend.storage import load_jsonl, overwrite_jsonl


BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE_DIR = BASE_DIR / "data" / "profiles"
PROFILE_FILE = PROFILE_DIR / "profiles.jsonl"


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def get_all_profiles():
    return load_jsonl(PROFILE_FILE)


def get_profile(email: str):
    normalized = _normalize_email(email)

    for profile in get_all_profiles():
        if _normalize_email(profile.get("email", "")) == normalized:
            return profile

    return None


def get_or_create_profile(email: str):
    normalized = _normalize_email(email)

    if not normalized:
        raise ValueError("이메일이 필요합니다.")

    existing = get_profile(normalized)

    if existing:
        return existing

    now = datetime.now().isoformat(timespec="seconds")
    profile = {
        "email": normalized,
        "name": "",
        "created_at": now,
        "updated_at": now,
    }

    rows = get_all_profiles()
    rows.append(profile)
    overwrite_jsonl(PROFILE_FILE, rows)

    return profile


def update_profile_name(email: str, name: str):
    normalized = _normalize_email(email)
    clean_name = (name or "").strip()

    if not normalized:
        raise ValueError("이메일이 필요합니다.")

    if not clean_name:
        raise ValueError("이름을 입력해 주세요.")

    rows = get_all_profiles()
    now = datetime.now().isoformat(timespec="seconds")
    updated = None

    for profile in rows:
        if _normalize_email(profile.get("email", "")) == normalized:
            profile["email"] = normalized
            profile["name"] = clean_name
            profile["updated_at"] = now
            updated = profile
            break

    if updated is None:
        updated = {
            "email": normalized,
            "name": clean_name,
            "created_at": now,
            "updated_at": now,
        }
        rows.append(updated)

    overwrite_jsonl(PROFILE_FILE, rows)
    return updated
