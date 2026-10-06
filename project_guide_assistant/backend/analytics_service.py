from typing import List, Dict


# =========================================================
# FAQ / 가이드 개선 후보 계산
# =========================================================

def build_improvement_candidates(
    question_groups: List[Dict],
    inquiries: List[Dict]
) -> List[Dict]:
    """
    유사 질문 그룹과 PM 문의 데이터를 기반으로
    FAQ 후보 / 가이드 개선 필요 항목을 계산한다.
    """

    inquiry_search_ids = {
        inquiry.get("search_id")
        for inquiry in inquiries
        if inquiry.get("search_id")
    }

    candidates = []


    for group in question_groups:

        questions = group.get(
            "questions",
            []
        )

        search_count = len(
            questions
        )

        if search_count == 0:
            continue


        # -------------------------------------------------
        # 이 질문 그룹에서 PM 문의로 이어진 검색 수
        # -------------------------------------------------

        inquiry_count = sum(
            1
            for item in questions
            if item.get("search_id")
            in inquiry_search_ids
        )


        inquiry_rate = (
            inquiry_count
            / search_count
            * 100
        )


        # -------------------------------------------------
        # 분류
        # -------------------------------------------------

        candidate_type = None
        priority_score = 0


        # 검색 자체가 반복되는 경우
        if search_count >= 3:

            priority_score += (
                search_count * 2
            )


        # PM 문의 전환이 높은 경우
        if inquiry_rate >= 30:

            priority_score += 5


        if inquiry_rate >= 50:

            priority_score += 5


        # -------------------------------------------------
        # 후보 유형
        # -------------------------------------------------

        if (
            search_count >= 3
            and inquiry_rate >= 30
        ):

            candidate_type = (
                "가이드 개선 필요"
            )

        elif search_count >= 2:

            candidate_type = (
                "FAQ 후보"
            )


        if not candidate_type:
            continue


        candidates.append({
            "representative_question":
                group.get(
                    "representative_question",
                    ""
                ),

            "search_count":
                search_count,

            "inquiry_count":
                inquiry_count,

            "inquiry_rate":
                inquiry_rate,

            "candidate_type":
                candidate_type,

            "priority_score":
                priority_score,

            "questions":
                questions
        })


    # 우선순위 높은 순
    candidates.sort(
        key=lambda x: (
            x["priority_score"],
            x["search_count"]
        ),
        reverse=True
    )


    return candidates