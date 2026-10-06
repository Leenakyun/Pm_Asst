import json
import os
from contextlib import contextmanager


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def database_enabled() -> bool:
    return bool(DATABASE_URL)


def _import_psycopg():
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "DATABASE_URL이 설정되어 있지만 psycopg가 설치되어 있지 않습니다. "
            "requirements.txt에 psycopg[binary]가 필요합니다."
        ) from exc
    return psycopg


@contextmanager
def get_connection():
    if not database_enabled():
        raise RuntimeError("DATABASE_URL이 설정되어 있지 않습니다.")

    psycopg = _import_psycopg()
    connection = psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
    )

    try:
        yield connection
    finally:
        connection.close()


def ensure_database_schema():
    """
    기존 서비스 코드를 크게 바꾸지 않고 PostgreSQL로 이전하기 위한
    범용 JSONB 저장 테이블을 만든다.

    collection: 기존 JSONL 파일의 논리 경로
    position:   해당 collection 안에서의 순서
    payload:    기존 dict 데이터를 그대로 JSONB로 저장
    """
    if not database_enabled():
        return

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_json_records (
                    id BIGSERIAL PRIMARY KEY,
                    collection TEXT NOT NULL,
                    position BIGINT NOT NULL,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(collection, position)
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_json_records_collection
                ON app_json_records(collection, position)
                """
            )
        connection.commit()


def load_collection(collection: str) -> list[dict]:
    ensure_database_schema()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT payload
                FROM app_json_records
                WHERE collection = %s
                ORDER BY position ASC
                """,
                (collection,),
            )
            rows = cursor.fetchall()

    result = []
    for row in rows:
        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)
        result.append(payload)

    return result


def append_collection(collection: str, data: dict):
    ensure_database_schema()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            # 같은 collection에 동시에 append가 와도 position 충돌이 나지 않도록
            # transaction-level advisory lock을 잡는다.
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (collection,),
            )
            cursor.execute(
                """
                SELECT COALESCE(MAX(position), 0) + 1
                FROM app_json_records
                WHERE collection = %s
                """,
                (collection,),
            )
            next_position = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO app_json_records(collection, position, payload)
                VALUES (%s, %s, %s::jsonb)
                """,
                (
                    collection,
                    next_position,
                    json.dumps(data, ensure_ascii=False),
                ),
            )
        connection.commit()


def overwrite_collection(collection: str, rows: list[dict]):
    ensure_database_schema()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (collection,),
            )
            cursor.execute(
                "DELETE FROM app_json_records WHERE collection = %s",
                (collection,),
            )

            for position, row in enumerate(rows, start=1):
                cursor.execute(
                    """
                    INSERT INTO app_json_records(collection, position, payload)
                    VALUES (%s, %s, %s::jsonb)
                    """,
                    (
                        collection,
                        position,
                        json.dumps(row, ensure_ascii=False),
                    ),
                )
        connection.commit()


def collection_count(collection: str) -> int:
    ensure_database_schema()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM app_json_records
                WHERE collection = %s
                """,
                (collection,),
            )
            return int(cursor.fetchone()[0])
