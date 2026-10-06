import sys
from datetime import datetime, timedelta
from pathlib import Path

import extra_streamlit_components as stx
import streamlit as st


# =========================================================
# 프로젝트 루트 등록
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


from backend.auth import (
    validate_worker_email,
    authenticate_admin,
)
from backend.demo_seed_service import ensure_demo_seed_data
from backend.profile_service import get_or_create_profile
from backend.inquiry_service import (
    get_all_inquiries,
    get_worker_inquiries,
)
from backend.answer_service import get_latest_answers
from backend.notification_service import (
    get_notifications,
    get_unread_count,
    mark_all_notifications_read,
)
from backend.session_service import (
    create_session_token,
    verify_session_token,
)


# =========================================================
# Streamlit
# =========================================================

st.set_page_config(
    page_title="프로젝트 가이드 도우미",
    page_icon="🔎",
    layout="wide"
)


# =========================================================
# 브라우저 로그인 쿠키
# =========================================================

COOKIE_NAME = "pm_asst_session"
COOKIE_EXPIRES_DAYS = 7

cookie_manager = stx.CookieManager(
    key="pm_asst_cookie_manager"
)


# =========================================================
# 시연용 초기 데이터
# =========================================================

ensure_demo_seed_data()


# =========================================================
# 세션 기본값
# =========================================================

SESSION_DEFAULTS = {
    "logged_in": False,
    "role": None,
    "worker_id": "",      # 내부 호환용: 작업자 이메일을 저장
    "worker_email": "",
    "worker_name": "",
    "admin_id": "",
}

for key, value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 쿠키에서 로그인 복구
# =========================================================

def restore_login_from_cookie():

    # 로그아웃 직후에는
    # 남아 있는 쿠키로 자동 로그인하지 않는다.
    if st.session_state.get(
        "_logout_block_restore",
        False
    ):
        return

    if st.session_state.get(
        "logged_in"
    ):
        return

    token = cookie_manager.get(COOKIE_NAME)

    if not token:
        return

    payload = verify_session_token(token)

    if not payload:
        # 만료/위조 토큰은 다음 정상 렌더링 때 삭제한다.
        try:
            cookie_manager.delete(COOKIE_NAME)
        except Exception:
            pass
        return

    role = payload.get("role")
    user_id = (payload.get("user_id") or "").strip()

    if role == "worker":
        success, _ = validate_worker_email(user_id)
        if not success:
            return

        normalized_email = user_id.lower()
        profile = get_or_create_profile(normalized_email)

        st.session_state["logged_in"] = True
        st.session_state["role"] = "worker"
        st.session_state["worker_id"] = normalized_email
        st.session_state["worker_email"] = normalized_email
        st.session_state["worker_name"] = profile.get("name", "")

    elif role == "admin":
        st.session_state["logged_in"] = True
        st.session_state["role"] = "admin"
        st.session_state["admin_id"] = user_id


restore_login_from_cookie()


# =========================================================
# 로그아웃
# =========================================================

def logout():

    # =====================================================
    # 자동 로그인 복구 차단
    # =====================================================

    st.session_state[
        "_logout_block_restore"
    ] = True


    # =====================================================
    # 로그인 쿠키 삭제
    # =====================================================

    try:

        cookie_manager.delete(
            COOKIE_NAME
        )

    except Exception:

        pass


    # =====================================================
    # 로그인 세션 초기화
    # =====================================================

    for key, value in (
        SESSION_DEFAULTS.items()
    ):

        st.session_state[
            key
        ] = value


    # =====================================================
    # 기타 세션 데이터 정리
    # =====================================================

    keys_to_remove = [

        "worker_last_question",
        "worker_last_results",
        "worker_last_faq_results",
        "worker_last_search_id",
        "worker_last_guide_id",
        "worker_last_guide_version",
        "worker_last_search_images",
        "worker_last_vision_result",
        "worker_last_vision_search_text",

        "guide_search_pasted_images",
        "guide_search_file_upload",

        "pm_pasted_images",
        "pm_inquiry_question",
        "pm_inquiry_file_upload",
        "pm_inquiry_success",

        "selected_worker_inquiry_id",
        "selected_admin_inquiry_id",

        "new_faq_pasted_images",
        "new_faq_question",
        "new_faq_answer",
        "new_faq_image_upload",

        "delete_faq_id",
    ]


    for key in keys_to_remove:

        if key in st.session_state:

            del st.session_state[
                key
            ]


    st.rerun()


