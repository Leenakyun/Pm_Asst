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

from backend.settings_service import (
    get_project_settings,
    set_vision_settings
)

from backend.vision_service import (
    vision_available
)


# =========================================================
# 권한 확인
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
# 페이지
# =========================================================

st.title(
    "⚙️ 프로젝트 설정"
)

st.caption(
    "프로젝트별 기능과 외부 AI 사용 여부를 설정합니다."
)


settings = (
    get_project_settings()
)


# =========================================================
# Vision
# =========================================================

st.subheader(
    "🖼️ 이미지 기반 가이드 검색"
)

st.write(
    "Vision을 활성화하면 작업자의 가이드 검색 화면에 "
    "이미지 첨부 기능이 표시됩니다."
)

st.write(
    "작업자가 첨부한 이미지를 AI가 분석하고 "
    "이미지 상황을 검색 키워드로 변환하여 "
    "FAQ와 작업 가이드 검색을 보조합니다."
)

st.warning(
    "Vision을 활성화하면 가이드 검색에 첨부한 "
    "작업 이미지가 외부 AI API로 전송됩니다. "
    "고객사 보안 정책 및 데이터 반출 기준을 "
    "확인한 뒤 활성화하세요."
)


# =========================================================
# API 상태
# =========================================================

if vision_available():

    st.success(
        "✅ Vision API 사용 가능"
    )

else:

    st.error(
        "❌ OPENAI_API_KEY가 설정되어 있지 않습니다."
    )


st.divider()


# =========================================================
# 현재 설정
# =========================================================

current_enabled = bool(
    settings.get(
        "vision_enabled",
        False
    )
)

current_detail = (
    settings.get(
        "vision_detail",
        "low"
    )
)


vision_enabled = st.toggle(
    "Vision 이미지 검색 사용",
    value=current_enabled
)


detail_options = [
    "low",
    "high"
]


try:

    detail_index = (
        detail_options.index(
            current_detail
        )
    )

except ValueError:

    detail_index = 0


vision_detail = st.selectbox(
    "이미지 분석 상세도",
    options=detail_options,
    index=detail_index,
    disabled=(
        not vision_enabled
    ),
    help=(
        "low는 비용과 속도를 우선합니다. "
        "작업 화면 판독력이 부족한 경우 high를 테스트할 수 있습니다."
    )
)


# =========================================================
# 저장
# =========================================================

if st.button(
    "설정 저장",
    type="primary",
    width="stretch"
):

    if (
        vision_enabled
        and not vision_available()
    ):

        st.error(
            "OPENAI_API_KEY가 없어서 "
            "Vision을 활성화할 수 없습니다."
        )

    else:

        set_vision_settings(
            enabled=vision_enabled,
            detail=vision_detail
        )

        st.success(
            "프로젝트 설정을 저장했습니다."
        )

        st.rerun()


st.divider()


# =========================================================
# 현재 상태
# =========================================================

if current_enabled:

    st.info(
        "현재 Vision 검색이 활성화되어 있습니다. "
        "작업자의 가이드 검색 화면에 이미지 첨부 기능이 표시됩니다."
    )

else:

    st.info(
        "현재 Vision 검색은 비활성화되어 있습니다. "
        "작업자의 가이드 검색 화면에는 이미지 첨부 기능이 표시되지 않습니다. "
        "PM 문의 시 이미지 첨부 기능은 계속 사용할 수 있습니다."
    )