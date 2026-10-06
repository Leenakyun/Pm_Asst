import html
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


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
# 유틸
# =========================================================

def get_chunk_value(
    chunk,
    key,
    default=None
):

    if isinstance(
        chunk,
        dict
    ):

        return chunk.get(
            key,
            default
        )

    return getattr(
        chunk,
        key,
        default
    )


def get_section_title(
    text: str,
    index: int
) -> str:

    if not text:

        return f"{index}. 가이드 항목"


    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


    if not lines:

        return f"{index}. 가이드 항목"


    first_line = lines[0]


    if (
        first_line.startswith("[")
        and first_line.endswith("]")
    ):

        first_line = (
            first_line[1:-1]
        )


    if len(first_line) > 80:

        first_line = (
            first_line[:80]
            + "..."
        )


    return first_line


def text_to_html(
    text: str,
    keyword: str = ""
) -> str:
    """
    가이드 원문을 안전한 HTML로 변환한다.
    검색어가 있으면 강조한다.
    """

    if not text:

        return ""


    safe_text = html.escape(
        text
    )


    # 줄바꿈 유지
    safe_text = safe_text.replace(
        "\n",
        "<br>"
    )


    if keyword.strip():

        safe_keyword = html.escape(
            keyword.strip()
        )

        # 단순 대소문자 일치 강조
        # 한글 검색에는 그대로 잘 동작
        safe_text = safe_text.replace(
            safe_keyword,
            (
                "<mark>"
                f"{safe_keyword}"
                "</mark>"
            )
        )


    return safe_text


# =========================================================
# 페이지
# =========================================================

st.title(
    "📖 전체 가이드"
)

st.caption(
    "현재 프로젝트에 적용 중인 "
    "작업 가이드 전체 내용을 확인할 수 있습니다."
)


# =========================================================
# 활성 가이드
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


# =========================================================
# 가이드 정보
# =========================================================

