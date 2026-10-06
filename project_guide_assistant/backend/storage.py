import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def ensure_directory(path: Path):
    """
    폴더가 없으면 자동 생성
    """
    path.mkdir(
        parents=True,
        exist_ok=True
    )


def append_jsonl(
    file_path: Path,
    data: dict
):
    """
    JSONL 파일에 데이터 1건 추가
    """

    ensure_directory(
        file_path.parent
    )

    with file_path.open(
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(
                data,
                ensure_ascii=False
            )
            + "\n"
        )


def load_jsonl(
    file_path: Path
):
    """
    JSONL 파일 전체 읽기
    """

    if not file_path.exists():
        return []

    rows = []

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:
                rows.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:
                continue

    return rows


def overwrite_jsonl(
    file_path: Path,
    rows: list
):
    """
    JSONL 파일 전체 덮어쓰기
    """

    ensure_directory(
        file_path.parent
    )

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        for row in rows:

            file.write(
                json.dumps(
                    row,
                    ensure_ascii=False
                )
                + "\n"
            )


def save_binary_file(
    file_bytes: bytes,
    directory: Path,
    file_name: str
):
    """
    이미지 등 바이너리 파일 저장
    """

    ensure_directory(
        directory
    )

    save_path = (
        directory
        / file_name
    )

    save_path.write_bytes(
        file_bytes
    )

    return str(save_path)


def file_exists(
    file_path
):
    """
    저장된 파일 존재 여부 확인
    """

    if not file_path:
        return False

    return Path(
        file_path
    ).exists()