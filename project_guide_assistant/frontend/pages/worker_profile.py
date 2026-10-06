import sys
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


from backend.profile_service import (
    get_or_create_profile,
    update_profile_name,
)


if (
    not st.session_state.get("logged_in")
    or st.session_state.get("role") != "worker"
):
    st.error("작업자만 접근할 수 있습니다.")
    st.stop()


worker_email = st.session_state.get("worker_id", "")

if not worker_email:
    st.error("작업자 로그인 정보가 없습니다.")
    st.stop()


profile = get_or_create_profile(worker_email)


st.title("👤 프로필")
st.caption("작업자 프로필 정보를 관리합니다.")


with st.container(border=True):
    st.markdown("### 계정 정보")
    st.text_input(
        "이메일",
        value=worker_email,
        disabled=True,
    )

    name = st.text_input(
        "이름",
        value=profile.get("name", ""),
        placeholder="업무에서 사용할 이름을 입력해 주세요.",
    )

    if st.button(
        "프로필 저장",
        type="primary",
        width="stretch",
    ):
        try:
            updated = update_profile_name(
                worker_email,
                name,
            )

            st.session_state["worker_name"] = updated.get(
                "name",
                ""
            )

            st.success("프로필을 저장했습니다.")
            st.rerun()

        except ValueError as error:
            st.warning(str(error))
