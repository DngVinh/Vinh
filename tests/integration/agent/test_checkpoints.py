from __future__ import annotations

from pathlib import Path
import sys
import pytest
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.state import AgentState, NormalizedTurn, Route, Terminal
from campus247.infrastructure.agent.checkpoints import AgentCheckpoint, AgentCheckpointer


@pytest.fixture
def db_conn():
    engine = create_engine("sqlite:///:memory:", echo=False)
    with engine.connect() as conn:
        yield conn


def test_save_and_retrieve_checkpoint(db_conn) -> None:
    checkpointer = AgentCheckpointer(db_conn)
    checkpointer.init_schema()

    thread_id = "thread_001"
    turn = NormalizedTurn(session_id=thread_id, turn_id="turn_1", user_id="u1", query="Học phí?")
    state = AgentState(request=turn, route=Route.GROUNDED_FAQ, terminal=Terminal.ANSWERED)

    checkpointer.save(thread_id=thread_id, step=1, state=state)

    latest = checkpointer.get_latest(thread_id=thread_id)
    assert latest is not None
    assert isinstance(latest, AgentCheckpoint)
    assert latest.thread_id == thread_id
    assert latest.step == 1
    assert "Học phí?" in latest.state_json


def test_get_nonexistent_checkpoint_returns_none(db_conn) -> None:
    checkpointer = AgentCheckpointer(db_conn)
    checkpointer.init_schema()
    assert checkpointer.get_latest("thread_non_existent") is None
