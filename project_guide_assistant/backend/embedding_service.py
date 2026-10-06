import re
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# 질문 정규화
# =========================================================

def normalize_question(
    question: str
) -> str:
    """
    질문 비교를 위한 간단한 정규화
    """

    question = question.strip().lower()

    # 여러 공백 -> 한 칸
    question = re.sub(
        r"\s+",
        " ",
        question
    )

    # 비교에 크게 필요 없는 일부 문장부호 제거
    question = re.sub(
        r"[?？!！.,。]",
        "",
        question
    )

    return question


# =========================================================
# 비슷한 질문 그룹화
# =========================================================

def cluster_similar_questions(
    questions: List[Dict],
    similarity_threshold: float = 0.55
) -> List[Dict]:
    """
    비슷한 질문을 하나의 그룹으로 묶는다.

    questions 형식:

    [
        {
            "question": "...",
            "worker_id": "...",
            "searched_at": "...",
            ...
        }
    ]
    """

    if not questions:
        return []


    # -----------------------------------------------------
    # 유효한 질문만 추출
    # -----------------------------------------------------

    valid_items = []

    for item in questions:

        question = (
            item.get(
                "question",
                ""
            )
            .strip()
        )

        if not question:
            continue

        valid_items.append(
            item
        )


    if not valid_items:
        return []


    # 질문이 하나뿐이면 그대로 한 그룹
    if len(valid_items) == 1:

        item = valid_items[0]

        return [
            {
                "representative_question":
                    item["question"],

                "count":
                    1,

                "questions":
                    [item]
            }
        ]


    # -----------------------------------------------------
    # 비교용 문자열
    # -----------------------------------------------------

    normalized_questions = [
        normalize_question(
            item["question"]
        )
        for item in valid_items
    ]


    # -----------------------------------------------------
    # 문자 단위 TF-IDF
    # -----------------------------------------------------

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
        sublinear_tf=True
    )


    matrix = vectorizer.fit_transform(
        normalized_questions
    )


    similarity_matrix = cosine_similarity(
        matrix
    )


    # -----------------------------------------------------
    # Greedy clustering
    # -----------------------------------------------------

    visited = set()

    clusters = []


    for index in range(
        len(valid_items)
    ):

        if index in visited:
            continue


        cluster_indices = [
            index
        ]

        visited.add(
            index
        )


        # 현재 질문과 유사한 질문 수집
        for other_index in range(
            index + 1,
            len(valid_items)
        ):

            if other_index in visited:
                continue


            similarity = float(
                similarity_matrix[
                    index
                ][
                    other_index
                ]
            )


            if (
                similarity
                >= similarity_threshold
            ):

                cluster_indices.append(
                    other_index
                )

                visited.add(
                    other_index
                )


        cluster_items = [
            valid_items[i]
            for i in cluster_indices
        ]


        # 가장 먼저 나온 질문을 대표 문장으로 사용
        representative = (
            cluster_items[0][
                "question"
            ]
        )


        clusters.append({
            "representative_question":
                representative,

            "count":
                len(cluster_items),

            "questions":
                cluster_items
        })


    # -----------------------------------------------------
    # 많이 나온 그룹 순
    # -----------------------------------------------------

    clusters.sort(
        key=lambda x:
            x["count"],
        reverse=True
    )


    return clusters