import base64
import json
import os

from openai import OpenAI


# =========================================================
# OpenAI 설정
# =========================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

VISION_MODEL = os.getenv(
    "VISION_MODEL",
    "gpt-6-luna"
)


# =========================================================
# 사용 가능 여부
# =========================================================

def vision_available() -> bool:

    return bool(
        OPENAI_API_KEY
    )


# =========================================================
# 기본 분석 결과
# =========================================================

def empty_vision_result():

    return {
        "summary": "",
        "object_types": [],
        "occlusion": "unknown",
        "point_density": "unknown",
        "orientation_issue": False,
        "boundary_issue": False,
        "likely_topics": [],
        "search_keywords": [],
    }


# =========================================================
# MIME type
# =========================================================

def get_mime_type(
    file_name: str
) -> str:

    file_name = (
        file_name
        .lower()
    )

    if (
        file_name.endswith(".jpg")
        or
        file_name.endswith(".jpeg")
    ):

        return "image/jpeg"

    if file_name.endswith(
        ".webp"
    ):

        return "image/webp"

    return "image/png"


# =========================================================
# 이미지 bytes → data URL
# =========================================================

def image_bytes_to_data_url(
    image_bytes: bytes,
    mime_type: str
) -> str:

    encoded = (
        base64.b64encode(
            image_bytes
        )
        .decode(
            "utf-8"
        )
    )

    return (
        f"data:{mime_type};"
        f"base64,{encoded}"
    )


# =========================================================
# Vision 분석
# =========================================================

def analyze_work_images(
    images: list,
    detail: str = "low"
) -> dict:
    """
    작업 화면을 분석해서
    가이드 검색을 보조할 상황 태그를 만든다.

    최종 작업 기준을 판단하지 않는다.
    """

    if not images:

        return empty_vision_result()


    if not vision_available():

        raise ValueError(
            "OPENAI_API_KEY가 설정되어 있지 않습니다."
        )


    if detail not in [
        "low",
        "high"
    ]:

        detail = "low"


    client = OpenAI(
        api_key=OPENAI_API_KEY
    )


    content = [
        {
            "type":
                "input_text",

            "text":
                """
당신은 3D LiDAR 및 자율주행 데이터 라벨링 작업 화면을
분석하는 검색 보조 시스템입니다.

목적은 작업 기준을 직접 결정하는 것이 아니라,
이미지에 보이는 상황을 구조화하여
작업 가이드 검색을 돕는 것입니다.

규칙:
1. 최종 작업 여부를 결정하지 마세요.
2. 이미지에서 확인 가능한 내용만 작성하세요.
3. 확실하지 않은 내용은 추측하지 마세요.
4. 알 수 없는 값은 unknown 또는 빈 배열을 사용하세요.
5. likely_topics와 search_keywords는 한국어 중심으로 작성하세요.
6. JSON 이외의 설명은 출력하지 마세요.

반환 형식:

{
  "summary": "이미지 상황에 대한 짧은 한국어 설명",
  "object_types": ["차량"],
  "occlusion": "none | partial | heavy | unknown",
  "point_density": "low | medium | high | unknown",
  "orientation_issue": false,
  "boundary_issue": false,
  "likely_topics": [
    "포인트 부족",
    "큐보이드 방향"
  ],
  "search_keywords": [
    "차량",
    "포인트 부족",
    "방향"
  ]
}
""".strip()
        }
    ]


    # =====================================================
    # 이미지 추가
    # =====================================================

    for image in images:

        image_bytes = (
            image.getvalue()
        )

        mime_type = (
            get_mime_type(
                image.name
            )
        )

        data_url = (
            image_bytes_to_data_url(
                image_bytes,
                mime_type
            )
        )


        content.append({
            "type":
                "input_image",

            "image_url":
                data_url,

            "detail":
                detail,
        })


    # =====================================================
    # API
    # =====================================================

    response = (
        client.responses.create(
            model=VISION_MODEL,

            input=[
                {
                    "role":
                        "user",

                    "content":
                        content,
                }
            ],
        )
    )


    raw_text = (
        response.output_text
        .strip()
    )


    # =====================================================
    # 혹시 markdown code fence가 포함된 경우
    # =====================================================

    if raw_text.startswith(
        "```"
    ):

        raw_text = (
            raw_text
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )


    try:

        result = json.loads(
            raw_text
        )

    except json.JSONDecodeError:

        raise ValueError(
            "Vision 분석 결과를 "
            "JSON으로 해석하지 못했습니다."
        )


    final_result = (
        empty_vision_result()
    )

    final_result.update(
        result
    )


    return final_result


# =========================================================
# Vision 결과 → 검색 문자열
# =========================================================

def build_vision_search_text(
    vision_result: dict
) -> str:

    parts = []


    summary = vision_result.get(
        "summary",
        ""
    )

    if summary:

        parts.append(
            summary
        )


    for item in vision_result.get(
        "object_types",
        []
    ):

        if item:
            parts.append(
                str(item)
            )


    occlusion = vision_result.get(
        "occlusion"
    )

    if (
        occlusion
        and occlusion != "unknown"
    ):

        occlusion_map = {
            "none":
                "가림 없음",

            "partial":
                "부분 가림",

            "heavy":
                "심한 가림",
        }

        parts.append(
            occlusion_map.get(
                occlusion,
                occlusion
            )
        )


    point_density = (
        vision_result.get(
            "point_density"
        )
    )

    if (
        point_density
        and point_density != "unknown"
    ):

        point_map = {
            "low":
                "포인트 부족",

            "medium":
                "보통 포인트",

            "high":
                "포인트 많음",
        }

        parts.append(
            point_map.get(
                point_density,
                point_density
            )
        )


    if vision_result.get(
        "orientation_issue",
        False
    ):

        parts.append(
            "큐보이드 방향"
        )


    if vision_result.get(
        "boundary_issue",
        False
    ):

        parts.append(
            "객체 경계"
        )


    for item in vision_result.get(
        "likely_topics",
        []
    ):

        if item:
            parts.append(
                str(item)
            )


    for item in vision_result.get(
        "search_keywords",
        []
    ):

        if item:
            parts.append(
                str(item)
            )


    # =====================================================
    # 중복 제거
    # =====================================================

    unique_parts = []

    for item in parts:

        item = (
            str(item)
            .strip()
        )

        if (
            item
            and item not in unique_parts
        ):

            unique_parts.append(
                item
            )


    return " ".join(
        unique_parts
    )