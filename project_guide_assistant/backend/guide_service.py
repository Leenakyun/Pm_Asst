import io
import re
from pathlib import Path
from typing import List, Dict

import fitz  # PyMuPDF
from docx import Document


# =========================================================
# 텍스트 정리
# =========================================================

def clean_text(text: str) -> str:
    """
    문서에서 추출한 텍스트를 검색하기 좋은 형태로 정리
    """

    text = text.replace("\u00a0", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# =========================================================
# 가이드 섹션 분리
# =========================================================

def split_into_chunks(
    text: str,
    page: int | None = None,
    source: str | None = None
) -> List[Dict]:
    """
    [1. 제목]
    본문...

    [2. 제목]
    본문...

    형식의 가이드를 섹션 단위로 분리한다.
    """

    text = clean_text(text)

    sections = re.split(
        r"(?=\[\d+\.\s*[^\]]+\])",
        text
    )

    chunks = []

    for section in sections:

        section = section.strip()

        if not section:
            continue

        chunks.append({
            "text": section,
            "page": page,
            "source": source
        })

    return chunks


# =========================================================
# PDF 읽기
# =========================================================

def read_pdf(
    file_bytes: bytes,
    file_name: str
) -> List[Dict]:
    """
    PDF 파일을 페이지별로 읽어서 검색 가능한 가이드 섹션으로 변환
    """

    pdf = fitz.open(
        stream=file_bytes,
        filetype="pdf"
    )

    chunks = []

    for page_index, page in enumerate(pdf):

        text = page.get_text("text")

        if not text.strip():
            continue

        page_chunks = split_into_chunks(
            text=text,
            page=page_index + 1,
            source=file_name
        )

        chunks.extend(
            page_chunks
        )

    return chunks


# =========================================================
# DOCX 읽기
# =========================================================

def read_docx(
    file_bytes: bytes,
    file_name: str
) -> List[Dict]:
    """
    DOCX 파일을 읽어서 검색 가능한 가이드 섹션으로 변환
    """

    document = Document(
        io.BytesIO(file_bytes)
    )

    text = "\n\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )

    return split_into_chunks(
        text=text,
        page=None,
        source=file_name
    )


# =========================================================
# TXT 읽기
# =========================================================

def read_txt(
    file_bytes: bytes,
    file_name: str
) -> List[Dict]:
    """
    TXT 파일의 인코딩을 자동으로 시도해서 읽는다.
    """

    text = None

    for encoding in [
        "utf-8",
        "cp949",
        "euc-kr"
    ]:

        try:

            text = file_bytes.decode(
                encoding
            )

            break

        except UnicodeDecodeError:

            continue


    if text is None:

        text = file_bytes.decode(
            "utf-8",
            errors="ignore"
        )


    return split_into_chunks(
        text=text,
        page=None,
        source=file_name
    )


# =========================================================
# 확장자에 따라 자동 처리
# =========================================================

def parse_guide_file(
    file_bytes: bytes,
    file_name: str
) -> List[Dict]:
    """
    PDF / DOCX / TXT를 확장자에 따라 자동 처리한다.
    """

    extension = Path(
        file_name
    ).suffix.lower()


    if extension == ".pdf":

        return read_pdf(
            file_bytes=file_bytes,
            file_name=file_name
        )


    if extension == ".docx":

        return read_docx(
            file_bytes=file_bytes,
            file_name=file_name
        )


    if extension == ".txt":

        return read_txt(
            file_bytes=file_bytes,
            file_name=file_name
        )


    raise ValueError(
        f"지원하지 않는 파일 형식입니다: {extension}"
    )


# =========================================================
# 서버에 저장된 현재 가이드 읽기
# =========================================================

def parse_saved_guide(
    file_path: str,
    original_file_name: str
) -> List[Dict]:
    """
    관리자에 의해 서버에 저장된 가이드 파일을 읽는다.

    내부 저장 파일명은 랜덤 ID일 수 있으므로
    검색 결과에는 original_file_name을 표시한다.
    """

    path = Path(
        file_path
    )

    if not path.exists():

        raise FileNotFoundError(
            "저장된 가이드 파일을 찾을 수 없습니다."
        )


    file_bytes = path.read_bytes()


    return parse_guide_file(
        file_bytes=file_bytes,
        file_name=original_file_name
    )