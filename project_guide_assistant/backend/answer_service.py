import uuid

from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from backend.models import PMAnswer
from backend.inquiry_service import (
    get_inquiry_by_id,
    get_worker_inquiry_number,
    mark_worker_answer_unchecked,
)
from backend.notification_service import create_notification
from backend.storage import (
    append_jsonl,
    load_jsonl,
    save_binary_file
)


BASE_DIR = Path(__file__).resolve().parent.parent

ANSWER_DIR = (
    BASE_DIR
    / "data"
    / "pm_answers"
)

PM_IMAGE_DIR = (
    ANSWER_DIR
    / "pm_images"
)

ANSWER_LOG = (
    ANSWER_DIR
    / "pm_answers.jsonl"
)


def create_answer(
    inquiry_id: str,
    pm_answer: str,
    category: str | None = None,
    uploaded_images: list | None = None
):
    """
    PM 답변 저장.
    답변이 새로 등록되면 작업자의 확인 상태를 미확인으로 되돌리고
    해당 작업자에게 알림을 생성한다.
    """

    pm_answer = pm_answer.strip()

    if not pm_answer:
        raise ValueError(
            "답변 내용을 입력해 주세요."
        )

    inquiry = get_inquiry_by_id(inquiry_id)

    if not inquiry:
        raise ValueError(
            "해당 문의를 찾을 수 없습니다."
        )

    image_paths = []

    if uploaded_images:
        for index, image in enumerate(
            uploaded_images,
            start=1
        ):
            extension = Path(
                image.name
            ).suffix.lower()

            if not extension:
                extension = ".png"

            file_name = (
                f"{inquiry_id}_pm_"
                f"{uuid.uuid4().hex[:6]}_"
                f"{index}"
                f"{extension}"
            )

            saved_path = save_binary_file(
                file_bytes=image.getvalue(),
                directory=PM_IMAGE_DIR,
                file_name=file_name
            )

            image_paths.append(saved_path)

    answer = PMAnswer(
        inquiry_id=inquiry_id,
        pm_answer=pm_answer,
        answered_at=(
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),
        status="answered",
        category=category,
        pm_images=image_paths
    )

    answer_data = asdict(answer)

    append_jsonl(
        ANSWER_LOG,
        answer_data
    )

    mark_worker_answer_unchecked(inquiry_id)

    worker_id = inquiry.get("worker_id", "")
    inquiry_number = get_worker_inquiry_number(inquiry_id)

    if inquiry_number is not None:
        message = (
            f"관리자가 {inquiry_number}번 문의에 "
            "답변을 달았습니다."
        )
    else:
        message = "관리자가 문의에 답변을 달았습니다."

    if worker_id:
        create_notification(
            recipient_type="worker",
            recipient_id=worker_id,
            notification_type="inquiry_answer",
            message=message,
            inquiry_id=inquiry_id,
        )

    return answer_data


def get_all_answers():
    """전체 답변 조회"""
    return load_jsonl(ANSWER_LOG)


def get_latest_answers():
    """문의별 최신 답변"""
    answers = get_all_answers()
    latest = {}

    for answer in answers:
        inquiry_id = answer.get("inquiry_id")

        if inquiry_id:
            latest[inquiry_id] = answer

    return latest


def get_answer_by_inquiry_id(inquiry_id: str):
    """특정 문의 최신 답변"""
    return get_latest_answers().get(inquiry_id)
