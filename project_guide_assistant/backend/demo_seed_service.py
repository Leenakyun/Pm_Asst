import os
from pathlib import Path
from datetime import datetime

from backend.storage import (
    load_jsonl,
    overwrite_jsonl
)


# =========================================================
# 프로젝트 경로
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
)

GUIDE_DIR = (
    DATA_DIR
    / "guides"
)

GUIDE_FILE_DIR = (
    GUIDE_DIR
    / "files"
)

GUIDE_REGISTRY = (
    GUIDE_DIR
    / "guides.jsonl"
)

FAQ_FILE = (
    DATA_DIR
    / "faqs"
    / "faqs.jsonl"
)

SEARCH_LOG_FILE = (
    DATA_DIR
    / "search_logs"
    / "search_logs.jsonl"
)

INQUIRY_FILE = (
    DATA_DIR
    / "pm_inquiries"
    / "pm_inquiries.jsonl"
)

ANSWER_FILE = (
    DATA_DIR
    / "pm_answers"
    / "pm_answers.jsonl"
)


# =========================================================
# Demo Seed 활성 여부
# =========================================================

def is_demo_seed_enabled():

    value = os.getenv(
        "DEMO_SEED_ENABLED",
        "true"
    )

    return (
        value
        .strip()
        .lower()
        in [
            "1",
            "true",
            "yes",
            "on"
        ]
    )


# =========================================================
# 기존 운영 데이터 존재 여부
# =========================================================

def has_existing_data():

    data_files = [
        GUIDE_REGISTRY,
        FAQ_FILE,
        SEARCH_LOG_FILE,
        INQUIRY_FILE,
        ANSWER_FILE
    ]

    for file_path in data_files:

        try:

            rows = load_jsonl(
                file_path
            )

            if rows:
                return True

        except Exception:
            pass

    return False


# =========================================================
# Demo Guide
# =========================================================

def create_demo_guide():

    GUIDE_FILE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    guide_file = (
        GUIDE_FILE_DIR
        / "demo_guide.txt"
    )


    guide_text = """
[1. 객체 생성 기준]

객체의 위치와 형태를 판단할 수 있는 경우 객체를 생성합니다.
대상 객체의 특징을 확인할 수 없는 경우 무리하게 생성하지 않습니다.


[2. 가림 객체 처리 기준]

다른 객체에 일부 가려져 있더라도 대상의 위치와 형태를 판단할 수 있다면 작업합니다.

대부분이 가려져 객체의 형태를 판단하기 어려운 경우 작업하지 않습니다.


[3. 큐보이드 방향]

큐보이드의 방향은 차량의 실제 진행 방향과 차체 방향을 기준으로 설정합니다.

단순히 LiDAR 포인트가 많이 분포한 방향만을 기준으로 설정하지 않습니다.


[4. 포인트가 적은 객체]

LiDAR 포인트가 적더라도 객체의 위치와 형태를 판단할 수 있다면 작업할 수 있습니다.

포인트가 지나치게 부족하여 객체의 크기와 방향을 추정하기 어려운 경우 작업하지 않습니다.


[5. 반복 오류]

동일한 오류가 반복될 경우 임의로 판단하지 말고 가이드를 다시 확인합니다.

가이드만으로 판단하기 어려운 경우 관리자에게 문의합니다.
""".strip()


    guide_file.write_text(
        guide_text,
        encoding="utf-8"
    )


    guide_data = [
        {
            "guide_id":
                "demo-guide-001",

            "version":
                "Demo v1.0",

            "file_name":
                "demo_guide.txt",

            "file_path":
                str(
                    guide_file
                ),

            "uploaded_at":
                "2026-10-04T09:00:00",

            "is_active":
                True
        }
    ]


    overwrite_jsonl(
        GUIDE_REGISTRY,
        guide_data
    )


# =========================================================
# Demo FAQ
# =========================================================

