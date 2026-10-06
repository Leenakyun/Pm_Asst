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

from backend.guide_management_service import (
    get_active_guide
)

from backend.guide_service import (
    parse_saved_guide
)

from backend.search_service import (
    build_search_engine,
    search_guide
)

from backend.search_log_service import (
    create_search_log
)

from backend.inquiry_service import (
    create_inquiry
)

from backend.faq_service import (
    search_faqs
)

from backend.settings_service import (
    get_project_settings
)

from backend.vision_service import (
    analyze_work_images,
    build_vision_search_text,
    vision_available
)


# =========================================================
# 권한
# =========================================================

if (
    not st.session_state.get(
        "logged_in"
    )
    or
    st.session_state.get(
        "role"
    ) != "worker"
):

    st.error(
        "작업자만 접근할 수 있습니다."
    )

    st.stop()


# =========================================================
# 작업자
# =========================================================

worker_id = (
    st.session_state.get(
        "worker_id",
        ""
    )
)

worker_name = (
    st.session_state.get(
        "worker_name",
        ""
    )
)


if not worker_id:

    st.error(
        "작업자 로그인 정보가 없습니다."
    )

    st.stop()


# =========================================================
# 프로젝트 설정
# =========================================================

project_settings = (
    get_project_settings()
)

vision_enabled = bool(
    project_settings.get(
        "vision_enabled",
        False
    )
)

vision_detail = (
    project_settings.get(
        "vision_detail",
        "low"
    )
)


# =========================================================
# Vision OFF라면 검색용 이미지 상태 제거
# =========================================================

if not vision_enabled:

    st.session_state[
        "guide_search_pasted_images"
    ] = []

    st.session_state[
        "worker_last_search_images"
    ] = []


# =========================================================
# bytes 이미지 wrapper
# =========================================================

class ClipboardImage:

    def __init__(
        self,
        name: str,
        data: bytes
    ):

        self.name = name
        self._data = data


    def getvalue(
        self
    ):

        return self._data


# =========================================================
# PM 문의 팝업
# =========================================================

