# tests/test_integration.py
import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch
from scripts.db import Database
from scripts.memory_manager import MemoryManager
from scripts.emotion_engine import EmotionEngine
from scripts.respond import ResponsePipeline
from scripts.interactions import apply_interaction
from scripts.maintenance import run_emotion_decay

FAKE_EMBED = [0.1] * 1536
ORTHOGONAL_EMBED = [(-1.0 if i % 2 == 0 else 1.0) for i in range(1536)]


@pytest.fixture
def setup(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    pid = db.create_persona("Alice", base_emotion=70, base_sadness=80, base_anger=80)
    db.save_values_profile(pid,
        core_values=["诚实", "家庭"],
        red_lines=["不会参与欺骗"],
        scenarios={}
    )
    db.init_emotion_state(pid)
    return db, pid


def test_full_chat_flow(setup):
    """Full flow: memory recall → response pipeline → emotion update."""
    db, pid = setup
    persona = db.get_persona(pid)
    values = db.get_values_profile(pid)
    state = db.get_emotion_state(pid)

    with patch("scripts.memory_manager.embed", return_value=FAKE_EMBED), \
         patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        mm = MemoryManager(persona_id=pid,
                           chroma_path=str(db.db_path).replace("test.db", "chroma"))
        mm.add("memory", "我喜欢和家人在一起", {})
        memories = mm.recall("你好吗")

        pipeline = ResponsePipeline()
        pipeline.load(persona, values, state)

    with patch("scripts.values_guard.embed", return_value=ORTHOGONAL_EMBED), \
         patch("scripts.respond.guard_check", return_value={"violates": False, "severity": 0, "reason": ""}), \
         patch("scripts.respond.chat", return_value="我很好，谢谢你问。"):
        result = pipeline.run("你好吗", memories)

    assert result["blocked"] is False
    assert result["reply"] == "我很好，谢谢你问。"

    db.save_conversation(pid, "user", "你好吗", state)
    db.save_conversation(pid, "assistant", result["reply"], state)
    history = db.get_recent_conversations(pid)
    assert len(history) == 2


def test_interaction_then_decay(setup):
    """Gameplay interaction raises emotion, then decay brings it back toward base."""
    db, pid = setup
    db.update_emotion_state(pid, instant_emotion=40, sadness=50, anger=80)

    new_state = apply_interaction(pid, "send_gift", db)
    assert new_state["instant_emotion"] > 40
    assert new_state["sadness"] > 50

    run_emotion_decay(pid, db, hours_elapsed=5)
    after_decay = db.get_emotion_state(pid)
    persona = db.get_persona(pid)
    assert after_decay["instant_emotion"] <= persona["base_emotion"]