def create_demo_faqs():

    faqs = [

        {
            "faq_id":
                "demo-faq-001",

            "question":
                "포인트가 적은 차량도 작업해야 하나요?",

            "answer":
                (
                    "포인트가 적더라도 차량의 위치와 "
                    "형태를 판단할 수 있다면 작업합니다. "
                    "크기와 방향을 판단하기 어려울 정도로 "
                    "포인트가 부족하다면 작업하지 않습니다."
                ),

            "created_at":
                "2026-10-04T10:00:00",

            "guide_version":
                "Demo v1.0",

            "source_type":
                "analytics_candidate",

            "source_question":
                "포인트가 적은 차량도 작업해야 하나요?",

            "images":
                [],

            "is_active":
                True
        },

        {
            "faq_id":
                "demo-faq-002",

            "question":
                "가려진 차량도 작업 대상인가요?",

            "answer":
                (
                    "일부가 가려졌더라도 차량의 위치와 "
                    "형태를 판단할 수 있다면 작업합니다. "
                    "대부분이 가려져 형태를 판단할 수 없다면 "
                    "작업하지 않습니다."
                ),

            "created_at":
                "2026-10-04T10:05:00",

            "guide_version":
                "Demo v1.0",

            "source_type":
                "analytics_candidate",

            "source_question":
                "가려진 차량도 작업 대상인가요?",

            "images":
                [],

            "is_active":
                True
        }

    ]


    overwrite_jsonl(
        FAQ_FILE,
        faqs
    )


# =========================================================
# Demo 검색 로그
# =========================================================

def create_demo_search_logs():

    logs = [

        # -------------------------------------------------
        # 포인트 부족 질문군
        # 검색 3 / PM 문의 1
        # -------------------------------------------------

        {
            "search_id":
                "demo-search-001",

            "worker_id":
                "worker_001",

            "worker_name":
                "김작업",

            "question":
                "포인트가 적은 차량도 작업해야 하나요?",

            "searched_at":
                "2026-10-04T13:00:00",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0",

            "result_count":
                2,

            "guide_result_count":
                1,

            "faq_result_count":
                1,

            "top_score":
                0.82,

            "result_sources":
                [
                    "demo_guide.txt"
                ],

            "faq_ids":
                [
                    "demo-faq-001"
                ]
        },

        {
            "search_id":
                "demo-search-002",

            "worker_id":
                "worker_002",

            "worker_name":
                "박작업",

            "question":
                "포인트 적은 차도 객체 생성하나요?",

            "searched_at":
                "2026-10-04T13:10:00",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0",

            "result_count":
                2,

            "guide_result_count":
                1,

            "faq_result_count":
                1,

            "top_score":
                0.74,

            "result_sources":
                [
                    "demo_guide.txt"
                ],

            "faq_ids":
                [
                    "demo-faq-001"
                ]
        },

        {
            "search_id":
                "demo-search-003",

            "worker_id":
                "worker_003",

            "worker_name":
                "이작업",

            "question":
                "점이 별로 없는 차량도 작업 대상인가요?",

            "searched_at":
                "2026-10-04T13:20:00",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0",

            "result_count":
                1,

            "guide_result_count":
                1,

            "faq_result_count":
                0,

            "top_score":
                0.51,

            "result_sources":
                [
                    "demo_guide.txt"
                ],

            "faq_ids":
                []
        },


        # -------------------------------------------------
        # 가림 질문군
        # -------------------------------------------------

        {
            "search_id":
                "demo-search-004",

            "worker_id":
                "worker_001",

            "worker_name":
                "김작업",

            "question":
                "가려진 차량도 작업하나요?",

            "searched_at":
                "2026-10-04T14:00:00",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0",

            "result_count":
                2,

            "guide_result_count":
                1,

            "faq_result_count":
                1,

            "top_score":
                0.78,

            "result_sources":
                [
                    "demo_guide.txt"
                ],

            "faq_ids":
                [
                    "demo-faq-002"
                ]
        },

        {
            "search_id":
                "demo-search-005",

            "worker_id":
                "worker_002",

            "worker_name":
                "박작업",

            "question":
                "가림이 있는 차도 작업 대상인가요?",

            "searched_at":
                "2026-10-04T14:10:00",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0",

            "result_count":
                2,

            "guide_result_count":
                1,

            "faq_result_count":
                1,

            "top_score":
                0.71,

            "result_sources":
                [
                    "demo_guide.txt"
                ],

            "faq_ids":
                [
                    "demo-faq-002"
                ]
        },


        # -------------------------------------------------
        # 큐보이드 방향 질문군
        # -------------------------------------------------

        {
            "search_id":
                "demo-search-006",

            "worker_id":
                "worker_003",

            "worker_name":
                "이작업",

            "question":
                "큐보이드 방향은 어떻게 잡나요?",

            "searched_at":
                "2026-10-04T15:00:00",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0",

            "result_count":
                1,

            "guide_result_count":
                1,

            "faq_result_count":
                0,

            "top_score":
                0.62,

            "result_sources":
                [
                    "demo_guide.txt"
                ],

            "faq_ids":
                []
        },

        {
            "search_id":
                "demo-search-007",

            "worker_id":
                "worker_001",

            "worker_name":
                "김작업",

            "question":
                "큐보이드 방향 기준이 뭐예요?",

            "searched_at":
                "2026-10-04T15:10:00",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0",

            "result_count":
                1,

            "guide_result_count":
                1,

            "faq_result_count":
                0,

            "top_score":
                0.57,

            "result_sources":
                [
                    "demo_guide.txt"
                ],

            "faq_ids":
                []
        }

    ]


    overwrite_jsonl(
        SEARCH_LOG_FILE,
        logs
    )