@st.dialog(
    "📨 관리자에게 문의",
    width="large"
)
def show_pm_inquiry_dialog():

    st.caption(
        "검색 결과만으로 판단하기 어려운 경우 "
        "관리자에게 직접 문의할 수 있습니다."
    )


    default_question = (
        st.session_state.get(
            "worker_last_question",
            ""
        )
    )


    inquiry_question = st.text_area(
        "문의 내용",
        value=default_question,
        height=140,
        placeholder=(
            "관리자가 상황을 이해할 수 있도록 "
            "구체적으로 작성해 주세요."
        ),
        key="pm_inquiry_question"
    )


    st.divider()


    # =====================================================
    # 이미지
    # =====================================================

    st.markdown(
        "### 🖼️ 작업 화면"
    )

    st.caption(
        "파일을 첨부하거나 "
        "캡처 이미지를 클립보드에서 "
        "바로 붙여넣을 수 있습니다."
    )


    # =====================================================
    # 검색 때 사용한 이미지
    # =====================================================

    search_images = (
        st.session_state.get(
            "worker_last_search_images",
            []
        )
    )


    if search_images:

        st.markdown(
            "#### 검색 때 첨부한 이미지"
        )

        st.caption(
            "가이드 검색 때 사용했던 이미지도 "
            "문의와 함께 전달됩니다."
        )


        for image in search_images:

            st.image(
                image[
                    "bytes"
                ],
                caption=image[
                    "name"
                ],
                width="stretch"
            )


    # =====================================================
    # 추가 파일
    # =====================================================

    uploaded_images = st.file_uploader(
        "이미지 파일 첨부",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        accept_multiple_files=True,
        key="pm_inquiry_file_upload"
    )


    st.markdown(
        "**또는**"
    )


    # =====================================================
    # 클립보드
    # =====================================================

    paste_result = paste_image_button(
        label="📋 클립보드 이미지 붙여넣기",
        key="pm_inquiry_paste"
    )


    if (
        "pm_pasted_images"
        not in st.session_state
    ):

        st.session_state[
            "pm_pasted_images"
        ] = []


    if (
        paste_result.image_data
        is not None
    ):

        buffer = io.BytesIO()

        paste_result.image_data.save(
            buffer,
            format="PNG"
        )

        image_bytes = (
            buffer.getvalue()
        )


        already_exists = any(
            image[
                "bytes"
            ]
            == image_bytes

            for image
            in st.session_state[
                "pm_pasted_images"
            ]
        )


        if not already_exists:

            image_number = (
                len(
                    st.session_state[
                        "pm_pasted_images"
                    ]
                )
                + 1
            )

            st.session_state[
                "pm_pasted_images"
            ].append({
                "name":
                    f"clipboard_{image_number}.png",

                "bytes":
                    image_bytes,
            })


    # =====================================================
    # 붙여넣은 이미지
    # =====================================================

    pasted_images = (
        st.session_state.get(
            "pm_pasted_images",
            []
        )
    )


    if pasted_images:

        st.markdown(
            "#### 붙여넣은 이미지"
        )


        for index, image in enumerate(
            pasted_images
        ):

            with st.container(
                border=True
            ):

                st.image(
                    image[
                        "bytes"
                    ],
                    caption=image[
                        "name"
                    ],
                    width="stretch"
                )


                if st.button(
                    "🗑️ 이 이미지 삭제",
                    key=(
                        f"delete_pasted_"
                        f"{index}"
                    ),
                    width="stretch"
                ):

                    st.session_state[
                        "pm_pasted_images"
                    ].pop(
                        index
                    )

                    st.rerun()


    # =====================================================
    # 일반 첨부 미리보기
    # =====================================================

    if uploaded_images:

        st.markdown(
            "#### 첨부한 이미지"
        )


        for image in uploaded_images:

            st.image(
                image,
                caption=image.name,
                width="stretch"
            )


    st.divider()


    # =====================================================
    # 검색 정보
    # =====================================================

    if (
        st.session_state.get(
            "worker_last_results",
            []
        )
        or
        st.session_state.get(
            "worker_last_faq_results",
            []
        )
    ):

        st.info(
            "현재 검색했던 FAQ 및 가이드 결과도 "
            "관리자에게 함께 전달됩니다."
        )


    # =====================================================
    # 버튼
    # =====================================================

    col1, col2 = st.columns(
        2
    )


    with col1:

        if st.button(
            "취소",
            width="stretch",
            key="cancel_pm_inquiry"
        ):

            st.session_state[
                "pm_pasted_images"
            ] = []

            st.rerun()


    with col2:

        if st.button(
            "문의 등록",
            type="primary",
            width="stretch",
            key="submit_pm_inquiry"
        ):

            if not inquiry_question.strip():

                st.warning(
                    "문의 내용을 입력해 주세요."
                )

                return


            final_images = []


            # ---------------------------------------------
            # 검색 이미지
            # ---------------------------------------------

            for search_image in (
                st.session_state.get(
                    "worker_last_search_images",
                    []
                )
            ):

                final_images.append(
                    ClipboardImage(
                        name=search_image[
                            "name"
                        ],
                        data=search_image[
                            "bytes"
                        ]
                    )
                )


            # ---------------------------------------------
            # 일반 첨부
            # ---------------------------------------------

            if uploaded_images:

                final_images.extend(
                    uploaded_images
                )


            # ---------------------------------------------
            # 클립보드
            # ---------------------------------------------

            for pasted in (
                st.session_state.get(
                    "pm_pasted_images",
                    []
                )
            ):

                final_images.append(
                    ClipboardImage(
                        name=pasted[
                            "name"
                        ],
                        data=pasted[
                            "bytes"
                        ]
                    )
                )


            # ---------------------------------------------
            # 저장
            # ---------------------------------------------

            try:

                inquiry = (
                    create_inquiry(
                        worker_id=worker_id,

                        worker_name=worker_name,

                        question=(
                            inquiry_question
                            .strip()
                        ),

                        search_results=(
                            st.session_state.get(
                                "worker_last_results",
                                []
                            )
                        ),

                        faq_results=(
                            st.session_state.get(
                                "worker_last_faq_results",
                                []
                            )
                        ),

                        uploaded_images=(
                            final_images
                        ),

                        search_id=(
                            st.session_state.get(
                                "worker_last_search_id"
                            )
                        ),

                        guide_id=(
                            st.session_state.get(
                                "worker_last_guide_id"
                            )
                        ),

                        guide_version=(
                            st.session_state.get(
                                "worker_last_guide_version"
                            )
                        )
                    )
                )


                st.session_state[
                    "pm_pasted_images"
                ] = []


                st.session_state[
                    "pm_inquiry_success"
                ] = inquiry[
                    "inquiry_id"
                ]


                st.rerun()


            except Exception as error:

                st.error(
                    "문의 등록 중 문제가 발생했습니다."
                )

                st.exception(
                    error
                )