# =========================================================
# 로그인
# =========================================================

def show_login():
    st.title("🔎 프로젝트 가이드 도우미")
    st.caption(
        "작업 가이드를 검색하고 필요한 경우 "
        "관리자에게 문의할 수 있습니다."
    )
    st.divider()

    login_type = st.radio(
        "로그인 유형",
        ["작업자", "관리자"],
        horizontal=True
    )

    st.write("")

    if login_type == "작업자":
        with st.container(border=True):
            st.subheader("👷 작업자 로그인")

            worker_email = st.text_input(
                "이메일",
                placeholder="예: worker@example.com"
            )

            if st.button(
                "작업 시작",
                type="primary",
                width="stretch"
            ):
                success, message = validate_worker_email(
                    worker_email
                )

                if not success:
                    st.warning(message)
                else:
                    normalized_email = worker_email.strip().lower()
                    profile = get_or_create_profile(normalized_email)

                    st.session_state.pop(
                        "_logout_block_restore",
                        None
                    )

                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "worker"
                    st.session_state["worker_id"] = normalized_email
                    st.session_state["worker_email"] = normalized_email
                    st.session_state["worker_name"] = profile.get(
                        "name",
                        ""
                    )

                    token = create_session_token(
                        role="worker",
                        user_id=normalized_email,
                    )
                    cookie_manager.set(
                        COOKIE_NAME,
                        token,
                        expires_at=(
                            datetime.now()
                            + timedelta(days=COOKIE_EXPIRES_DAYS)
                        ),
                    )

                    st.rerun()

    else:
        with st.container(border=True):
            st.subheader("🧑‍💼 관리자 로그인")

            admin_id = st.text_input("관리자 ID")
            admin_password = st.text_input(
                "비밀번호",
                type="password"
            )

            if st.button(
                "관리자 로그인",
                type="primary",
                width="stretch"
            ):
                if authenticate_admin(
                    admin_id,
                    admin_password
                ):

                    st.session_state.pop(
                        "_logout_block_restore",
                        None
                    )
                    
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "admin"
                    st.session_state["admin_id"] = admin_id.strip()

                    token = create_session_token(
                        role="admin",
                        user_id=admin_id.strip(),
                    )
                    cookie_manager.set(
                        COOKIE_NAME,
                        token,
                        expires_at=(
                            datetime.now()
                            + timedelta(days=COOKIE_EXPIRES_DAYS)
                        ),
                    )

                    st.rerun()
                else:
                    st.error(
                        "관리자 ID 또는 비밀번호가 "
                        "올바르지 않습니다."
                    )


# =========================================================
# 로그인 상태에 따른 사이드바 표시
# =========================================================

