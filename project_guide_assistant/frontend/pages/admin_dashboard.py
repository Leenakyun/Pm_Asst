import io
import sys

from collections import Counter, defaultdict
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

from backend.search_log_service import (
    get_all_search_logs
)

from backend.inquiry_service import (
    get_all_inquiries
)

from backend.answer_service import (
    get_latest_answers
)

from backend.embedding_service import (
    cluster_similar_questions
)

from backend.analytics_service import (
    build_improvement_candidates
)

from backend.faq_service import (
    create_faq
)


# =========================================================
# 접근 권한
# =========================================================

if (
    not st.session_state.get(
        "logged_in"
    )
    or
    st.session_state.get(
        "role"
    ) != "admin"
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
# FAQ 등록 팝업
# =========================================================

@st.dialog(
    "💡 FAQ 등록",
    width="large"
)
def show_faq_create_dialog(
    candidate: dict
):

    representative_question = (
        candidate.get(
            "representative_question",
            ""
        )
    )


    st.caption(
        "반복 검색 데이터를 기반으로 발견된 "
        "질문을 FAQ로 등록합니다."
    )


    # -----------------------------------------------------
    # FAQ 질문
    # -----------------------------------------------------

    faq_question = st.text_area(
        "FAQ 질문",
        value=representative_question,
        height=100,
        key="new_faq_question"
    )


    # -----------------------------------------------------
    # FAQ 답변
    # -----------------------------------------------------

    faq_answer = st.text_area(
        "FAQ 답변",
        height=180,
        placeholder=(
            "작업자가 이 FAQ만 읽고도 "
            "판단할 수 있도록 기준을 작성해 주세요."
        ),
        key="new_faq_answer"
    )


    # -----------------------------------------------------
    # FAQ 이미지
    # -----------------------------------------------------

    st.markdown(
        "#### 🖼️ FAQ 이미지"
    )

    st.caption(
        "설명이 필요한 작업 화면을 파일로 첨부하거나 "
        "클립보드에서 바로 붙여넣을 수 있습니다."
    )

    faq_uploaded_images = st.file_uploader(
        "FAQ 이미지 첨부",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        accept_multiple_files=True,
        key="new_faq_image_upload"
    )

    if (
        "new_faq_pasted_images"
        not in st.session_state
    ):
        st.session_state[
            "new_faq_pasted_images"
        ] = []

    paste_result = paste_image_button(
        label="📋 클립보드 이미지 붙여넣기",
        key="new_faq_paste_image"
    )

    if paste_result.image_data is not None:

        buffer = io.BytesIO()

        paste_result.image_data.save(
            buffer,
            format="PNG"
        )

        image_bytes = buffer.getvalue()

        already_exists = any(
            item["bytes"] == image_bytes
            for item in st.session_state[
                "new_faq_pasted_images"
            ]
        )

        if not already_exists:

            image_number = (
                len(
                    st.session_state[
                        "new_faq_pasted_images"
                    ]
                )
                + 1
            )

            st.session_state[
                "new_faq_pasted_images"
            ].append({
                "name": (
                    f"faq_clipboard_"
                    f"{image_number}.png"
                ),
                "bytes": image_bytes
            })

    if faq_uploaded_images:

        st.markdown(
            "##### 첨부한 이미지"
        )

        for image in faq_uploaded_images:
            st.image(
                image,
                caption=image.name,
                width="stretch"
            )

    pasted_faq_images = (
        st.session_state.get(
            "new_faq_pasted_images",
            []
        )
    )

    if pasted_faq_images:

        st.markdown(
            "##### 붙여넣은 이미지"
        )

        for index, image in enumerate(
            pasted_faq_images
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
                    "🗑️ 이 이미지 삭제",
                    key=(
                        "delete_new_faq_image_"
                        + str(index)
                    ),
                    width="stretch"
                ):
                    st.session_state[
                        "new_faq_pasted_images"
                    ].pop(index)
                    st.rerun()


    # -----------------------------------------------------
    # 주요 가이드 버전
    # -----------------------------------------------------

    versions = [
        item.get(
            "guide_version"
        )

        for item in candidate.get(
            "questions",
            []
        )

        if item.get(
            "guide_version"
        )
    ]


    if versions:

        guide_version = (
            Counter(
                versions
            )
            .most_common(1)[0][0]
        )

        st.caption(
            f"주요 발생 가이드 버전: "
            f"{guide_version}"
        )

    else:

        guide_version = None


    # -----------------------------------------------------
    # 후보 통계
    # -----------------------------------------------------

    st.markdown(
        "#### 후보 데이터"
    )

    col1, col2, col3 = st.columns(
        3
    )


    with col1:

        st.metric(
            "검색",
            candidate.get(
                "search_count",
                0
            )
        )


    with col2:

        st.metric(
            "PM 문의",
            candidate.get(
                "inquiry_count",
                0
            )
        )


    with col3:

        st.metric(
            "문의 전환율",
            (
                f"{candidate.get('inquiry_rate', 0):.1f}%"
            )
        )


    st.divider()


    # -----------------------------------------------------
    # 버튼
    # -----------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "취소",
            width="stretch",
            key="cancel_faq_create"
        ):

            st.session_state[
                "new_faq_pasted_images"
            ] = []

            st.rerun()


    with col2:

        if st.button(
            "✅ FAQ 등록",
            type="primary",
            width="stretch",
            key="submit_faq_create"
        ):

            try:

                final_faq_images = []

                if faq_uploaded_images:
                    final_faq_images.extend(
                        faq_uploaded_images
                    )

                for pasted in (
                    st.session_state.get(
                        "new_faq_pasted_images",
                        []
                    )
                ):
                    final_faq_images.append(
                        ClipboardImage(
                            name=pasted["name"],
                            data=pasted["bytes"]
                        )
                    )

                faq = create_faq(
                    question=faq_question,
                    answer=faq_answer,
                    guide_version=guide_version,
                    source_type=(
                        "analytics_candidate"
                    ),
                    source_question=(
                        representative_question
                    ),
                    uploaded_images=(
                        final_faq_images
                    )
                )

                st.session_state[
                    "new_faq_pasted_images"
                ] = []


                st.session_state[
                    "faq_create_success"
                ] = faq[
                    "faq_id"
                ]


                st.rerun()


            except ValueError as error:

                st.warning(
                    str(error)
                )


            except Exception as error:

                st.error(
                    "FAQ 등록 중 문제가 발생했습니다."
                )

                st.exception(
                    error
                )


