from typing import List, Dict, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# 검색 엔진 생성
# =========================================================

def build_search_engine(
    chunks: List[Dict]
) -> Tuple[TfidfVectorizer, object]:
    """
    가이드 chunk 목록을 기반으로 TF-IDF 검색 엔진 생성
    """

    if not chunks:
        raise ValueError(
            "검색할 가이드 내용이 없습니다."
        )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(
        texts
    )

    return vectorizer, matrix


# =========================================================
# 가이드 검색
# =========================================================

def search_guide(
    question: str,
    chunks: List[Dict],
    vectorizer,
    matrix,
    top_k: int = 3
) -> List[Dict]:
    """
    작업자의 자연어 질문과 유사한 가이드 섹션 검색
    """

    question = question.strip()

    if not question:
        return []

    question_vector = vectorizer.transform(
        [question]
    )

    scores = cosine_similarity(
        question_vector,
        matrix
    ).flatten()

    ranked_indices = (
        scores.argsort()[::-1]
    )

    if len(ranked_indices) == 0:
        return []

    top_score = float(
        scores[ranked_indices[0]]
    )

    results = []

    for index in ranked_indices:

        score = float(
            scores[index]
        )

        # 관련도가 너무 낮은 결과 제거
        if score < 0.10:
            continue

        # 1위 결과와 차이가 너무 큰 결과 제거
        if (
            top_score > 0
            and score < top_score * 0.35
        ):
            continue

        results.append({
            "text":
                chunks[index]["text"],

            "page":
                chunks[index].get("page"),

            "source":
                chunks[index].get(
                    "source",
                    ""
                ),

            "score":
                score
        })

        if len(results) >= top_k:
            break

    return results