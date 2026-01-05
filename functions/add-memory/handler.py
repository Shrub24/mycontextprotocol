import os
import json
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, field_validator
import psycopg2
from psycopg2.extras import RealDictCursor


class MemoryRequest(BaseModel):
    content: str
    source: str = "api"

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        cursor_factory=RealDictCursor,
    )


def handle(event, context):
    try:
        body = json.loads(event.body)
        request = MemoryRequest.model_validate(body)

        memory_id = str(uuid4())

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO inbox (id, content, source, processed, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        memory_id,
                        request.content,
                        request.source,
                        False,
                        datetime.utcnow(),
                    ),
                )
                conn.commit()
        finally:
            conn.close()

        return {
            "statusCode": 202,
            "body": json.dumps({"id": memory_id, "status": "accepted"}),
        }

    except ValueError as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
