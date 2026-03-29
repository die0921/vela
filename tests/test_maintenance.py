# tests/test_maintenance.py
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock
from scripts.db import Database
from scripts.maintenance import (
    run_emotion_decay, run_proactive_check, run_memory_consolidation
)

FAKE_EMBED = [0.1] * 1536

@pytest.fixture
def db(tmp_path):
    d = Database(str(tmp_path / "test.db"))
    pid = d.create_persona("Alice", base_emotion=70, base_sadness=80, base_anger=80)
    d.init_emotion_state(pid)
    return d, pid

def test_emotion_decay_recovers_toward_base(db):
    database, pid = db
    # Set emotion below base
    database.update_emotion_state(pid, instant_emotion=50, sadness=80, anger=80)
    run_emotion_decay(pid, database, hours_elapsed=5)
    state = database.get_emotion_state(pid)
    assert state["instant_emotion"] > 50

def test_emotion_decay_does_not_exceed_base(db):
    database, pid = db
    database.update_emotion_state(pid, instant_emotion=95, sadness=80, anger=80)
    run_emotion_decay(pid, database, hours_elapsed=10)
    state = database.get_emotion_state(pid)
    persona = database.get_persona(pid)
    assert state["instant_emotion"] <= persona["base_emotion"]

def test_memory_consolidation_runs_without_error(db):
    database, pid = db
    with patch("scripts.maintenance.MemoryManager") as MockMM:
        mock_instance = MagicMock()
        mock_instance.get_all.return_value = []
        MockMM.return_value = mock_instance
        result = run_memory_consolidation(pid, database)
    assert result["status"] == "ok"
