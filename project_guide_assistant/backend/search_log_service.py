import uuid

from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from backend.models import SearchLog
from backend.storage import (
    DATA_DIR,
    append_jsonl,
    load_jsonl
)


SEARCH_LOG_DIR = (
    DATA_DIR
    / "search_logs"
)

SEARCH_LOG_FILE = (
    SEARCH_LOG_DIR
    / "search_logs.jsonl"
)


def create_search_log(
    worker_id: str,
    worker_name: str,
    question: str,
    guide_id: str,
    guide_version: str,
    search_results: list,
    faq_results: list | None = None
):
    """
    작업자가 검색 버튼을 누를 때마다 검색 기록 1건을 저장한다.
    FAQ 결과도 함께 기록해서 실제 검색 결과 유무를 정확하게 계산한다.
    """

    search_results = search_results or []
    faq_results = faq_results or []

    search_id = (
        datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )
        + "-"
        + uuid.uuid4().hex[:6]
    )

    result_count = (
        len(search_results)
        + len(faq_results)
    )

    guide_top_score = 0.0
    faq_top_score = 0.0

    if search_results:
        guide_top_score = float(
            search_results[0].get(
                "score",
                0
            )
        )

    if faq_results:
        faq_top_score = float(
            faq_results[0].get(
                "score",
                0
            )
        )

    top_score = max(
        guide_top_score,
        faq_top_score
    )

    result_sources = []

    for result in search_results:
        source = result.get(
            "source",
            ""
        )

        if source:
            result_sources.append(
                source
            )

    log = SearchLog(
        search_id=search_id,
        worker_id=worker_id,
        worker_name=worker_name,
        question=question.strip(),
        searched_at=(
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),
        guide_id=guide_id,
        guide_version=guide_version,
        result_count=result_count,
        top_score=top_score,
        result_sources=result_sources
    )

    log_data = asdict(
        log
    )

    # 기존 SearchLog 모델과 호환하면서 FAQ 분석용 필드 추가
    log_data[
        "guide_result_count"
    ] = len(search_results)

    log_data[
        "faq_result_count"
    ] = len(faq_results)

    log_data[
        "faq_ids"
    ] = [
        faq.get("faq_id")
        for faq in faq_results
        if faq.get("faq_id")
    ]

    append_jsonl(
        SEARCH_LOG_FILE,
        log_data
    )

    return log_data


def get_all_search_logs():

    return load_jsonl(
        SEARCH_LOG_FILE
    )


def get_worker_search_logs(
    worker_id: str
):

    logs = get_all_search_logs()

    return [
        log
        for log in logs
        if log.get(
            "worker_id"
        ) == worker_id
    ]