with st.container(
    border=True
):

    col1, col2 = st.columns(
        2
    )


    with col1:

        st.metric(
            "현재 가이드 버전",
            active_guide.get(
                "version",
                ""
            )
        )


    with col2:

        uploaded_at = (
            active_guide.get(
                "uploaded_at",
                ""
            )
        )


        uploaded_date = (
            uploaded_at.split("T")[0]
            if uploaded_at
            else "-"
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
# 가이드 불러오기
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

    st.info(
        "표시할 가이드 내용이 없습니다."
    )

    st.stop()


# =========================================================
# 데이터 정리
# =========================================================

guide_sections = []


for index, chunk in enumerate(
    chunks,
    start=1
):

    text = get_chunk_value(
        chunk,
        "text",
        ""
    )

    page = get_chunk_value(
        chunk,
        "page"
    )

    source = get_chunk_value(
        chunk,
        "source",
        ""
    )


    title = get_section_title(
        text,
        index
    )


    guide_sections.append({
        "index": index,
        "title": title,
        "text": text,
        "page": page,
        "source": source,
    })


# =========================================================
# 검색
# =========================================================

st.subheader(
    "🔍 가이드 내 검색"
)


guide_keyword = st.text_input(
    "가이드 내 검색",
    placeholder=(
        "예: 포인트 부족, "
        "가림, 큐보이드 방향"
    ),
    label_visibility="collapsed"
)


if guide_keyword.strip():

    keyword_lower = (
        guide_keyword
        .strip()
        .lower()
    )


    visible_sections = [

        section

        for section
        in guide_sections

        if (
            keyword_lower
            in (
                section["title"]
                + " "
                + section["text"]
            ).lower()
        )
    ]


    st.caption(
        f"'{guide_keyword.strip()}' "
        f"검색 결과 "
        f"{len(visible_sections)}개 항목"
    )


else:

    visible_sections = (
        guide_sections
    )


if not visible_sections:

    st.warning(
        "검색어와 일치하는 "
        "가이드 항목이 없습니다."
    )

    st.stop()


st.caption(
    "💡 ← → 방향키 또는 하단 버튼으로 이동할 수 있습니다. "
    "본문 끝에서 마우스 휠을 한 번 더 움직여도 "
    "이전·다음 항목으로 넘어갑니다."
)


# =========================================================
# 책 뷰어 HTML 생성
# =========================================================

toc_html_parts = []

page_html_parts = []


for viewer_index, section in enumerate(
    visible_sections
):

    title = html.escape(
        section[
            "title"
        ]
    )

    text_html = text_to_html(
        section[
            "text"
        ],
        guide_keyword
    )


    info_parts = []


    if section[
        "page"
    ] is not None:

        info_parts.append(
            f"{section['page']}페이지"
        )


    if section[
        "source"
    ]:

        info_parts.append(
            html.escape(
                str(
                    section[
                        "source"
                    ]
                )
            )
        )


    info_text = " · ".join(
        info_parts
    )


    # =====================================================
    # 목차
    # =====================================================

    toc_html_parts.append(
        f"""
        <button
            class="toc-item"
            data-index="{viewer_index}"
            onclick="goToPage({viewer_index})"
        >
            <span class="toc-number">
                {viewer_index + 1}
            </span>

            <span class="toc-title">
                {title}
            </span>
        </button>
        """
    )


    # =====================================================
    # 페이지
    # =====================================================

    page_html_parts.append(
        f"""
        <section
            class="guide-page"
            data-page="{viewer_index}"
        >

            <div class="page-heading">

                <div class="chapter-label">
                    GUIDE {viewer_index + 1}
                </div>

                <h1>
                    {title}
                </h1>

                <div class="page-meta">
                    {info_text}
                </div>

            </div>


            <div
                class="page-content"
                id="page-content-{viewer_index}"
            >
                {text_html}
            </div>

        </section>
        """
    )


toc_html = "\n".join(
    toc_html_parts
)

pages_html = "\n".join(
    page_html_parts
)


total_pages = len(
    visible_sections
)


# =========================================================
# 책 뷰어
# =========================================================

viewer_html = f"""
<!DOCTYPE html>

<html lang="ko">

<head>

<meta charset="UTF-8">

<style>

    * {{
        box-sizing: border-box;
    }}


    html,
    body {{

        margin: 0;
        padding: 0;

        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            "Apple SD Gothic Neo",
            "Noto Sans KR",
            sans-serif;

        background: transparent;

        overflow: hidden;
    }}


    .viewer {{

        width: 100%;
        height: 760px;

        display: grid;

        grid-template-columns:
            260px
            minmax(0, 1fr);

        gap: 18px;
    }}


    /* ==================================================
       목차
       ================================================== */

    .toc {{

        height: 760px;

        overflow-y: auto;

        padding:
            18px
            12px;

        border:
            1px solid
            rgba(128, 128, 128, 0.25);

        border-radius:
            14px;

        background:
            rgba(128, 128, 128, 0.04);
    }}


    .toc-header {{

        font-size: 18px;
        font-weight: 700;

        margin:
            0
            6px
            14px
            6px;
    }}


    .toc-item {{

        width: 100%;

        display: flex;

        align-items: flex-start;

        gap: 10px;

        text-align: left;

        border: 0;

        background: transparent;

        padding:
            10px
            8px;

        margin-bottom: 3px;

        border-radius: 8px;

        cursor: pointer;

        color: inherit;

        font-size: 14px;
    }}


    .toc-item:hover {{

        background:
            rgba(128, 128, 128, 0.12);
    }}


    .toc-item.active {{

        background:
            rgba(128, 128, 128, 0.18);

        font-weight: 700;
    }}


    .toc-number {{

        flex:
            0
            0
            25px;

        opacity: 0.6;
    }}


    .toc-title {{

        line-height: 1.45;
    }}


    /* ==================================================
       책
       ================================================== */

    .book-shell {{

        min-width: 0;

        height: 760px;

        display: flex;

        flex-direction: column;

        border:
            1px solid
            rgba(128, 128, 128, 0.25);

        border-radius: 16px;

        overflow: hidden;

        background:
            rgba(255, 255, 255, 0.03);
    }}


    .book {{

        flex: 1;

        min-height: 0;

        position: relative;

        padding:
            42px
            55px
            20px
            55px;
    }}


    .guide-page {{

        display: none;

        height: 100%;

        min-height: 0;
    }}


    .guide-page.active {{

        display: flex;

        flex-direction: column;
    }}


    .page-heading {{

        flex: 0 0 auto;

        padding-bottom: 20px;

        border-bottom:
            1px solid
            rgba(128, 128, 128, 0.18);
    }}


    .chapter-label {{

        font-size: 12px;

        letter-spacing: 0.12em;

        opacity: 0.5;

        margin-bottom: 8px;
    }}


    h1 {{

        margin:
            0
            0
            10px
            0;

        font-size: 28px;

        line-height: 1.35;
    }}


    .page-meta {{

        min-height: 20px;

        font-size: 13px;

        opacity: 0.55;
    }}


    .page-content {{

        flex: 1;

        min-height: 0;

        overflow-y: auto;

        padding:
            28px
            6px
            36px
            0;

        font-size: 16px;

        line-height: 1.95;

        word-break: keep-all;

        overflow-wrap: break-word;
    }}


    mark {{

        padding:
            1px
            3px;

        border-radius: 3px;
    }}


    /* ==================================================
       하단 navigation
       ================================================== */

    .navigation {{

        flex:
            0
            0
            70px;

        display: grid;

        grid-template-columns:
            1fr
            auto
            1fr;

        align-items: center;

        gap: 12px;

        padding:
            12px
            22px;

        border-top:
            1px solid
            rgba(128, 128, 128, 0.18);

        background:
            rgba(128, 128, 128, 0.03);
    }}


    .nav-button {{

        min-height: 42px;

        padding:
            8px
            18px;

        border:
            1px solid
            rgba(128, 128, 128, 0.30);

        border-radius: 9px;

        background: transparent;

        color: inherit;

        cursor: pointer;

        font-size: 14px;
    }}


    .nav-button:hover:not(:disabled) {{

        background:
            rgba(128, 128, 128, 0.10);
    }}


    .nav-button:disabled {{

        opacity: 0.3;

        cursor: default;
    }}


    #previous-button {{

        justify-self: start;
    }}


    #next-button {{

        justify-self: end;
    }}


    .page-counter {{

        min-width: 80px;

        text-align: center;

        font-size: 14px;

        opacity: 0.7;
    }}


    /* ==================================================
       모바일
       ================================================== */

    @media (
        max-width: 800px
    ) {{

        .viewer {{

            grid-template-columns: 1fr;

            height: 820px;
        }}


        .toc {{

            height: 160px;
        }}


        .book-shell {{

            height: 640px;
        }}


        .book {{

            padding:
                28px
                25px
                15px
                25px;
        }}


        h1 {{

            font-size: 23px;
        }}

    }}

</style>

</head>


<body>


<div class="viewer">


    <!-- ================================================
         목차
         ================================================ -->

    <aside class="toc">

        <div class="toc-header">
            📑 목차
        </div>

        {toc_html}

    </aside>


    <!-- ================================================
         책
         ================================================ -->

    <main class="book-shell">


        <div
            class="book"
            id="book"
        >

            {pages_html}

        </div>


        <!-- ============================================
             navigation
             ============================================ -->

        <div class="navigation">

            <button
                class="nav-button"
                id="previous-button"
                onclick="previousPage()"
            >
                ← 이전
            </button>


            <div
                class="page-counter"
                id="page-counter"
            >
                1 / {total_pages}
            </div>


            <button
                class="nav-button"
                id="next-button"
                onclick="nextPage()"
            >
                다음 →
            </button>

        </div>


    </main>


</div>


<script>

    const totalPages = {total_pages};

    let currentPage = 0;

    let wheelLocked = false;


    // ==================================================
    // 페이지 이동
    // ==================================================

    function goToPage(index) {{

        if (
            index < 0
            ||
            index >= totalPages
        ) {{

            return;

        }}


        currentPage = index;


        const pages = (
            document.querySelectorAll(
                ".guide-page"
            )
        );


        pages.forEach(
            (page, pageIndex) => {{

                if (
                    pageIndex === currentPage
                ) {{

                    page.classList.add(
                        "active"
                    );

                }}

                else {{

                    page.classList.remove(
                        "active"
                    );

                }}

            }}
        );


        const tocItems = (
            document.querySelectorAll(
                ".toc-item"
            )
        );


        tocItems.forEach(
            (item, itemIndex) => {{

                if (
                    itemIndex === currentPage
                ) {{

                    item.classList.add(
                        "active"
                    );

                    item.scrollIntoView({{
                        behavior: "smooth",
                        block: "nearest"
                    }});

                }}

                else {{

                    item.classList.remove(
                        "active"
                    );

                }}

            }}
        );


        const counter = (
            document.getElementById(
                "page-counter"
            )
        );


        counter.textContent =
            (currentPage + 1)
            + " / "
            + totalPages;


        const previousButton = (
            document.getElementById(
                "previous-button"
            )
        );


        const nextButton = (
            document.getElementById(
                "next-button"
            )
        );


        previousButton.disabled = (
            currentPage === 0
        );


        nextButton.disabled = (
            currentPage
            ===
            totalPages - 1
        );


        // 새 페이지를 열면
        // 본문 맨 위에서 시작
        const content = (
            document.getElementById(
                "page-content-"
                + currentPage
            )
        );


        if (content) {{

            content.scrollTop = 0;

        }}

    }}


    function previousPage() {{

        goToPage(
            currentPage - 1
        );

    }}


    function nextPage() {{

        goToPage(
            currentPage + 1
        );

    }}


    // ==================================================
    // 키보드
    // ==================================================

    document.addEventListener(
        "keydown",
        function(event) {{

            if (
                event.key
                ===
                "ArrowLeft"
            ) {{

                event.preventDefault();

                previousPage();

            }}


            if (
                event.key
                ===
                "ArrowRight"
            ) {{

                event.preventDefault();

                nextPage();

            }}

        }}
    );


    // ==================================================
    // 마우스 휠
    //
    // 본문 중간에서는 일반 스크롤.
    //
    // 맨 아래에서 더 아래로:
    // 다음 페이지
    //
    // 맨 위에서 더 위로:
    // 이전 페이지
    // ==================================================

    document.addEventListener(
        "wheel",
        function(event) {{

            const content = (
                document.getElementById(
                    "page-content-"
                    + currentPage
                )
            );


            if (!content) {{

                return;

            }}


            const tolerance = 4;


            const atTop = (
                content.scrollTop
                <=
                tolerance
            );


            const atBottom = (
                content.scrollTop
                + content.clientHeight
                >=
                content.scrollHeight
                - tolerance
            );


            // 아래쪽 경계
            if (
                event.deltaY > 0
                &&
                atBottom
                &&
                currentPage
                <
                totalPages - 1
            ) {{

                event.preventDefault();


                if (!wheelLocked) {{

                    wheelLocked = true;

                    nextPage();


                    setTimeout(
                        function() {{

                            wheelLocked = false;

                        }},
                        450
                    );

                }}

            }}


            // 위쪽 경계
            else if (
                event.deltaY < 0
                &&
                atTop
                &&
                currentPage > 0
            ) {{

                event.preventDefault();


                if (!wheelLocked) {{

                    wheelLocked = true;

                    goToPage(
                        currentPage - 1
                    );


                    const previousContent = (
                        document.getElementById(
                            "page-content-"
                            + currentPage
                        )
                    );


                    if (previousContent) {{

                        previousContent.scrollTop =
                            previousContent.scrollHeight;

                    }}


                    setTimeout(
                        function() {{

                            wheelLocked = false;

                        }},
                        450
                    );

                }}

            }}

        }},
        {{
            passive: false
        }}
    );


    // ==================================================
    // 최초 페이지
    // ==================================================

    goToPage(0);

</script>


</body>

</html>
"""


components.html(
    viewer_html,
    height=790,
    scrolling=False
)