# =========================================================
# 페이지
# =========================================================

st.title(
    "📊 운영 대시보드"
)

st.caption(
    "작업자의 가이드 검색 및 "
    "관리자 문의 현황을 확인합니다."
)


# =========================================================
# FAQ 등록 성공
# =========================================================

if (
    "faq_create_success"
    in st.session_state
):

    st.session_state.pop(
        "faq_create_success"
    )

    st.success(
        "✅ FAQ가 등록되었습니다."
    )


# =========================================================
# 데이터
# =========================================================

search_logs = (
    get_all_search_logs()
)

inquiries = (
    get_all_inquiries()
)

answers = (
    get_latest_answers()
)


# =========================================================
# 기본 통계
# =========================================================

total_searches = len(
    search_logs
)

total_inquiries = len(
    inquiries
)


answered_inquiries = sum(
    1

    for inquiry in inquiries

    if inquiry.get(
        "inquiry_id"
    ) in answers
)


waiting_inquiries = (
    total_inquiries
    - answered_inquiries
)


# =========================================================
# 검색 ↔ 문의 연결
# =========================================================

linked_search_ids = {
    inquiry.get(
        "search_id"
    )

    for inquiry in inquiries

    if inquiry.get(
        "search_id"
    )
}


linked_inquiry_count = len(
    linked_search_ids
)


estimated_resolved = max(
    total_searches
    - linked_inquiry_count,
    0
)


if total_searches > 0:

    inquiry_conversion_rate = (
        linked_inquiry_count
        / total_searches
        * 100
    )

    estimated_resolution_rate = (
        estimated_resolved
        / total_searches
        * 100
    )


else:

    inquiry_conversion_rate = 0.0

    estimated_resolution_rate = 0.0


# =========================================================
# 핵심 지표
# =========================================================

st.subheader(
    "📌 핵심 지표"
)


col1, col2, col3, col4 = (
    st.columns(4)
)


with col1:

    st.metric(
        "전체 검색",
        total_searches
    )


with col2:

    st.metric(
        "PM 문의",
        linked_inquiry_count
    )


with col3:

    st.metric(
        "검색 해결 추정",
        estimated_resolved,
        help=(
            "전체 검색 중 PM 문의로 "
            "이어지지 않은 검색 수입니다."
        )
    )


