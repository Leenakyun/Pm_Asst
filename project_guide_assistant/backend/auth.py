import os
import re


# =========================================================
# 관리자 계정
# =========================================================

ADMIN_ID = os.getenv(
    "ADMIN_ID",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "4864"
)


# =========================================================
# 작업자 이메일 로그인 확인
# =========================================================

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_worker_email(email: str) -> tuple[bool, str]:
    email = (email or "").strip().lower()

    if not email:
        return False, "이메일을 입력해 주세요."

    if not EMAIL_PATTERN.match(email):
        return False, "올바른 이메일 형식을 입력해 주세요."

    return True, ""


# 기존 코드와의 호환용
# 새 로그인 화면에서는 validate_worker_email을 사용한다.
def validate_worker(worker_id: str, worker_name: str = "") -> tuple[bool, str]:
    return validate_worker_email(worker_id)


# =========================================================
# 관리자 로그인 확인
# =========================================================

def authenticate_admin(
    admin_id: str,
    password: str
) -> bool:
    return (
        admin_id.strip() == ADMIN_ID
        and password == ADMIN_PASSWORD
    )
