import re
import uuid

from pathlib import Path
from datetime import datetime

from backend.storage import (
    DATA_DIR,
    load_jsonl,
    overwrite_jsonl,
    save_binary_file
)


# =========================================================
# 경로
# =========================================================

FAQ_DIR = (
    DATA_DIR
    / "faqs"
)

FAQ_IMAGE_DIR = (
    FAQ_DIR
    / "images"
)

FAQ_FILE = (
    FAQ_DIR
    / "faqs.jsonl"
)


# =========================================================
# 질문 정규화
# =========================================================

def normalize_faq_question(
    question: str
) -> str:

    question = (
        question
        .strip()
        .lower()
    )

    question = re.sub(
        r"\s+",
        " ",
        question
    )

    question = re.sub(
        r"[?？!！.,。]",
        "",
        question
    )

    return question


# =========================================================
# 전체 FAQ 조회
# =========================================================

def get_all_faqs():

    faqs = load_jsonl(
        FAQ_FILE
    )

    return sorted(
        faqs,
        key=lambda x:
            x.get(
                "created_at",
                ""
            ),
        reverse=True
    )


# =========================================================
# 사용 중인 FAQ
# =========================================================

def get_active_faqs():

    return [
        faq
        for faq in get_all_faqs()
        if faq.get(
            "is_active",
            True
        )
    ]


# =========================================================
# FAQ 생성
# =========================================================

def create_faq(
    question: str,
    answer: str,
    guide_version: str | None = None,
    source_type: str = "manual",
    source_question: str | None = None,
    uploaded_images: list | None = None
):

    question = question.strip()
    answer = answer.strip()

    if not question:
        raise ValueError(
            "FAQ 질문을 입력해 주세요."
        )

    if not answer:
        raise ValueError(
            "FAQ 답변을 입력해 주세요."
        )

    normalized_question = (
        normalize_faq_question(
            question
        )
    )

    faqs = get_all_faqs()

    # -----------------------------------------------------
    # 동일 질문 중복 등록 방지
    # -----------------------------------------------------

    for faq in faqs:

        existing_question = (
            normalize_faq_question(
                faq.get(
                    "question",
                    ""
                )
            )
        )

        if (
            existing_question
            == normalized_question
        ):
            raise ValueError(
                "이미 동일한 FAQ가 등록되어 있습니다."
            )

    faq_id = uuid.uuid4().hex[:10]
    image_paths = []

    # -----------------------------------------------------
    # FAQ 이미지 저장
    # -----------------------------------------------------

    if uploaded_images:

        for index, image in enumerate(
            uploaded_images,
            start=1
        ):

            extension = (
                Path(image.name)
                .suffix
                .lower()
            )

            if extension not in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp"
            }:
                extension = ".png"

            file_name = (
                f"{faq_id}_"
                f"{index}_"
                f"{uuid.uuid4().hex[:6]}"
                f"{extension}"
            )

            saved_path = save_binary_file(
                file_bytes=image.getvalue(),
                directory=FAQ_IMAGE_DIR,
                file_name=file_name
            )

            image_paths.append(
                saved_path
            )

    faq = {
        "faq_id": faq_id,
        "question": question,
        "answer": answer,
        "created_at": (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),
        "guide_version": guide_version,
        "source_type": source_type,
        "source_question": source_question,
        "images": image_paths,
        "is_active": True
    }

    faqs.append(
        faq
    )

    overwrite_jsonl(
        FAQ_FILE,
        faqs
    )

    return faq


# =========================================================
# FAQ 활성 / 비활성
# =========================================================

def set_faq_active(
    faq_id: str,
    is_active: bool
):

    faqs = get_all_faqs()
    found = False

    for faq in faqs:

        if faq.get(
            "faq_id"
        ) == faq_id:

            faq[
                "is_active"
            ] = is_active

            found = True
            break

    if not found:
        raise ValueError(
            "FAQ를 찾을 수 없습니다."
        )

    overwrite_jsonl(
        FAQ_FILE,
        faqs
    )


# =========================================================
# FAQ 삭제
# =========================================================

def delete_faq(
    faq_id: str
):

    faqs = get_all_faqs()

    target = next(
        (
            faq
            for faq in faqs
            if faq.get(
                "faq_id"
            ) == faq_id
        ),
        None
    )

    if target is None:
        raise ValueError(
            "FAQ를 찾을 수 없습니다."
        )

    # FAQ에 연결된 이미지도 함께 삭제
    for image_path in target.get(
        "images",
        []
    ):
        try:
            path = Path(image_path)
            if path.exists():
                path.unlink()
        except OSError:
            pass

    new_faqs = [
        faq
        for faq in faqs
        if faq.get(
            "faq_id"
        ) != faq_id
    ]

    overwrite_jsonl(
        FAQ_FILE,
        new_faqs
    )


# =========================================================
# FAQ 검색
# =========================================================

def search_faqs(
    question: str,
    similarity_threshold: float = 0.35,
    top_k: int = 3
):
    """
    활성 FAQ 중 사용자 질문과 유사한 항목 검색
    """

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    question = question.strip()

    if not question:
        return []

    faqs = get_active_faqs()

    if not faqs:
        return []

    faq_questions = [
        normalize_faq_question(
            faq.get(
                "question",
                ""
            )
        )
        for faq in faqs
    ]

    normalized_query = (
        normalize_faq_question(
            question
        )
    )

    texts = (
        faq_questions
        + [
            normalized_query
        ]
    )

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(
        texts
    )

    query_vector = matrix[-1]
    faq_matrix = matrix[:-1]

    scores = cosine_similarity(
        query_vector,
        faq_matrix
    ).flatten()

    ranked_indices = (
        scores.argsort()[::-1]
    )

    results = []

    for index in ranked_indices:

        score = float(
            scores[index]
        )

        if score < similarity_threshold:
            continue

        faq = faqs[index]

        results.append({
            "faq_id": faq.get(
                "faq_id"
            ),
            "question": faq.get(
                "question",
                ""
            ),
            "answer": faq.get(
                "answer",
                ""
            ),
            "guide_version": faq.get(
                "guide_version"
            ),
            "images": faq.get(
                "images",
                []
            ),
            "score": score
        })

        if len(results) >= top_k:
            break

    return results
