# tests/test_emotion_engine.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.emotion_engine import EmotionEngine

def make_state(ie=70, sad=80, ang=80):
    return {"instant_emotion": ie, "sadness": sad, "anger": ang}

def make_persona(base_emotion=70, base_sadness=80, base_anger=80):
    return {"base_emotion": base_emotion, "base_sadness": base_sadness, "base_anger": base_anger}

def test_update_with_positive_topic():
    engine = EmotionEngine()
    state = make_state(60, 80, 80)
    new_state = engine.update(state, make_persona(), topic_sentiment=0.8, events=[])
    assert new_state["instant_emotion"] > 60

def test_values_violation_reduces_anger():
    engine = EmotionEngine()
    state = make_state(70, 80, 80)
    new_state = engine.update(state, make_persona(), topic_sentiment=0.0,
                              events=[{"type": "values_violation", "severity": 7}])
    assert new_state["anger"] < 80

def test_clamp_to_0_100():
    engine = EmotionEngine()
    state = make_state(ie=5, sad=5, ang=5)
    new_state = engine.update(state, make_persona(), topic_sentiment=-1.0,
                              events=[{"type": "values_violation", "severity": 10}])
    assert new_state["instant_emotion"] >= 0
    assert new_state["anger"] >= 0

def test_behavior_instruction_low_emotion():
    engine = EmotionEngine()
    state = make_state(ie=15, sad=80, ang=80)
    instruction = engine.get_behavior_instruction(state)
    assert "不想说话" in instruction

def test_behavior_instruction_high_emotion():
    engine = EmotionEngine()
    state = make_state(ie=85, sad=80, ang=80)
    instruction = engine.get_behavior_instruction(state)
    assert "热情" in instruction or "主动" in instruction

def test_apply_interaction_gift():
    engine = EmotionEngine()
    state = make_state(ie=50, sad=40, ang=80)
    new_state = engine.apply_interaction(state, "send_gift")
    assert new_state["instant_emotion"] > 50
    assert new_state["sadness"] > 40

def test_time_decay_moves_toward_base():
    engine = EmotionEngine()
    state = make_state(ie=40, sad=80, ang=80)
    persona = make_persona(base_emotion=70)
    new_state = engine.time_decay(state, persona, hours_elapsed=5)
    assert new_state["instant_emotion"] > 40