# =========================================================
# Demo 문의
# =========================================================

def create_demo_inquiries():

    inquiries = [

        {
            "inquiry_id":
                "demo-inquiry-001",

            "worker_id":
                "worker_003",

            "worker_name":
                "이작업",

            "question":
                (
                    "포인트가 적은 차량인데 "
                    "형태가 조금 보이는 경우도 "
                    "작업해야 하나요?"
                ),

            "created_at":
                "2026-10-04T13:22:00",

            "status":
                "waiting",

            "worker_images":
                [],

            "search_results":
                [],

            "faq_results":
                [],

            "search_id":
                "demo-search-003",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0"
        },

        {
            "inquiry_id":
                "demo-inquiry-002",

            "worker_id":
                "worker_001",

            "worker_name":
                "김작업",

            "question":
                (
                    "차량 진행 방향과 포인트 분포 방향이 "
                    "다를 때 어떤 방향으로 잡아야 하나요?"
                ),

            "created_at":
                "2026-10-04T15:12:00",

            "status":
                "waiting",

            "worker_images":
                [],

            "search_results":
                [],

            "faq_results":
                [],

            "search_id":
                "demo-search-007",

            "guide_id":
                "demo-guide-001",

            "guide_version":
                "Demo v1.0"
        }

    ]


    overwrite_jsonl(
        INQUIRY_FILE,
        inquiries
    )


# =========================================================
# Demo PM 답변
# =========================================================

def create_demo_answers():

    answers = [

        {
            "inquiry_id":
                "demo-inquiry-001",

            "pm_answer":
                (
                    "포인트가 적더라도 차량의 전체적인 "
                    "위치와 형태를 판단할 수 있으면 작업합니다. "
                    "방향이나 크기를 판단하기 어렵다면 "
                    "작업하지 않는 것이 기준입니다."
                ),

            "answered_at":
                "2026-10-04T13:30:00",

            "status":
                "answered",

            "category":
                "포인트 부족",

            "pm_images":
                []
        }

    ]


    overwrite_jsonl(
        ANSWER_FILE,
        answers
    )


# =========================================================
# 전체 Demo Seed
# =========================================================

def ensure_demo_seed_data():
    """
    DEMO_SEED_ENABLED=true 이고
    기존 데이터가 전혀 없을 때만
    시연용 데이터를 자동 생성한다.
    """

    if not is_demo_seed_enabled():
        return False


    if has_existing_data():
        return False


    create_demo_guide()

    create_demo_faqs()

    create_demo_search_logs()

    create_demo_inquiries()

    create_demo_answers()


    return True