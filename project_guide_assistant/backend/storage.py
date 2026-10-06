import json
import os
from pathlib import Path

from backend.database_service import (
    database_enabled,
    append_collection,
    load_collection,
    overwrite_collection,
)


BASE_DIR = Path(__file__).resolve().parent.parent

# 로컬에서는 프로젝트 내부 data/를 사용하고,
# Railway에서는 APP_DATA_DIR=/app/data 로 지정해 Volume을 사용한다.
_configured_data_dir = os.getenv("APP_DATA_DIR", "").strip()

if _configured_data_dir:
    DATA_DIR = Path(_configured_data_dir).expanduser()
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR = DATA_DIR.resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_directory(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _collection_name(file_path: Path) -> str:
    """
    기존 JSONL 경로를 PostgreSQL collection 이름으로 변환한다.

    예:
    /app/data/faqs/faqs.jsonl -> faqs/faqs.jsonl
    """
    path = Path(file_path).resolve()

    try:
        relative = path.relative_to(DATA_DIR)
        return relative.as_posix()
    except ValueError:
        return path.as_posix()


def append_jsonl(file_path: Path, data: dict):
    """
    DATABASE_URL이 있으면 PostgreSQL JSONB 저장소를 사용하고,
    로컬 개발처럼 DATABASE_URL이 없으면 기존 JSONL 파일을 사용한다.
    """
    if database_enabled():
        append_collection(
            _collection_name(file_path),
            data,
        )
        return

    ensure_directory(file_path.parent)

    with file_path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(data, ensure_ascii=False)
            + "\n"
        )


def load_jsonl(file_path: Path):
    if database_enabled():
        return load_collection(
            _collection_name(file_path)
        )

    if not file_path.exists():
        return []

    rows = []

    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return rows


def overwrite_jsonl(file_path: Path, rows: list):
    if database_enabled():
        overwrite_collection(
            _collection_name(file_path),
            rows,
        )
        return

    ensure_directory(file_path.parent)

    with file_path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(
                json.dumps(row, ensure_ascii=False)
                + "\n"
            )


def save_binary_file(
    file_bytes: bytes,
    directory: Path,
    file_name: str,
):
    """
    PDF/DOCX/TXT/이미지는 DB가 아니라 Railway Volume에 저장한다.
    """
    ensure_directory(directory)

    save_path = directory / file_name
    save_path.write_bytes(file_bytes)

    return str(save_path)


def file_exists(file_path):
    if not file_path:
        return False

    return Path(file_path).exists()
