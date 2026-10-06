import sys
from pathlib import Path

import streamlit as st


# =========================================================
# 프로젝트 루트
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.append(
        str(BASE_DIR)
    )


# =========================================================
# 백엔드
# =========================================================

from backend.inquiry_service import (
    get_worker_inquiries,
    mark_worker_answer_checked
)

from backend.notification_service import (
    mark_notifications_read_for_inquiry
)

from backend.answer_service import (
    get_latest_answers
)


# =========================================================
# 접근 권한
# =========================================================

if (
    not st.session_state.get("logged_in")
    or st.session_state.get("role") != "worker"
):
    st.error(
        "작업자만 접근할 수 있습니다."
    )
    st.stop()


# =========================================================
# 작업자 정보
# =========================================================

worker_id = st.session_state.get(
    "worker_id",
    ""
)

worker_name = st.session_state.get(
    "worker_name",
    ""
)


if not worker_id:
    st.error(
        "작업자 로그인 정보가 없습니다."
    )
    st.stop()


# =========================================================
# 문의 상세 팝업
# =========================================================

@st.dialog(
    "📬 문의 상세",
    width="large"
)
def show_inquiry_dialog(
    inquiry: dict,
    answer: dict | None
):

    inquiry_id = inquiry.get(
        "inquiry_id",
        ""
    )

    created_at = (
        inquiry.get(
            "created_at",
            ""
        )
        .replace(
            "T",
            " "
        )
    )


    # -----------------------------------------------------
    # 상태
    # -----------------------------------------------------

    col1, col2 = st.columns(
        [3, 1]
    )

    with col1:

        st.markdown(
            "### 내가 보낸 문의"
        )

    with col2:

        if answer:

            st.success(
                "✅ 답변 완료"
            )

        else:

            st.warning(
                "⏳ 답변 대기"
            )


    st.caption(
        f"문의 시각: {created_at}"
    )

    st.caption(
        f"문의 번호: {inquiry_id}"
    )

    st.divider()


    # =====================================================
    # 문의 내용
    # =====================================================

    st.markdown(
        "### 💬 문의 내용"
    )

    st.write(
        inquiry.get(
            "question",
            ""
        )
    )


    # =====================================================
    # 내가 첨부한 이미지
    # =====================================================

    worker_images = inquiry.get(
        "worker_images",
        []
    )


    if worker_images:

        st.markdown(
            "### 🖼️ 첨부한 작업 화면"
        )

        image_columns = st.columns(
            min(
                len(worker_images),
                2
            )
        )

        for index, image_path in enumerate(
            worker_images
        ):

            path = Path(
                image_path
            )

            if not path.exists():
                continue

            with image_columns[
                index % len(image_columns)
            ]:

                st.image(
                    str(path),
                    width="stretch"
                )


    # =====================================================
    # 답변 대기
    # =====================================================

    if not answer:

        st.divider()

        st.info(
            "관리자 답변을 기다리고 있습니다."
        )

        if st.button(
            "닫기",
            width="stretch",
            key=f"close_waiting_{inquiry_id}"
        ):

            st.session_state[
                "selected_worker_inquiry_id"
            ] = None

            st.rerun()

        return


    # =====================================================
    # 관리자 답변
    # =====================================================

    st.divider()

    st.markdown(
        "### ✅ 관리자 답변"
    )


    category = answer.get(
        "category"
    )

    if category:

        st.caption(
            f"문의 분류: {category}"
        )


    st.write(
        answer.get(
            "pm_answer",
            ""
        )
    )


    # =====================================================
    # 관리자 첨부 이미지
    # =====================================================

    pm_images = answer.get(
        "pm_images",
        []
    )


    if pm_images:

        st.markdown(
            "### 🖼️ 답변 첨부 이미지"
        )

        image_columns = st.columns(
            min(
                len(pm_images),
                2
            )
        )

        for index, image_path in enumerate(
            pm_images
        ):

            path = Path(
                image_path
            )

            if not path.exists():
                continue

            with image_columns[
                index % len(image_columns)
            ]:

                st.image(
                    str(path),
                    width="stretch"
                )


    # =====================================================
    # 답변 시각
    # =====================================================

    answered_at = (
        answer.get(
            "answered_at",
            ""
        )
        .replace(
            "T",
            " "
        )
    )


    if answered_at:

        st.caption(
            f"답변 시각: {answered_at}"
        )


    st.divider()


    if st.button(
        "닫기",
        width="stretch",
        key=f"close_answered_{inquiry_id}"
    ):

        st.session_state[
            "selected_worker_inquiry_id"
        ] = None

        st.rerun()


# =========================================================
# 페이지
# =========================================================

st.title(
    "📬 내 문의"
)

st.caption(
    "관리자에게 전달한 문의와 "
    "답변 상태를 확인할 수 있습니다."
)


# =========================================================
# 문의 / 답변 불러오기
# =========================================================

inquiries = get_worker_inquiries(
    worker_id
)

answers = get_latest_answers()


# =========================================================
# 상태 숫자
# =========================================================

total_count = len(
    inquiries
)

waiting_count = sum(
    1
    for inquiry in inquiries
    if inquiry.get(
        "inquiry_id"
    ) not in answers
)

answered_count = (
    total_count
    - waiting_count
)