# =========================================================
# 페이지
# =========================================================

st.title(
    "🔎 가이드 검색"
)

st.caption(
    "현재 적용 중인 작업 가이드를 기준으로 "
    "관련 내용을 검색합니다."
)


# =========================================================
# 작업자 표시
# =========================================================

with st.container(
    border=True
):

    st.markdown(
        f"**작업자:** "
        f"{worker_name or worker_id}"
    )

    st.caption(
        f"작업자 ID: "
        f"{worker_id}"
    )


# =========================================================
# 현재 가이드
# =========================================================

active_guide = (
    get_active_guide()
)


if not active_guide:

    st.warning(
        "현재 적용 중인 가이드가 없습니다. "
        "관리자에게 문의해 주세요."
    )

    st.stop()


st.subheader(
    "📘 현재 적용 가이드"
)


col1, col2 = st.columns(
    2
)


with col1:

    st.metric(
        "가이드 버전",
        active_guide.get(
            "version",
            ""
        )
    )


with col2:

    uploaded_date = (
        active_guide.get(
            "uploaded_at",
            ""
        )
        .split(
            "T"
        )[0]
    )

    st.metric(
        "등록일",
        uploaded_date
    )


st.caption(
    f"파일명: "
    f"{active_guide.get('file_name', '')}"
)


st.divider()


# =========================================================
# 가이드 파싱
# =========================================================

try:

    chunks = (
        parse_saved_guide(
            file_path=active_guide[
                "file_path"
            ],

            original_file_name=(
                active_guide[
                    "file_name"
                ]
            )
        )
    )


except Exception as error:

    st.error(
        "가이드를 불러오는 중 문제가 발생했습니다."
    )

    st.exception(
        error
    )

    st.stop()


if not chunks:

    st.warning(
        "현재 가이드에서 검색 가능한 "
        "내용을 찾지 못했습니다."
    )

    st.stop()


# =========================================================
# 검색 엔진
# =========================================================

try:

    vectorizer, matrix = (
        build_search_engine(
            chunks
        )
    )


except Exception as error:

    st.error(
        "검색 엔진 준비 중 문제가 발생했습니다."
    )

    st.exception(
        error
    )

    st.stop()


# =========================================================
# 전체 가이드에서 넘어온 질문
# =========================================================

if (
    "worker_prefill_question"
    in st.session_state
):

    st.session_state[
        "worker_guide_question"
    ] = st.session_state.pop(
        "worker_prefill_question"
    )


# =========================================================
# 질문
# =========================================================

question = st.text_area(
    "작업 중 궁금한 내용을 입력해 주세요.",
    placeholder=(
        "예: 포인트가 적은 차량도 "
        "작업해야 하나요?"
    ),
    height=100,
    label_visibility="collapsed",
    key="worker_guide_question"
)


# =========================================================
# 전체 가이드에서 넘어온 기준 표시
# =========================================================

