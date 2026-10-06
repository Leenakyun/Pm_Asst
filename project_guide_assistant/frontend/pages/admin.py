import sys
from pathlib import Path

import streamlit as st



# =========================================================
# 관리자 권한 확인
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
# 프로젝트 루트를 import 경로에 추가
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


from backend.guide_management_service import (
    get_all_guides,
    get_active_guide,
    upload_guide,
    activate_guide,
    delete_guide
)


# =========================================================
# 화면 기본 설정
# =========================================================

st.title("🧑‍💼 관리자")

st.caption(
    "작업 가이드 버전을 등록하고 "
    "현재 사용 중인 가이드를 관리합니다."
)


# =========================================================
# 현재 적용 가이드
# =========================================================

st.subheader("📌 현재 적용 가이드")

active_guide = get_active_guide()


if active_guide:

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "현재 버전",
            active_guide["version"]
        )

    with col2:
        uploaded_date = (
            active_guide["uploaded_at"]
            .replace("T", " ")
        )

        st.metric(
            "등록일",
            uploaded_date
        )

    with col3:
        st.metric(
            "파일명",
            active_guide["file_name"]
        )

else:

    st.warning(
        "현재 적용 중인 가이드가 없습니다."
    )


st.divider()


# =========================================================
# 새 가이드 업로드
# =========================================================

st.subheader("📤 새 가이드 등록")


guide_version = st.text_input(
    "가이드 버전",
    placeholder="예: v1.0"
)


guide_file = st.file_uploader(
    "가이드 파일",
    type=[
        "pdf",
        "docx",
        "txt"
    ],
    accept_multiple_files=False
)


if st.button(
    "새 버전 등록",
    type="primary",
    width="stretch"
):

    if not guide_version.strip():

        st.warning(
            "가이드 버전을 입력해 주세요."
        )

    elif guide_file is None:

        st.warning(
            "가이드 파일을 선택해 주세요."
        )

    else:

        try:

            new_guide = upload_guide(

                file_bytes=
                    guide_file.getvalue(),

                original_file_name=
                    guide_file.name,

                version=
                    guide_version
            )


            st.success(
                f"{new_guide['version']} 버전이 "
                "등록되었습니다."
            )


            st.rerun()


        except ValueError as error:

            st.error(
                str(error)
            )


st.divider()


# =========================================================
# 등록된 가이드 목록
# =========================================================

st.subheader("📚 등록된 가이드 버전")


guides = get_all_guides()


if not guides:

    st.info(
        "등록된 가이드가 없습니다."
    )


else:

    for guide in guides:

        with st.container(
            border=True
        ):

            col1, col2 = st.columns(
                [3, 1]
            )


            with col1:

                if guide["is_active"]:

                    st.markdown(
                        f"### 🟢 {guide['version']}"
                    )

                    st.success(
                        "현재 사용 중"
                    )

                else:

                    st.markdown(
                        f"### ⚪ {guide['version']}"
                    )


                st.write(
                    f"**파일명:** "
                    f"{guide['file_name']}"
                )


                st.write(
                    f"**등록일:** "
                    f"{guide['uploaded_at'].replace('T', ' ')}"
                )


            with col2:

                if not guide["is_active"]:

                    if st.button(
                        "현재 버전으로 변경",
                        key=(
                            "activate_"
                            + guide["guide_id"]
                        ),
                        width="stretch"
                    ):

                        try:

                            activate_guide(
                                guide["guide_id"]
                            )

                            st.success(
                                "현재 가이드가 변경되었습니다."
                            )

                            st.rerun()

                        except ValueError as error:

                            st.error(
                                str(error)
                            )


                    if st.button(
                        "삭제",
                        key=(
                            "delete_"
                            + guide["guide_id"]
                        ),
                        width="stretch"
                    ):

                        try:

                            delete_guide(
                                guide["guide_id"]
                            )

                            st.success(
                                "가이드가 삭제되었습니다."
                            )

                            st.rerun()

                        except ValueError as error:

                            st.error(
                                str(error)
                            )

                else:

                    st.caption(
                        "현재 사용 중인 가이드는 "
                        "삭제할 수 없습니다."
                    )