col1, col2, col3 = st.columns(
    3
)

with col1:

    st.metric(
        "전체 문의",
        total_count
    )

with col2:

    st.metric(
        "답변 대기",
        waiting_count
    )

with col3:

    st.metric(
        "답변 완료",
        answered_count
    )


# =========================================================
# 상태 필터
# =========================================================

filter_option = st.radio(
    "문의 상태",
    [
        "전체",
        "답변 대기",
        "답변 완료"
    ],
    horizontal=True
)


# =========================================================
# 검색
# =========================================================

search_keyword = st.text_input(
    "문의 검색",
    placeholder="문의 내용을 검색해 보세요."
)


# =========================================================
# 새로고침
# =========================================================

if st.button(
    "🔄 답변 상태 새로고침",
    width="stretch"
):

    st.rerun()


st.divider()


# =========================================================
# 최신순 정렬
# =========================================================

inquiries = sorted(
    inquiries,
    key=lambda x:
        x.get(
            "created_at",
            ""
        ),
    reverse=True
)


# =========================================================
# 필터링
# =========================================================

filtered_inquiries = []


for inquiry in inquiries:

    inquiry_id = inquiry.get(
        "inquiry_id",
        ""
    )

    answered = (
        inquiry_id
        in answers
    )


    # -----------------------------------------------------
    # 상태 필터
    # -----------------------------------------------------

    if (
        filter_option
        == "답변 대기"
        and answered
    ):
        continue


    if (
        filter_option
        == "답변 완료"
        and not answered
    ):
        continue


    # -----------------------------------------------------
    # 검색어
    # -----------------------------------------------------

    if search_keyword.strip():

        keyword = (
            search_keyword
            .strip()
            .lower()
        )

        question = (
            inquiry.get(
                "question",
                ""
            )
            .lower()
        )

        if keyword not in question:
            continue


    filtered_inquiries.append(
        inquiry
    )


# =========================================================
# 문의 없음
# =========================================================

if not filtered_inquiries:

    st.info(
        "조건에 맞는 문의가 없습니다."
    )


# =========================================================
# 게시판
# =========================================================

else:

    # -----------------------------------------------------
    # 헤더
    # -----------------------------------------------------

    header1, header2, header3, header4 = (
        st.columns(
            [1.5, 6, 1.5, 1]
        )
    )

    with header1:
        st.markdown(
            "**문의일**"
        )

    with header2:
        st.markdown(
            "**문의 내용**"
        )

    with header3:
        st.markdown(
            "**상태**"
        )

    with header4:
        st.markdown(
            "**상세**"
        )


    st.divider()


    # =====================================================
    # 목록
    # =====================================================

    for inquiry in filtered_inquiries:

        inquiry_id = inquiry.get(
            "inquiry_id",
            ""
        )

        answer = answers.get(
            inquiry_id
        )

        created_at = (
            inquiry.get(
                "created_at",
                ""
            )
            .replace(
                "T",
                " "
            )
        )


        # MM-DD HH:MM
        if len(created_at) >= 16:

            display_date = (
                created_at[
                    5:16
                ]
            )

        else:

            display_date = (
                created_at
            )


        question = inquiry.get(
            "question",
            ""
        )


        # 너무 긴 문의는 목록에서 자르기
        if len(question) > 65:

            question_preview = (
                question[:65]
                + "..."
            )

        else:

            question_preview = (
                question
            )


        # -------------------------------------------------
        # 한 행
        # -------------------------------------------------

        with st.container(
            border=True
        ):

            col1, col2, col3, col4 = (
                st.columns(
                    [1.5, 6, 1.5, 1]
                )
            )


            with col1:

                st.write(
                    display_date
                )


            with col2:

                st.write(
                    question_preview
                )


            with col3:

                if answer:

                    if not inquiry.get(
                        "worker_answer_checked_at"
                    ):

                        st.markdown(
                            "🔵 **새 답변**"
                        )

                    else:

                        st.markdown(
                            "🟢 **완료**"
                        )

                else:

                    st.markdown(
                        "🟠 **대기**"
                    )


            with col4:

                if st.button(
                    "보기",
                    key=(
                        f"open_worker_inquiry_"
                        f"{inquiry_id}"
                    ),
                    width="stretch"
                ):

                    if answer:

                        mark_worker_answer_checked(
                            inquiry_id
                        )

                        mark_notifications_read_for_inquiry(
                            recipient_type="worker",
                            recipient_id=worker_id,
                            inquiry_id=inquiry_id
                        )

                    st.session_state[
                        "selected_worker_inquiry_id"
                    ] = inquiry_id

                    st.rerun()


# =========================================================
# 선택된 문의 팝업 열기
# =========================================================

selected_inquiry_id = (
    st.session_state.get(
        "selected_worker_inquiry_id"
    )
)


if selected_inquiry_id:

    selected_inquiry = next(
        (
            inquiry
            for inquiry in inquiries
            if inquiry.get(
                "inquiry_id"
            )
            == selected_inquiry_id
        ),
        None
    )


    if selected_inquiry:

        selected_answer = answers.get(
            selected_inquiry_id
        )

        show_inquiry_dialog(
            selected_inquiry,
            selected_answer
        )


    else:

        st.session_state[
            "selected_worker_inquiry_id"
        ] = None