question_source = (
    st.session_state.get(
        "worker_question_source"
    )
)


if question_source:

    section_title = (
        question_source.get(
            "section_title",
            ""
        )
    )

    page = (
        question_source.get(
            "page"
        )
    )


    source_text = (
        f"📖 선택한 가이드 기준: "
        f"{section_title}"
    )


    if page is not None:

        source_text += (
            f" · {page}페이지"
        )


    st.info(
        source_text
    )


    if st.button(
        "선택한 기준 해제",
        key="clear_guide_question_source"
    ):

        st.session_state.pop(
            "worker_question_source",
            None
        )

        st.session_state[
            "worker_guide_question"
        ] = ""

        st.rerun()


# =========================================================
# 검색 이미지
# Vision ON일 때만 표시
# =========================================================

search_uploaded_images = []


if vision_enabled:

    st.markdown(
        "### 🖼️ 이미지로 함께 검색"
    )

    st.caption(
        "작업 화면을 첨부하면 이미지 상황을 분석해 "
        "가이드 검색을 보조합니다."
    )


    search_uploaded_images = (
        st.file_uploader(
            "검색 이미지 파일 첨부",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            accept_multiple_files=True,
            key="guide_search_file_upload"
        )
        or []
    )


    st.markdown(
        "**또는**"
    )


    search_paste_result = (
        paste_image_button(
            label=(
                "📋 클립보드 이미지 붙여넣기"
            ),
            key="guide_search_paste"
        )
    )


    if (
        "guide_search_pasted_images"
        not in st.session_state
    ):

        st.session_state[
            "guide_search_pasted_images"
        ] = []


    if (
        search_paste_result.image_data
        is not None
    ):

        buffer = io.BytesIO()

        search_paste_result.image_data.save(
            buffer,
            format="PNG"
        )

        image_bytes = (
            buffer.getvalue()
        )


        already_exists = any(
            image[
                "bytes"
            ]
            == image_bytes

            for image
            in st.session_state[
                "guide_search_pasted_images"
            ]
        )


        if not already_exists:

            image_number = (
                len(
                    st.session_state[
                        "guide_search_pasted_images"
                    ]
                )
                + 1
            )


            st.session_state[
                "guide_search_pasted_images"
            ].append({
                "name":
                    f"search_clipboard_"
                    f"{image_number}.png",

                "bytes":
                    image_bytes,
            })


    # =====================================================
    # 파일 미리보기
    # =====================================================

    if search_uploaded_images:

        st.markdown(
            "#### 첨부한 이미지"
        )


        for image in (
            search_uploaded_images
        ):

            st.image(
                image,
                caption=image.name,
                width="stretch"
            )


    # =====================================================
    # 클립보드 미리보기
    # =====================================================

    search_pasted_images = (
        st.session_state.get(
            "guide_search_pasted_images",
            []
        )
    )


    if search_pasted_images:

        st.markdown(
            "#### 붙여넣은 이미지"
        )


        for index, image in enumerate(
            search_pasted_images
        ):

            with st.container(
                border=True
            ):

                st.image(
                    image[
                        "bytes"
                    ],
                    caption=image[
                        "name"
                    ],
                    width="stretch"
                )


                if st.button(
                    "🗑️ 이 이미지 삭제",
                    key=(
                        f"delete_search_pasted_"
                        f"{index}"
                    ),
                    width="stretch"
                ):

                    st.session_state[
                        "guide_search_pasted_images"
                    ].pop(
                        index
                    )

                    st.rerun()


# =========================================================
# 검색
# =========================================================