if not st.session_state.get("logged_in", False):
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }

            [data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: block !important;
            }

            [data-testid="stSidebarCollapsedControl"] {
                display: block !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 로그인 전
# =========================================================

if not st.session_state["logged_in"]:
    show_login()
    st.stop()


# =========================================================
# 현재 사용자 알림 정보
# =========================================================

if st.session_state["role"] == "worker":
    notification_recipient_type = "worker"
    notification_recipient_id = st.session_state["worker_id"]
else:
    notification_recipient_type = "admin"
    notification_recipient_id = "admin"

notification_count = get_unread_count(
    notification_recipient_type,
    notification_recipient_id
)


# =========================================================
# 알림 팝업
# =========================================================

@st.dialog("🔔 알림", width="small")
def show_notifications():
    notifications = get_notifications(
        notification_recipient_type,
        notification_recipient_id
    )

    # 알림 창을 실제로 열면 알림 자체는 읽음 처리한다.
    # 문의함의 새 답변 숫자는 별도 상태이므로 유지된다.
    mark_all_notifications_read(
        notification_recipient_type,
        notification_recipient_id
    )

    if not notifications:
        st.info("새로운 알림이 없습니다.")
    else:
        for item in notifications[:30]:
            with st.container(border=True):
                unread_mark = (
                    "● "
                    if not item.get("is_read", False)
                    else ""
                )

                st.markdown(
                    f"**{unread_mark}{item.get('message', '')}**"
                )

                created_at = item.get("created_at", "").replace(
                    "T",
                    " "
                )

                if created_at:
                    st.caption(created_at)

    if st.button(
        "닫기",
        width="stretch",
        key="close_notification_dialog"
    ):
        st.rerun()


# =========================================================
# 사이드바
# =========================================================

with st.sidebar:
    if st.session_state["role"] == "worker":
        display_name = (
            st.session_state.get("worker_name")
            or "이름 미설정"
        )

        st.markdown(f"### 👤 {display_name}")
        st.caption(
            f"이메일: {st.session_state['worker_id']}"
        )

        if not st.session_state.get("worker_name"):
            st.info(
                "프로필에서 이름을 설정해 주세요."
            )

    elif st.session_state["role"] == "admin":
        st.markdown("### 🧑‍💼 관리자")

    st.divider()

    if st.button(
        "로그아웃",
        width="stretch"
    ):
        logout()


# =========================================================
# 상단 알림 버튼
# =========================================================

_top_left, _top_right = st.columns([12, 1])

with _top_right:
    bell_label = (
        f"🔔 {notification_count}"
        if notification_count > 0
        else "🔔"
    )

    if st.button(
        bell_label,
        key="global_notification_button",
        help="알림",
        width="stretch"
    ):
        show_notifications()


# =========================================================
# Navigation 숫자 계산
# =========================================================

FRONTEND_DIR = Path(__file__).resolve().parent
answers = get_latest_answers()


if st.session_state["role"] == "worker":
    worker_id = st.session_state["worker_id"]
    worker_inquiries = get_worker_inquiries(worker_id)

    unchecked_answer_count = sum(
        1
        for inquiry in worker_inquiries
        if inquiry.get("inquiry_id") in answers
        and not inquiry.get("worker_answer_checked_at")
    )

    inquiry_title = (
        f"내 문의 ({unchecked_answer_count})"
        if unchecked_answer_count > 0
        else "내 문의"
    )

    pages = {
        "작업": [
            st.Page(
                str(FRONTEND_DIR / "pages" / "worker.py"),
                title="가이드 검색",
                icon="🔎"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "worker_guide.py"),
                title="전체 가이드",
                icon="📖"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "worker_faqs.py"),
                title="FAQ",
                icon="💡"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "worker_inquiries.py"),
                title=inquiry_title,
                icon="📬"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "worker_profile.py"),
                title="프로필",
                icon="👤"
            ),
        ]
    }


elif st.session_state["role"] == "admin":
    all_inquiries = get_all_inquiries()

    waiting_count = sum(
        1
        for inquiry in all_inquiries
        if inquiry.get("inquiry_id") not in answers
    )

    admin_inquiry_title = (
        f"문의 관리 ({waiting_count})"
        if waiting_count > 0
        else "문의 관리"
    )

    pages = {
        "관리": [
            st.Page(
                str(FRONTEND_DIR / "pages" / "admin.py"),
                title="가이드 관리",
                icon="📘"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "admin_faqs.py"),
                title="FAQ 관리",
                icon="💡"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "admin_inquiries.py"),
                title=admin_inquiry_title,
                icon="📨"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "admin_dashboard.py"),
                title="운영 대시보드",
                icon="📊"
            ),
            st.Page(
                str(FRONTEND_DIR / "pages" / "admin_settings.py"),
                title="프로젝트 설정",
                icon="⚙️"
            ),
        ]
    }

else:
    logout()
    st.stop()


navigation = st.navigation(pages)
navigation.run()