with col4:

    st.metric(
        "PM 문의 전환율",
        f"{inquiry_conversion_rate:.1f}%"
    )


st.caption(
    f"검색 해결 추정률: "
    f"{estimated_resolution_rate:.1f}%"
)


st.divider()


# =========================================================
# 문의 현황
# =========================================================

st.subheader(
    "📨 문의 현황"
)


col1, col2, col3 = (
    st.columns(3)
)


with col1:

    st.metric(
        "전체 문의",
        total_inquiries
    )


with col2:

    st.metric(
        "답변 대기",
        waiting_inquiries
    )


with col3:

    st.metric(
        "답변 완료",
        answered_inquiries
    )


st.divider()


# =========================================================
# 가이드 버전별 현황
# =========================================================

st.subheader(
    "📘 가이드 버전별 현황"
)


version_stats = defaultdict(
    lambda: {
        "searches": 0,
        "inquiries": 0
    }
)


# 검색 집계
for log in search_logs:

    version = (
        log.get(
            "guide_version"
        )
        or "버전 정보 없음"
    )

    version_stats[
        version
    ][
        "searches"
    ] += 1


# 문의 집계
for inquiry in inquiries:

    version = inquiry.get(
        "guide_version"
    )

    if not version:
        continue

    version_stats[
        version
    ][
        "inquiries"
    ] += 1


if not version_stats:

    st.info(
        "아직 가이드 버전별 데이터가 없습니다."
    )


else:

    for version, stats in sorted(
        version_stats.items()
    ):

        searches = stats[
            "searches"
        ]

        inquiry_count = stats[
            "inquiries"
        ]


        if searches > 0:

            rate = (
                inquiry_count
                / searches
                * 100
            )

        else:

            rate = 0.0


        with st.container(
            border=True
        ):

            st.markdown(
                f"### {version}"
            )


            col1, col2, col3 = (
                st.columns(3)
            )


            with col1:

                st.metric(
                    "검색",
                    searches
                )


            with col2:

                st.metric(
                    "문의",
                    inquiry_count
                )


            with col3:

                st.metric(
                    "문의 전환율",
                    f"{rate:.1f}%"
                )


st.divider()


# =========================================================
# 비슷한 검색 질문 그룹
# =========================================================

st.subheader(
    "🔎 반복 검색 질문 TOP 10"
)

st.caption(
    "표현이 조금 달라도 내용이 비슷한 질문을 "
    "하나의 질문군으로 묶어 집계합니다."
)


question_groups = (
    cluster_similar_questions(
        search_logs,
        similarity_threshold=0.55
    )
)


repeated_groups = [
    group

    for group in question_groups

    if group.get(
        "count",
        0
    ) >= 2
]


top_groups = (
    repeated_groups[:10]
)


if not top_groups:

    st.info(
        "아직 반복해서 검색된 "
        "유사 질문이 없습니다."
    )


else:

    for rank, group in enumerate(
        top_groups,
        start=1
    ):

        with st.container(
            border=True
        ):

            col1, col2 = (
                st.columns(
                    [8, 1]
                )
            )


            with col1:

                st.markdown(
                    f"### {rank}. "
                    f"{group.get('representative_question', '')}"
                )


            with col2:

                st.metric(
                    "검색",
                    f"{group.get('count', 0)}회"
                )


            with st.expander(
                "같은 질문군 보기"
            ):

                for item in group.get(
                    "questions",
                    []
                ):

                    question = item.get(
                        "question",
                        ""
                    )

                    worker_name = item.get(
                        "worker_name",
                        ""
                    )

                    searched_at = (
                        item.get(
                            "searched_at",
                            ""
                        )
                        .replace(
                            "T",
                            " "
                        )
                    )

                    st.write(
                        f"• {question}"
                    )

                    st.caption(
                        f"{worker_name} "
                        f"· {searched_at}"
                    )


st.divider()


# =========================================================
# FAQ / 가이드 개선 후보
# =========================================================

st.subheader(
    "💡 FAQ / 가이드 개선 후보"
)

st.caption(
    "반복 검색과 PM 문의 전환율을 기준으로 "
    "자주 헷갈리는 기준을 자동으로 표시합니다."
)


improvement_candidates = (
    build_improvement_candidates(
        question_groups,
        inquiries
    )
)


if not improvement_candidates:

    st.info(
        "아직 충분한 반복 데이터가 없습니다."
    )