if st.button(
    "🔎 가이드 검색",
    type="primary",
    width="stretch"
):

    if not question.strip():

        st.warning(
            "질문을 입력해 주세요."
        )


    else:

        try:

            # =============================================
            # 기본 검색문
            # =============================================

            search_question = (
                question.strip()
            )

            vision_result = None

            vision_search_text = ""


            # =============================================
            # 검색 이미지 구성
            # =============================================

            search_images = []

            search_image_payloads = []


            if vision_enabled:

                for image in (
                    search_uploaded_images
                ):

                    search_images.append(
                        image
                    )

                    search_image_payloads.append({
                        "name":
                            image.name,

                        "bytes":
                            image.getvalue()
                    })


                for pasted in (
                    st.session_state.get(
                        "guide_search_pasted_images",
                        []
                    )
                ):

                    clipboard_image = (
                        ClipboardImage(
                            name=pasted[
                                "name"
                            ],
                            data=pasted[
                                "bytes"
                            ]
                        )
                    )


                    search_images.append(
                        clipboard_image
                    )


                    search_image_payloads.append({
                        "name":
                            pasted[
                                "name"
                            ],

                        "bytes":
                            pasted[
                                "bytes"
                            ]
                    })


            st.session_state[
                "worker_last_search_images"
            ] = search_image_payloads


            # =============================================
            # Vision
            # =============================================

            if (
                vision_enabled
                and search_images
            ):

                if not vision_available():

                    st.warning(
                        "Vision API를 사용할 수 없어 "
                        "텍스트 질문만으로 검색합니다."
                    )


                else:

                    try:

                        with st.spinner(
                            "작업 이미지를 분석하고 있습니다..."
                        ):

                            vision_result = (
                                analyze_work_images(
                                    search_images,
                                    detail=vision_detail
                                )
                            )


                            vision_search_text = (
                                build_vision_search_text(
                                    vision_result
                                )
                            )


                        if vision_search_text:

                            search_question = (
                                f"{search_question} "
                                f"{vision_search_text}"
                            )


                    except Exception as error:

                        st.warning(
                            "이미지 분석에 실패하여 "
                            "텍스트 질문만으로 검색합니다."
                        )


            # =============================================
            # 가이드 검색
            # =============================================

            results = (
                search_guide(
                    question=search_question,
                    chunks=chunks,
                    vectorizer=vectorizer,
                    matrix=matrix
                )
            )


            # =============================================
            # FAQ 검색
            # =============================================

            faq_results = (
                search_faqs(
                    question=search_question
                )
            )


            # =============================================
            # 검색 로그
            # =============================================

            search_log = (
                create_search_log(
                    worker_id=worker_id,

                    worker_name=worker_name,

                    # 로그에는 원래 질문을 저장
                    question=question,

                    guide_id=(
                        active_guide.get(
                            "guide_id",
                            ""
                        )
                    ),

                    guide_version=(
                        active_guide.get(
                            "version",
                            ""
                        )
                    ),

                    search_results=results,

                    faq_results=faq_results
                )
            )


            # =============================================
            # 상태 저장
            # =============================================

            st.session_state[
                "worker_last_question"
            ] = question.strip()


            st.session_state[
                "worker_last_results"
            ] = results


            st.session_state[
                "worker_last_faq_results"
            ] = faq_results


            st.session_state[
                "worker_last_search_id"
            ] = search_log[
                "search_id"
            ]


            st.session_state[
                "worker_last_guide_id"
            ] = active_guide.get(
                "guide_id",
                ""
            )


            st.session_state[
                "worker_last_guide_version"
            ] = active_guide.get(
                "version",
                ""
            )


            st.session_state[
                "worker_last_vision_result"
            ] = vision_result


            st.session_state[
                "worker_last_vision_search_text"
            ] = vision_search_text


        except Exception as error:

            st.error(
                "가이드 검색 중 문제가 발생했습니다."
            )

            st.exception(
                error
            )


# =========================================================
# 검색 결과
# =========================================================

