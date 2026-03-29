# scripts/interactions.py
from scripts.emotion_engine import EmotionEngine
from scripts.db import Database

ACTIONS = {
    "share_memory":    "分享照片或回忆",
    "apologize":       "道歉",
    "share_good_news": "分享开心的事",
    "send_gift":       "送虚拟礼物",
    "do_together":     "一起做某件事",
    "align_values":    "说了契合价值观的话",
}

_ENGINE = EmotionEngine()


def apply_interaction(persona_id: int, action_type: str, db: Database) -> dict:
    """Apply an interaction action and persist new emotion state."""
    state = db.get_emotion_state(persona_id)
    new_state = _ENGINE.apply_interaction(state, action_type)
    db.update_emotion_state(
        persona_id,
        instant_emotion=new_state["instant_emotion"],
        sadness=new_state["sadness"],
        anger=new_state["anger"]
    )
    delta = {
        "instant_emotion": new_state["instant_emotion"] - state["instant_emotion"],
        "sadness": new_state["sadness"] - state["sadness"],
        "anger": new_state["anger"] - state["anger"],
    }
    db.log_interaction(persona_id, action_type, delta)
    return new_state


def list_actions() -> list[dict]:
    return [{"key": k, "label": v} for k, v in ACTIONS.items()]
