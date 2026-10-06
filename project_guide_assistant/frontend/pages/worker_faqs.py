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
    get_active_faqs
)


# =========================================================
# 권한 확인
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
# 페이지
# =========================================================

st.title(
    "💡 FAQ"
)

st.caption(
    "관리자가 등록한 자주 묻는 질문과 "
    "작업 기준을 확인할 수 있습니다."
)


# =========================================================
# FAQ
# =========================================================

faqs = get_active_faqs()


# =========================================================
# 검색
# =========================================================

search_keyword = st.text_input(
    "FAQ 검색",
    placeholder=(
        "예: 포인트, 가림, 큐보이드 방향"
    )
)


# =========================================================
# 검색 필터
# =========================================================

if search_keyword.strip():

    keyword = (
        search_keyword
        .strip()
        .lower()
    )


    faqs = [
        faq

        for faq in faqs

        if (
            keyword
            in (
                f"{faq.get('question', '')} "
                f"{faq.get('answer', '')}"
            ).lower()
        )
    ]


st.divider()


# =========================================================
# FAQ 없음
# =========================================================

if not faqs:

    st.info(
        "등록된 FAQ가 없습니다."
    )

    st.stop()


# =========================================================
# FAQ 목록
# =========================================================

for faq in faqs:

    question = faq.get(
        "question",
        ""
    )


    with st.expander(
        f"💡 {question}"
    ):

        st.write(
            faq.get(
                "answer",
                ""
            )
        )


        # =================================================
        # 이미지
        # =================================================

        faq_images = faq.get(
            "images",
            []
        )


        if faq_images:

            st.markdown(
                "#### 참고 이미지"
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


        # =================================================
        # 가이드 버전
        # =================================================

        guide_version = faq.get(
            "guide_version"
        )


        if guide_version:

            st.caption(
                f"기준 가이드: "
                f"{guide_version}"
            )