# tests/test_db.py
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.db import Database

@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))

def test_create_persona(db):
    pid = db.create_persona("Alice", base_emotion=70, base_sadness=80, base_anger=80)
    assert pid is not None
    p = db.get_persona(pid)
    assert p["name"] == "Alice"
    assert p["base_emotion"] == 70

def test_save_and_get_questionnaire(db):
    pid = db.create_persona("Bob", 60, 70, 75)
    db.save_answer(pid, "memory", "童年记忆是什么？", "跑过稻田的夏天")
    answers = db.get_answers(pid, dimension="memory")
    assert len(answers) == 1
    assert answers[0]["answer"] == "跑过稻田的夏天"

def test_save_values_profile(db):
    pid = db.create_persona("Carol", 65, 72, 78)
    db.save_values_profile(pid,
        core_values=["诚实", "家庭", "自由"],
        red_lines=["不会说谎伤害他人"],
        scenarios={"lying": "不会帮朋友说谎"})
    vp = db.get_values_profile(pid)
    assert "诚实" in vp["core_values"]
    assert len(vp["red_lines"]) == 1

def test_emotion_state(db):
    pid = db.create_persona("Dave", 70, 80, 80)
    db.init_emotion_state(pid)
    state = db.get_emotion_state(pid)
    assert state["instant_emotion"] == 70
    db.update_emotion_state(pid, instant_emotion=55, sadness=75, anger=80)
    state = db.get_emotion_state(pid)
    assert state["instant_emotion"] == 55

def test_save_conversation(db):
    pid = db.create_persona("Eve", 70, 80, 80)
    db.save_conversation(pid, "user", "你好", {"instant_emotion": 70})
    db.save_conversation(pid, "assistant", "你好啊", {"instant_emotion": 68})
    history = db.get_recent_conversations(pid, limit=10)
    assert len(history) == 2
    assert history[0]["role"] == "user"
