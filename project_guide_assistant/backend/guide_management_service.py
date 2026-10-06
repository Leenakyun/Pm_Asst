import uuid

from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from backend.models import GuideVersion
from backend.storage import (
    DATA_DIR,
    load_jsonl,
    overwrite_jsonl,
    save_binary_file
)


# =========================================================
# 저장 경로
# =========================================================

GUIDE_DIR = (
    DATA_DIR
    / "guides"
)

GUIDE_FILE_DIR = (
    GUIDE_DIR
    / "files"
)

GUIDE_REGISTRY = (
    GUIDE_DIR
    / "guides.jsonl"
)


# =========================================================
# 전체 가이드 목록
# =========================================================

def get_all_guides():

    guides = load_jsonl(
        GUIDE_REGISTRY
    )

    return sorted(
        guides,
        key=lambda x: x.get(
            "uploaded_at",
            ""
        ),
        reverse=True
    )


# =========================================================
# 현재 가이드
# =========================================================

def get_active_guide():

    guides = get_all_guides()

    for guide in guides:

        if guide.get(
            "is_active"
        ):

            return guide

    return None


# =========================================================
# 가이드 업로드
# =========================================================

def upload_guide(
    file_bytes: bytes,
    original_file_name: str,
    version: str
):

    if not version.strip():

        raise ValueError(
            "가이드 버전을 입력해 주세요."
        )


    guides = get_all_guides()


    # 같은 버전 중복 방지
    for guide in guides:

        if guide.get(
            "version"
        ) == version.strip():

            raise ValueError(
                "이미 등록된 가이드 버전입니다."
            )


    # 기존 가이드 비활성화
    for guide in guides:

        guide[
            "is_active"
        ] = False


    guide_id = (
        uuid.uuid4().hex[:10]
    )


    extension = Path(
        original_file_name
    ).suffix.lower()


    saved_file_name = (
        f"{guide_id}{extension}"
    )


    file_path = save_binary_file(
        file_bytes=file_bytes,
        directory=GUIDE_FILE_DIR,
        file_name=saved_file_name
    )


    guide = GuideVersion(

        guide_id=guide_id,

        version=version.strip(),

        file_name=original_file_name,

        file_path=file_path,

        uploaded_at=(
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),

        is_active=True
    )


    guides.append(
        asdict(guide)
    )


    overwrite_jsonl(
        GUIDE_REGISTRY,
        guides
    )


    return asdict(
        guide
    )


# =========================================================
# 현재 버전 변경
# =========================================================

def activate_guide(
    guide_id: str
):

    guides = get_all_guides()

    found = False


    for guide in guides:

        if guide.get(
            "guide_id"
        ) == guide_id:

            guide[
                "is_active"
            ] = True

            found = True

        else:

            guide[
                "is_active"
            ] = False


    if not found:

        raise ValueError(
            "해당 가이드를 찾을 수 없습니다."
        )


    overwrite_jsonl(
        GUIDE_REGISTRY,
        guides
    )


# =========================================================
# 가이드 삭제
# =========================================================

def delete_guide(
    guide_id: str
):

    guides = get_all_guides()

    target = None


    for guide in guides:

        if guide.get(
            "guide_id"
        ) == guide_id:

            target = guide

            break


    if target is None:

        raise ValueError(
            "해당 가이드를 찾을 수 없습니다."
        )


    # 현재 사용 중인 버전은 바로 삭제하지 못하게 함
    if target.get(
        "is_active"
    ):

        raise ValueError(
            "현재 사용 중인 가이드는 삭제할 수 없습니다. "
            "다른 버전을 현재 버전으로 변경한 뒤 삭제해 주세요."
        )


    file_path = Path(
        target[
            "file_path"
        ]
    )


    if file_path.exists():

        file_path.unlink()


    guides = [

        guide

        for guide in guides

        if guide.get(
            "guide_id"
        ) != guide_id
    ]


    overwrite_jsonl(
        GUIDE_REGISTRY,
        guides
    )