else:

    for rank, candidate in enumerate(
        improvement_candidates[:10],
        start=1
    ):

        with st.container(
            border=True
        ):

            candidate_type = (
                candidate.get(
                    "candidate_type",
                    ""
                )
            )


            # ---------------------------------------------
            # 후보 유형
            # ---------------------------------------------

            if (
                candidate_type
                == "가이드 개선 필요"
            ):

                st.error(
                    "🔴 가이드 개선 필요"
                )


            else:

                st.warning(
                    "🟡 FAQ 후보"
                )


            # ---------------------------------------------
            # 대표 질문
            # ---------------------------------------------

            st.markdown(
                f"### {rank}. "
                f"{candidate.get('representative_question', '')}"
            )


            # ---------------------------------------------
            # 지표
            # ---------------------------------------------

            col1, col2, col3 = (
                st.columns(3)
            )


            with col1:

                st.metric(
                    "검색",
                    candidate.get(
                        "search_count",
                        0
                    )
                )


            with col2:

                st.metric(
                    "PM 문의",
                    candidate.get(
                        "inquiry_count",
                        0
                    )
                )


            with col3:

                st.metric(
                    "문의 전환율",
                    (
                        f"{candidate.get('inquiry_rate', 0):.1f}%"
                    )
                )


            # ---------------------------------------------
            # 판단 설명
            # ---------------------------------------------

            if (
                candidate_type
                == "가이드 개선 필요"
            ):

                st.caption(
                    "반복 검색이 많고 "
                    "PM 문의 전환율도 높습니다. "
                    "기존 가이드 표현이 충분히 "
                    "명확한지 검토할 필요가 있습니다."
                )


            else:

                st.caption(
                    "반복해서 검색되는 질문입니다. "
                    "FAQ로 정리하면 검색 시간을 "
                    "줄일 가능성이 있습니다."
                )


            # ---------------------------------------------
            # 실제 질문 보기
            # ---------------------------------------------

            with st.expander(
                "실제 질문 보기"
            ):

                for item in candidate.get(
                    "questions",
                    []
                ):

                    question = item.get(
                        "question",
                        ""
                    )

                    worker_name = item.get(
                        "worker_name",
                        ""
                    )

                    searched_at = (
                        item.get(
                            "searched_at",
                            ""
                        )
                        .replace(
                            "T",
                            " "
                        )
                    )


                    st.write(
                        f"• {question}"
                    )

                    st.caption(
                        f"{worker_name} "
                        f"· {searched_at}"
                    )


            # =============================================
            # FAQ 등록 버튼
            #
            # expander 바깥
            # candidate container 안
            # =============================================

            if st.button(
                "💡 FAQ로 등록",
                key=(
                    "create_faq_"
                    + str(rank)
                ),
                width="stretch"
            ):

                show_faq_create_dialog(
                    candidate
                )


st.divider()


# =========================================================
# 검색 결과 없음
# =========================================================

st.subheader(
    "⚠️ 검색 결과를 찾지 못한 질문"
)


no_result_logs = [
    log

    for log in search_logs

    if log.get(
        "result_count",
        0
    ) == 0
]


st.metric(
    "검색 결과 없음",
    len(
        no_result_logs
    )
)


if no_result_logs:

    recent_no_results = sorted(
        no_result_logs,

        key=lambda x:
            x.get(
                "searched_at",
                ""
            ),

        reverse=True
    )[:10]


    for log in recent_no_results:

        searched_at = (
            log.get(
                "searched_at",
                ""
            )
            .replace(
                "T",
                " "
            )
        )


        with st.container(
            border=True
        ):

            st.write(
                log.get(
                    "question",
                    ""
                )
            )

            st.caption(
                f"{log.get('worker_name', '')} "
                f"· {searched_at}"
            )


else:

    st.success(
        "현재까지 검색 결과가 없는 "
        "질문은 없습니다."
    )


st.divider()


# =========================================================
# 문의 분류
# =========================================================

st.subheader(
    "🏷️ 문의 분류"
)


category_counter = Counter()


for answer in answers.values():

    category = answer.get(
        "category"
    )

    if category:

        category_counter[
            category
        ] += 1


if not category_counter:

    st.info(
        "아직 분류된 문의가 없습니다."
    )


else:

    for category, count in (
        category_counter
        .most_common()
    ):

        col1, col2 = (
            st.columns(
                [5, 1]
            )
        )


        with col1:

            st.write(
                category
            )


        with col2:

            st.write(
                f"{count}건"
            )