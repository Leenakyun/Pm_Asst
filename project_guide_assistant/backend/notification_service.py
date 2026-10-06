import uuid
from datetime import datetime
from pathlib import Path

from backend.storage import append_jsonl, load_jsonl, overwrite_jsonl


BASE_DIR = Path(__file__).resolve().parent.parent
NOTIFICATION_DIR = BASE_DIR / "data" / "notifications"
NOTIFICATION_FILE = NOTIFICATION_DIR / "notifications.jsonl"


def create_notification(
    recipient_type: str,
    recipient_id: str,
    notification_type: str,
    message: str,
    inquiry_id: str | None = None,
):
    notification = {
        "notification_id": (
            datetime.now().strftime("%Y%m%d-%H%M%S")
            + "-"
            + uuid.uuid4().hex[:6]
        ),
        "recipient_type": recipient_type,
        "recipient_id": recipient_id,
        "type": notification_type,
        "message": message,
        "inquiry_id": inquiry_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "is_read": False,
    }

    append_jsonl(NOTIFICATION_FILE, notification)
    return notification


def get_all_notifications():
    return load_jsonl(NOTIFICATION_FILE)


def get_notifications(recipient_type: str, recipient_id: str):
    notifications = [
        item
        for item in get_all_notifications()
        if item.get("recipient_type") == recipient_type
        and item.get("recipient_id") == recipient_id
    ]

    return sorted(
        notifications,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )


def get_unread_count(recipient_type: str, recipient_id: str) -> int:
    return sum(
        1
        for item in get_notifications(recipient_type, recipient_id)
        if not item.get("is_read", False)
    )


def mark_all_notifications_read(recipient_type: str, recipient_id: str):
    rows = get_all_notifications()
    changed = False

    for item in rows:
        if (
            item.get("recipient_type") == recipient_type
            and item.get("recipient_id") == recipient_id
            and not item.get("is_read", False)
        ):
            item["is_read"] = True
            item["read_at"] = datetime.now().isoformat(timespec="seconds")
            changed = True

    if changed:
        overwrite_jsonl(NOTIFICATION_FILE, rows)

    return changed


def mark_notifications_read_for_inquiry(
    recipient_type: str,
    recipient_id: str,
    inquiry_id: str,
):
    rows = get_all_notifications()
    changed = False

    for item in rows:
        if (
            item.get("recipient_type") == recipient_type
            and item.get("recipient_id") == recipient_id
            and item.get("inquiry_id") == inquiry_id
            and not item.get("is_read", False)
        ):
            item["is_read"] = True
            item["read_at"] = datetime.now().isoformat(timespec="seconds")
            changed = True

    if changed:
        overwrite_jsonl(NOTIFICATION_FILE, rows)

    return changed
