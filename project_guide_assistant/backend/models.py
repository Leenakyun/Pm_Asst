from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchResult:

    source: str

    text: str

    score: float

    page: Optional[int] = None


@dataclass
class Inquiry:

    inquiry_id: str

    worker_id: str

    worker_name: str

    question: str

    created_at: str

    status: str = "waiting"

    worker_images: List[str] = (
        field(
            default_factory=list
        )
    )

    search_results: List[dict] = (
        field(
            default_factory=list
        )
    )

    faq_results: List[dict] = (
        field(
            default_factory=list
        )
    )

    search_id: Optional[str] = None

    guide_id: Optional[str] = None

    guide_version: Optional[str] = None

    worker_answer_checked_at: Optional[str] = None


@dataclass
class PMAnswer:

    inquiry_id: str

    pm_answer: str

    answered_at: str

    status: str = "answered"

    category: Optional[str] = None

    pm_images: List[str] = (
        field(
            default_factory=list
        )
    )


@dataclass
class Worker:

    worker_id: str

    worker_name: str


@dataclass
class Admin:

    admin_id: str

    admin_name: str = "관리자"


@dataclass
class GuideVersion:

    guide_id: str

    version: str

    file_name: str

    file_path: str

    uploaded_at: str

    is_active: bool = False


@dataclass
class SearchLog:

    search_id: str

    worker_id: str

    worker_name: str

    question: str

    searched_at: str

    guide_id: str

    guide_version: str

    result_count: int

    top_score: float = 0.0

    result_sources: List[str] = (
        field(
            default_factory=list
        )
    )