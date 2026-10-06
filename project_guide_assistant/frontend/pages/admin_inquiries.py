import io
import sys
from pathlib import Path

import streamlit as st
from streamlit_paste_button import paste_image_button


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
    get_all_inquiries
)

from backend.notification_service import (
    mark_notifications_read_for_inquiry
)

from backend.answer_service import (
    get_latest_answers,
    create_answer
)


# =========================================================
# 접근 권한
# =========================================================

if (
    not st.session_state.get("logged_in")
    or st.session_state.get("role") != "admin"
):
    st.error(
        "관리자만 접근할 수 있습니다."
    )
    st.stop()


# =========================================================
# 클립보드 이미지 객체
# =========================================================

class ClipboardImage:

    def __init__(
        self,
        name: str,
        data: bytes
    ):
        self.name = name
        self._data = data

    def getvalue(self):
        return self._data


# =========================================================
# 문의 상세 팝업
# =========================================================

@st.dialog(
    "📨 문의 상세",
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

    # -----------------------------------------------------
    # 작업자 정보
    # -----------------------------------------------------

    worker_name = inquiry.get(
        "worker_name",
        ""
    )

    worker_id = inquiry.get(
        "worker_id",
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

    col1, col2 = st.columns(
        [3, 1]
    )

    with col1:

        st.markdown(
            f"### 👤 {worker_name}"
        )

        st.caption(
            f"작업자 ID: {worker_id}"
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
    # 질문
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
    # 작업자가 첨부한 이미지
    # =====================================================

    worker_images = inquiry.get(
        "worker_images",
        []
    )

    if worker_images:

        st.markdown(
            "### 🖼️ 작업 화면"
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
    # 작업자가 확인했던 FAQ
    # =====================================================

    faq_results = inquiry.get(
        "faq_results",
        []
    )

    if faq_results:

        with st.expander(
            "💡 작업자가 확인했던 FAQ"
        ):

            for number, faq in enumerate(
                faq_results,
                start=1
            ):

                st.markdown(
                    f"**{number}. "
                    f"{faq.get('question', '')}**"
                )

                st.write(
                    faq.get(
                        "answer",
                        ""
                    )
                )

                faq_images = faq.get(
                    "images",
                    []
                )

                if faq_images:

                    image_columns = st.columns(
                        min(
                            len(faq_images),
                            2
                        )
                    )

                    for image_index, image_path in enumerate(
                        faq_images
                    ):

                        path = Path(
                            image_path
                        )

                        if not path.exists():
                            continue

                        with image_columns[
                            image_index
                            % len(image_columns)
                        ]:
                            st.image(
                                str(path),
                                width="stretch"
                            )

                guide_version = (
                    faq.get(
                        "guide_version"
                    )
                )

                if guide_version:

                    st.caption(
                        f"등록 기준 가이드: "
                        f"{guide_version}"
                    )

                if (
                    number
                    < len(faq_results)
                ):

                    st.divider()

    # =====================================================
    # 작업자가 봤던 검색 결과
    # =====================================================

    search_results = inquiry.get(
        "search_results",
        []
    )

    if search_results:

        with st.expander(
            "🔎 작업자가 확인했던 가이드 검색 결과"
        ):

            for number, result in enumerate(
                search_results,
                start=1
            ):

                source = result.get(
                    "source",
                    ""
                )

                page = result.get(
                    "page"
                )

                st.markdown(
                    f"**{number}. {source}**"
                )

                if page is not None:

                    st.caption(
                        f"{page}페이지"
                    )

                st.write(
                    result.get(
                        "text",
                        ""
                    )
                )

                if (
                    number
                    < len(search_results)
                ):

                    st.divider()

    # =====================================================
    # 이미 답변 완료된 문의
    # =====================================================

    if answer:

        st.divider()

        st.markdown(
            "### ✅ 관리자 답변"
        )

        category = answer.get(
            "category"
        )

        if category:

            st.caption(
                f"분류: {category}"
            )

        st.write(
            answer.get(
                "pm_answer",
                ""
            )
        )

        # -------------------------------------------------
        # 답변 이미지
        # -------------------------------------------------

        pm_images = answer.get(
            "pm_images",
            []
        )

        if pm_images:

            st.markdown(
                "#### 첨부 이미지"
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
                "selected_admin_inquiry_id"
            ] = None

            st.rerun()

        return

    # =====================================================
    # 답변 작성
    # =====================================================

    st.divider()

    st.markdown(
        "### ✏️ 답변 작성"
    )

    category = st.selectbox(
        "문의 분류",
        [
            "일반 기준",
            "객체 생성",
            "가림/절단",
            "큐보이드 방향",
            "포인트 부족",
            "예외 상황",
            "기타"
        ],
        key=(
            f"category_"
            f"{inquiry_id}"
        )
    )

    pm_answer = st.text_area(
        "답변 내용",
        height=160,
        placeholder=(
            "작업자가 바로 판단할 수 있도록 "
            "기준을 명확하게 작성해 주세요."
        ),
        key=(
            f"answer_"
            f"{inquiry_id}"
        )
    )

    # =====================================================
    # 답변 이미지
    # =====================================================

    st.markdown(
        "### 🖼️ 답변 이미지"
    )

    st.caption(
        "파일을 첨부하거나 캡처한 이미지를 "
        "클립보드에서 바로 붙여넣을 수 있습니다."
    )

    # -----------------------------------------------------
    # 파일 첨부
    # -----------------------------------------------------

    pm_images = st.file_uploader(
        "이미지 파일 첨부",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        accept_multiple_files=True,
        key=(
            f"answer_images_"
            f"{inquiry_id}"
        )
    )

    # -----------------------------------------------------
    # 클립보드 이미지 저장 key
    # -----------------------------------------------------

    clipboard_state_key = (
        f"pm_answer_pasted_images_"
        f"{inquiry_id}"
    )

    if (
        clipboard_state_key
        not in st.session_state
    ):

        st.session_state[
            clipboard_state_key
        ] = []

    # -----------------------------------------------------
    # 클립보드 붙여넣기
    # -----------------------------------------------------

    paste_result = paste_image_button(
        label="📋 클립보드 이미지 붙여넣기",
        key=(
            f"pm_answer_paste_"
            f"{inquiry_id}"
        )
    )

    if paste_result.image_data is not None:

        buffer = io.BytesIO()

        paste_result.image_data.save(
            buffer,
            format="PNG"
        )

        image_bytes = buffer.getvalue()

        already_exists = any(
            image["bytes"]
            == image_bytes

            for image
            in st.session_state[
                clipboard_state_key
            ]
        )

        if not already_exists:

            image_number = (
                len(
                    st.session_state[
                        clipboard_state_key
                    ]
                )
                + 1
            )

            st.session_state[
                clipboard_state_key
            ].append({
                "name":
                    f"pm_clipboard_"
                    f"{image_number}.png",

                "bytes":
                    image_bytes
            })

    # -----------------------------------------------------
    # 파일 이미지 미리보기
    # -----------------------------------------------------

    if pm_images:

        st.markdown(
            "#### 첨부한 이미지"
        )

        for image in pm_images:

            st.image(
                image,
                caption=image.name,
                width="stretch"
            )

    # -----------------------------------------------------
    # 붙여넣은 이미지 미리보기
    # -----------------------------------------------------

    pasted_pm_images = (
        st.session_state.get(
            clipboard_state_key,
            []
        )
    )

    if pasted_pm_images:

        st.markdown(
            "#### 붙여넣은 이미지"
        )

        for index, image in enumerate(
            pasted_pm_images
        ):

            with st.container(
                border=True
            ):

                st.image(
                    image["bytes"],
                    caption=image["name"],
                    width="stretch"
                )

                if st.button(
                    "🗑️ 이미지 삭제",
                    key=(
                        f"delete_pm_image_"
                        f"{inquiry_id}_"
                        f"{index}"
                    ),
                    width="stretch"
                ):

                    st.session_state[
                        clipboard_state_key
                    ].pop(index)

                    # 선택된 문의 ID가 남아 있기 때문에
                    # rerun 후 팝업이 다시 열린다.
                    st.rerun()

    # =====================================================
    # 답변 등록 / 취소
    # =====================================================

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "취소",
            width="stretch",
            key=(
                f"cancel_answer_"
                f"{inquiry_id}"
            )
        ):

            st.session_state[
                "selected_admin_inquiry_id"
            ] = None

            st.session_state[
                clipboard_state_key
            ] = []

            st.rerun()

    with col2:

        if st.button(
            "✅ 답변 등록",
            type="primary",
            width="stretch",
            key=(
                f"submit_answer_"
                f"{inquiry_id}"
            )
        ):

            if not pm_answer.strip():

                st.warning(
                    "답변 내용을 입력해 주세요."
                )

                return

            try:

                final_pm_images = []

                # -----------------------------------------
                # 일반 첨부 이미지
                # -----------------------------------------

                if pm_images:

                    final_pm_images.extend(
                        pm_images
                    )

                # -----------------------------------------
                # 클립보드 이미지
                # -----------------------------------------

                for pasted in (
                    st.session_state.get(
                        clipboard_state_key,
                        []
                    )
                ):

                    final_pm_images.append(
                        ClipboardImage(
                            name=pasted[
                                "name"
                            ],
                            data=pasted[
                                "bytes"
                            ]
                        )
                    )

                # -----------------------------------------
                # 답변 저장
                # -----------------------------------------

                create_answer(
                    inquiry_id=inquiry_id,
                    pm_answer=pm_answer,
                    category=category,
                    uploaded_images=(
                        final_pm_images
                    )
                )

                # -----------------------------------------
                # 상태 초기화
                # -----------------------------------------

                st.session_state[
                    clipboard_state_key
                ] = []

                st.session_state[
                    "selected_admin_inquiry_id"
                ] = None

                st.session_state[
                    "admin_answer_success"
                ] = inquiry_id

                st.rerun()

            except ValueError as error:

                st.warning(
                    str(error)
                )

            except Exception as error:

                st.error(
                    "답변 등록 중 문제가 발생했습니다."
                )

                st.exception(
                    error
                )


# =========================================================
# 페이지
# =========================================================

st.title(
    "📨 문의 관리"
)

st.caption(
    "작업자가 등록한 문의를 확인하고 "
    "답변할 수 있습니다."
)


# =========================================================
# 답변 등록 성공 메시지
# =========================================================

if (
    "admin_answer_success"
    in st.session_state
):

    st.session_state.pop(
        "admin_answer_success"
    )

    st.success(
        "✅ 답변이 등록되었습니다."
    )


# =========================================================
# 데이터 불러오기
# =========================================================

inquiries = get_all_inquiries()

answers = get_latest_answers()


# =========================================================
# 상태별 숫자
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
# 필터
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
    placeholder=(
        "작업자 이름, ID 또는 질문 내용 검색"
    )
)


st.divider()


# =========================================================
# 문의 정렬
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

    # 상태 필터
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

    # 검색어
    if search_keyword.strip():

        keyword = (
            search_keyword
            .strip()
            .lower()
        )

        searchable_text = (
            f"{inquiry.get('worker_name', '')} "
            f"{inquiry.get('worker_id', '')} "
            f"{inquiry.get('question', '')}"
        ).lower()

        if (
            keyword
            not in searchable_text
        ):
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
# 게시판 헤더
# =========================================================

else:

    header1, header2, header3, header4, header5 = (
        st.columns(
            [1.3, 1.5, 5, 1.3, 1]
        )
    )

    with header1:
        st.markdown(
            "**문의일**"
        )

    with header2:
        st.markdown(
            "**작업자**"
        )

    with header3:
        st.markdown(
            "**문의 내용**"
        )

    with header4:
        st.markdown(
            "**상태**"
        )

    with header5:
        st.markdown(
            "**상세**"
        )

    st.divider()


    # =====================================================
    # 게시판 목록
    # =====================================================

    for inquiry in filtered_inquiries:

        inquiry_id = inquiry.get(
            "inquiry_id",
            ""
        )

        answer = answers.get(
            inquiry_id
        )

        created_at = inquiry.get(
            "created_at",
            ""
        )

        # 날짜 + 시간 정도만 표시
        display_date = (
            created_at
            .replace(
                "T",
                " "
            )
        )

        if len(display_date) >= 16:

            display_date = (
                display_date[
                    5:16
                ]
            )

        worker_display = (
            inquiry.get(
                "worker_name",
                ""
            )
        )

        question = inquiry.get(
            "question",
            ""
        )

        # 게시판에서 질문이 너무 길게
        # 늘어나는 것 방지
        if len(question) > 55:

            question_preview = (
                question[:55]
                + "..."
            )

        else:

            question_preview = (
                question
            )


        with st.container(
            border=True
        ):

            col1, col2, col3, col4, col5 = (
                st.columns(
                    [1.3, 1.5, 5, 1.3, 1]
                )
            )

            with col1:

                st.write(
                    display_date
                )

            with col2:

                st.write(
                    worker_display
                )

                st.caption(
                    inquiry.get(
                        "worker_id",
                        ""
                    )
                )

            with col3:

                st.write(
                    question_preview
                )

            with col4:

                if answer:

                    st.markdown(
                        "🟢 **완료**"
                    )

                else:

                    st.markdown(
                        "🟠 **대기**"
                    )

            with col5:

                if st.button(
                    "보기",
                    key=(
                        f"open_inquiry_"
                        f"{inquiry_id}"
                    ),
                    width="stretch"
                ):

                    mark_notifications_read_for_inquiry(
                        recipient_type="admin",
                        recipient_id="admin",
                        inquiry_id=inquiry_id
                    )

                    st.session_state[
                        "selected_admin_inquiry_id"
                    ] = inquiry_id

                    st.rerun()


# =========================================================
# 선택된 문의 팝업 열기
# =========================================================

selected_inquiry_id = (
    st.session_state.get(
        "selected_admin_inquiry_id"
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
            "selected_admin_inquiry_id"
        ] = None