if (
    "worker_last_results"
    in st.session_state
):

    results = (
        st.session_state.get(
            "worker_last_results",
            []
        )
    )

    faq_results = (
        st.session_state.get(
            "worker_last_faq_results",
            []
        )
    )

    vision_result = (
        st.session_state.get(
            "worker_last_vision_result"
        )
    )


    st.divider()


    # =====================================================
    # Vision 참고 정보
    # =====================================================

    if (
        vision_enabled
        and vision_result
    ):

        topics = (
            vision_result.get(
                "likely_topics",
                []
            )
        )

        keywords = (
            vision_result.get(
                "search_keywords",
                []
            )
        )

        display_tags = []


        for tag in (
            topics
            + keywords
        ):

            if (
                tag
                and tag not in display_tags
            ):

                display_tags.append(
                    tag
                )


        if display_tags:

            st.info(
                "🖼️ 이미지 분석 참고: "
                + " · ".join(
                    display_tags[:8]
                )
            )


    # =====================================================
    # FAQ
    # =====================================================

    if faq_results:

        st.subheader(
            "💡 FAQ"
        )

        st.caption(
            "관리자가 등록한 FAQ 중 "
            "현재 질문과 관련된 항목입니다."
        )


        for faq in faq_results:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### "
                    f"{faq.get('question', '')}"
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

                    image_columns = (
                        st.columns(
                            min(
                                len(
                                    faq_images
                                ),
                                2
                            )
                        )
                    )


                    for (
                        image_index,
                        image_path
                    ) in enumerate(
                        faq_images
                    ):

                        path = Path(
                            image_path
                        )


                        if not path.exists():

                            continue


                        with image_columns[
                            image_index
                            % len(
                                image_columns
                            )
                        ]:

                            st.image(
                                str(
                                    path
                                ),
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


        st.divider()


    # =====================================================
    # 가이드 결과
    # =====================================================

    st.subheader(
        "📘 관련 가이드"
    )


    if not results:

        st.warning(
            "관련 가이드 기준을 찾지 못했습니다."
        )


    else:

        for number, result in enumerate(
            results,
            start=1
        ):

            with st.container(
                border=True
            ):

                location = (
                    result.get(
                        "source",
                        ""
                    )
                )


                if (
                    result.get(
                        "page"
                    )
                    is not None
                ):

                    location += (
                        f" · "
                        f"{result['page']}페이지"
                    )


                st.markdown(
                    f"### {number}. "
                    f"{location}"
                )


                score = (
                    result.get(
                        "score",
                        0
                    )
                )


                if score >= 0.30:

                    label = (
                        "높은 관련도"
                    )

                    color = (
                        "#16a34a"
                    )


                elif score >= 0.15:

                    label = (
                        "관련 가능성 있음"
                    )

                    color = (
                        "#f59e0b"
                    )


                else:

                    label = (
                        "참고 결과"
                    )

                    color = (
                        "#dc2626"
                    )


                st.markdown(
                    f"""
                    <div style="
                        display:inline-block;
                        padding:6px 12px;
                        border-radius:999px;
                        background-color:{color};
                        color:white;
                        font-weight:600;
                        margin-bottom:10px;
                    ">
                        {label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


                st.write(
                    result.get(
                        "text",
                        ""
                    )
                )


    # =====================================================
    # 관리자 문의
    # =====================================================

    st.divider()


    st.subheader(
        "원하는 기준을 찾지 못했나요?"
    )


    st.caption(
        "FAQ와 가이드 검색 결과만으로 "
        "판단하기 어려운 경우 "
        "관리자에게 직접 문의할 수 있습니다."
    )


    if st.button(
        "📨 관리자에게 문의",
        width="stretch"
    ):

        if (
            "pm_pasted_images"
            not in st.session_state
        ):

            st.session_state[
                "pm_pasted_images"
            ] = []


        show_pm_inquiry_dialog()


# =========================================================
# 문의 성공
# =========================================================

if (
    "pm_inquiry_success"
    in st.session_state
):

    inquiry_id = (
        st.session_state.pop(
            "pm_inquiry_success"
        )
    )


    st.success(
        "✅ 관리자에게 문의가 등록되었습니다."
    )


    st.caption(
        f"문의 번호: "
        f"{inquiry_id}"
    )