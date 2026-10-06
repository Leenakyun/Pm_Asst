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

from backend.faq_service import (
    get_all_faqs,
    set_faq_active,
    delete_faq
)


# =========================================================
# 권한 확인
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
# 페이지
# =========================================================

st.title(
    "💡 FAQ 관리"
)

st.caption(
    "등록된 FAQ를 확인하고 "
    "사용 여부를 관리할 수 있습니다."
)


# =========================================================
# FAQ 불러오기
# =========================================================

faqs = get_all_faqs()


# =========================================================
# 통계
# =========================================================

total_count = len(
    faqs
)

active_count = sum(
    1
    for faq in faqs
    if faq.get(
        "is_active",
        True
    )
)

inactive_count = (
    total_count
    - active_count
)


col1, col2, col3 = st.columns(
    3
)


with col1:

    st.metric(
        "전체 FAQ",
        total_count
    )


with col2:

    st.metric(
        "사용 중",
        active_count
    )


with col3:

    st.metric(
        "사용 안 함",
        inactive_count
    )


# =========================================================
# 필터
# =========================================================

filter_option = st.radio(
    "상태",
    [
        "전체",
        "사용 중",
        "사용 안 함"
    ],
    horizontal=True
)


search_keyword = st.text_input(
    "FAQ 검색",
    placeholder=(
        "질문 또는 답변 내용 검색"
    )
)


st.divider()


# =========================================================
# 필터링
# =========================================================

filtered_faqs = []


for faq in faqs:

    is_active = faq.get(
        "is_active",
        True
    )


    if (
        filter_option == "사용 중"
        and not is_active
    ):
        continue


    if (
        filter_option == "사용 안 함"
        and is_active
    ):
        continue


    if search_keyword.strip():

        keyword = (
            search_keyword
            .strip()
            .lower()
        )

        searchable_text = (
            f"{faq.get('question', '')} "
            f"{faq.get('answer', '')}"
        ).lower()


        if keyword not in searchable_text:
            continue


    filtered_faqs.append(
        faq
    )


# =========================================================
# FAQ 없음
# =========================================================

if not filtered_faqs:

    st.info(
        "조건에 맞는 FAQ가 없습니다."
    )

    st.stop()


# =========================================================
# FAQ 목록
# =========================================================

for faq in filtered_faqs:

    faq_id = faq.get(
        "faq_id",
        ""
    )

    is_active = faq.get(
        "is_active",
        True
    )


    with st.container(
        border=True
    ):

        # -------------------------------------------------
        # 제목 / 상태
        # -------------------------------------------------

        col1, col2 = st.columns(
            [5, 1]
        )


        with col1:

            st.markdown(
                f"### {faq.get('question', '')}"
            )


        with col2:

            if is_active:

                st.success(
                    "사용 중"
                )

            else:

                st.warning(
                    "사용 안 함"
                )


        # -------------------------------------------------
        # 답변
        # -------------------------------------------------

        st.write(
            faq.get(
                "answer",
                ""
            )
        )


        # -------------------------------------------------
        # 이미지
        # -------------------------------------------------

        faq_images = faq.get(
            "images",
            []
        )


        if faq_images:

            st.markdown(
                "#### 🖼️ 첨부 이미지"
            )

            image_columns = st.columns(
                min(
                    len(faq_images),
                    3
                )
            )


            for index, image_path in enumerate(
                faq_images
            ):

                path = Path(
                    image_path
                )

                if not path.exists():
                    continue


                with image_columns[
                    index
                    % len(image_columns)
                ]:

                    st.image(
                        str(path),
                        width="stretch"
                    )


        # -------------------------------------------------
        # 정보
        # -------------------------------------------------

        guide_version = faq.get(
            "guide_version"
        )

        created_at = (
            faq.get(
                "created_at",
                ""
            )
            .replace(
                "T",
                " "
            )
        )


        if guide_version:

            st.caption(
                f"등록 기준 가이드: "
                f"{guide_version}"
            )


        if created_at:

            st.caption(
                f"등록일: "
                f"{created_at}"
            )


        # -------------------------------------------------
        # 관리 버튼
        # -------------------------------------------------

        st.divider()


        col1, col2 = st.columns(
            2
        )


        with col1:

            if is_active:

                if st.button(
                    "⏸️ 사용 중지",
                    key=(
                        f"disable_faq_"
                        f"{faq_id}"
                    ),
                    width="stretch"
                ):

                    try:

                        set_faq_active(
                            faq_id,
                            False
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            "FAQ 상태 변경 중 "
                            "문제가 발생했습니다."
                        )

                        st.exception(
                            error
                        )


            else:

                if st.button(
                    "▶️ 다시 사용",
                    key=(
                        f"enable_faq_"
                        f"{faq_id}"
                    ),
                    width="stretch"
                ):

                    try:

                        set_faq_active(
                            faq_id,
                            True
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            "FAQ 상태 변경 중 "
                            "문제가 발생했습니다."
                        )

                        st.exception(
                            error
                        )


        with col2:

            if st.button(
                "🗑️ 삭제",
                key=(
                    f"delete_faq_"
                    f"{faq_id}"
                ),
                width="stretch"
            ):

                st.session_state[
                    "delete_faq_id"
                ] = faq_id

                st.rerun()


# =========================================================
# 삭제 확인
# =========================================================

delete_faq_id = (
    st.session_state.get(
        "delete_faq_id"
    )
)


if delete_faq_id:

    target = next(
        (
            faq
            for faq in faqs
            if faq.get(
                "faq_id"
            ) == delete_faq_id
        ),
        None
    )


    if target:

        @st.dialog(
            "⚠️ FAQ 삭제 확인"
        )
        def confirm_delete():

            st.write(
                "다음 FAQ를 삭제하시겠습니까?"
            )

            st.markdown(
                f"**{target.get('question', '')}**"
            )

            st.warning(
                "삭제한 FAQ는 복구할 수 없습니다."
            )


            col1, col2 = st.columns(
                2
            )


            with col1:

                if st.button(
                    "취소",
                    width="stretch",
                    key="cancel_faq_delete"
                ):

                    st.session_state[
                        "delete_faq_id"
                    ] = None

                    st.rerun()


            with col2:

                if st.button(
                    "삭제",
                    type="primary",
                    width="stretch",
                    key="confirm_faq_delete"
                ):

                    try:

                        delete_faq(
                            delete_faq_id
                        )

                        st.session_state[
                            "delete_faq_id"
                        ] = None

                        st.rerun()

                    except Exception as error:

                        st.error(
                            "FAQ 삭제 중 "
                            "문제가 발생했습니다."
                        )

                        st.exception(
                            error
                        )


        confirm_delete()