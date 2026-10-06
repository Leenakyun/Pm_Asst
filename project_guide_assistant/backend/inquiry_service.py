import uuid

from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from backend.models import Inquiry
from backend.notification_service import create_notification
from backend.storage import (
    DATA_DIR,
    append_jsonl,
    load_jsonl,
    overwrite_jsonl,
    save_binary_file
)


INQUIRY_DIR = (
    DATA_DIR
    / "pm_inquiries"
)

WORKER_IMAGE_DIR = (
    INQUIRY_DIR
    / "worker_images"
)

INQUIRY_LOG = (
    INQUIRY_DIR
    / "pm_inquiries.jsonl"
)


def create_inquiry(
    worker_id: str,
    worker_name: str,
    question: str,
    search_results: list,
    faq_results: list | None = None,
    uploaded_images: list | None = None,
    search_id: str | None = None,
    guide_id: str | None = None,
    guide_version: str | None = None
):
    inquiry_id = (
        datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )
        + "-"
        + uuid.uuid4().hex[:6]
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
                f"{inquiry_id}_{index}"
                f"{extension}"
            )

            saved_path = save_binary_file(
                file_bytes=image.getvalue(),
                directory=WORKER_IMAGE_DIR,
                file_name=file_name
            )

            image_paths.append(saved_path)

    inquiry = Inquiry(
        inquiry_id=inquiry_id,
        worker_id=worker_id,
        worker_name=worker_name,
        question=question,
        created_at=(
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),
        status="waiting",
        worker_images=image_paths,
        search_results=search_results,
        faq_results=faq_results or [],
        search_id=search_id,
        guide_id=guide_id,
        guide_version=guide_version,
        worker_answer_checked_at=None,
    )

    inquiry_data = asdict(inquiry)

    append_jsonl(
        INQUIRY_LOG,
        inquiry_data
    )

    worker_display = worker_name.strip() or worker_id
    create_notification(
        recipient_type="admin",
        recipient_id="admin",
        notification_type="new_inquiry",
        message=f"{worker_display}님이 새 문의를 등록했습니다.",
        inquiry_id=inquiry_id,
    )

    return inquiry_data


def get_all_inquiries():
    return load_jsonl(INQUIRY_LOG)


def get_inquiry_by_id(inquiry_id: str):
    for inquiry in get_all_inquiries():
        if inquiry.get("inquiry_id") == inquiry_id:
            return inquiry
    return None


def get_worker_inquiries(worker_id: str):
    inquiries = get_all_inquiries()

    return [
        inquiry
        for inquiry in inquiries
        if inquiry.get("worker_id") == worker_id
    ]


def get_worker_inquiry_number(inquiry_id: str) -> int | None:
    target = get_inquiry_by_id(inquiry_id)

    if not target:
        return None

    worker_id = target.get("worker_id", "")
    worker_inquiries = sorted(
        get_worker_inquiries(worker_id),
        key=lambda item: item.get("created_at", ""),
    )

    for index, inquiry in enumerate(worker_inquiries, start=1):
        if inquiry.get("inquiry_id") == inquiry_id:
            return index

    return None


def _update_answer_checked_at(
    inquiry_id: str,
    checked_at: str | None
):
    rows = get_all_inquiries()
    changed = False

    for inquiry in rows:
        if inquiry.get("inquiry_id") == inquiry_id:
            inquiry["worker_answer_checked_at"] = checked_at
            changed = True
            break

    if changed:
        overwrite_jsonl(INQUIRY_LOG, rows)

    return changed


def mark_worker_answer_checked(inquiry_id: str):
    return _update_answer_checked_at(
        inquiry_id,
        datetime.now().isoformat(timespec="seconds")
    )


def mark_worker_answer_unchecked(inquiry_id: str):
    return _update_answer_checked_at(
        inquiry_id,
        None
    )
