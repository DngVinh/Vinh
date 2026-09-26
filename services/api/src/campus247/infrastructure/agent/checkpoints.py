from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import uuid
from sqlalchemy import Connection, text

from campus247.agent.state import AgentState


@dataclass(frozen=True)
class AgentCheckpoint:
    thread_id: str
    checkpoint_id: str
    step: int
    state_json: str
    created_at: datetime


class AgentCheckpointer:
    """PostgreSQL / SQLite persistent agent state checkpointer."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def init_schema(self) -> None:
        self._conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS agent_checkpoint (
                    checkpoint_id VARCHAR(64) PRIMARY KEY,
                    thread_id VARCHAR(64) NOT NULL,
                    step INTEGER NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )
        )
        self._conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_checkpoint_thread ON agent_checkpoint (thread_id, step)
                """
            )
        )
        self._conn.commit()

    def save(self, thread_id: str, step: int, state: AgentState) -> AgentCheckpoint:
        chk_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        payload = json.dumps(asdict(state), ensure_ascii=False, default=str)

        stmt = text(
            """
            INSERT INTO agent_checkpoint (checkpoint_id, thread_id, step, state_json, created_at)
            VALUES (:checkpoint_id, :thread_id, :step, :state_json, :created_at)
            """
        )
        self._conn.execute(
            stmt,
            {
                "checkpoint_id": chk_id,
                "thread_id": thread_id,
                "step": step,
                "state_json": payload,
                "created_at": now,
            },
        )
        self._conn.commit()

        return AgentCheckpoint(
            thread_id=thread_id,
            checkpoint_id=chk_id,
            step=step,
            state_json=payload,
            created_at=now,
        )

    def get_latest(self, thread_id: str) -> AgentCheckpoint | None:
        stmt = text(
            """
            SELECT checkpoint_id, thread_id, step, state_json, created_at
            FROM agent_checkpoint
            WHERE thread_id = :thread_id
            ORDER BY step DESC, created_at DESC
            LIMIT 1
            """
        )
        row = self._conn.execute(stmt, {"thread_id": thread_id}).fetchone()
        if not row:
            return None

        created_at = row[4]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return AgentCheckpoint(
            checkpoint_id=row[0],
            thread_id=row[1],
            step=row[2],
            state_json=row[3],
            created_at=created_at,
        )
