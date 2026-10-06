import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional


SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
    "dev-session-secret-change-me"
)

SESSION_TTL_SECONDS = 7 * 24 * 60 * 60


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(payload_b64: str) -> str:
    digest = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64encode(digest)


def create_session_token(
    role: str,
    user_id: str,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> str:
    now = int(time.time())
    payload = {
        "role": role,
        "user_id": user_id,
        "iat": now,
        "exp": now + ttl_seconds,
    }

    payload_json = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    payload_b64 = _b64encode(payload_json)
    signature = _sign(payload_b64)

    return f"{payload_b64}.{signature}"


def verify_session_token(token: str) -> Optional[dict]:
    if not token or "." not in token:
        return None

    try:
        payload_b64, signature = token.rsplit(".", 1)
        expected_signature = _sign(payload_b64)

        if not hmac.compare_digest(signature, expected_signature):
            return None

        payload = json.loads(
            _b64decode(payload_b64).decode("utf-8")
        )

        if int(payload.get("exp", 0)) <= int(time.time()):
            return None

        role = payload.get("role")
        user_id = (payload.get("user_id") or "").strip()

        if role not in {"worker", "admin"} or not user_id:
            return None

        return payload

    except (ValueError, TypeError, json.JSONDecodeError):
        return None
