# scripts/maintenance.py
from datetime import datetime, timezone
from scripts.db import Database
from scripts.emotion_engine import EmotionEngine
from scripts.memory_manager import MemoryManager

_ENGINE = EmotionEngine()


def run_emotion_decay(persona_id: int, db: Database, hours_elapsed: float = 1.0) -> dict:
    """Hourly: decay emotion toward base values."""
    state = db.get_emotion_state(persona_id)
    persona = db.get_persona(persona_id)
    new_state = _ENGINE.time_decay(state, persona, hours_elapsed)
    db.update_emotion_state(
        persona_id,
        instant_emotion=new_state["instant_emotion"],
        sadness=new_state["sadness"],
        anger=new_state["anger"]
    )
    result = {"task": "emotion_decay", "status": "ok",
              "before": state["instant_emotion"], "after": new_state["instant_emotion"]}
    db.log_maintenance(persona_id, "emotion_decay", result)
    return result


def run_proactive_check(persona_id: int, db: Database) -> dict:
    """Hourly: if emotion is high and no recent chat, return proactive message."""
    state = db.get_emotion_state(persona_id)
    history = db.get_recent_conversations(persona_id, limit=1)
    result = {"task": "proactive_check", "status": "ok", "message": None}

    if state["instant_emotion"] >= 70 and not history:
        persona = db.get_persona(persona_id)
        result["message"] = f"[{persona['name']}] 好久没和你聊了，你最近怎么样？"

    db.log_maintenance(persona_id, "proactive_check", result)
    return result


def run_memory_consolidation(persona_id: int, db: Database) -> dict:
    """Daily: scan for near-duplicate memory chunks and remove redundancy."""
    mm = MemoryManager(persona_id=persona_id)
    all_memories = mm.get_all()
    removed = 0
    seen_ids: set[str] = set()

    for i, mem_a in enumerate(all_memories):
        if mem_a["id"] in seen_ids:
            continue
        for mem_b in all_memories[i + 1:]:
            if mem_b["id"] in seen_ids:
                continue
            if mem_a["text"].strip() == mem_b["text"].strip():
                mm.delete(mem_b["id"])
                seen_ids.add(mem_b["id"])
                removed += 1

    result = {"task": "memory_consolidation", "status": "ok",
              "total": len(all_memories), "removed": removed}
    db.log_maintenance(persona_id, "memory_consolidation", result)
    return result


def run_soul_consistency_check(persona_id: int, db: Database) -> dict:
    """Weekly: check if recent answers conflict with values profile."""
    from scripts.ai_client import chat
    values = db.get_values_profile(persona_id)
    recent_answers = db.get_answers(persona_id)[-10:]

    if not recent_answers or not values["core_values"]:
        result = {"task": "soul_check", "status": "skipped", "conflicts": []}
        db.log_maintenance(persona_id, "soul_check", result)
        return result

    answers_text = "\n".join(f"- {a['answer']}" for a in recent_answers)
    core = "、".join(values["core_values"])
    red_lines = "; ".join(values["red_lines"])

    prompt = f"""检查以下回答是否与这个人的价值观存在矛盾。

核心价值观：{core}
红线：{red_lines}

最近的回答：
{answers_text}

如果有矛盾，列出矛盾点。没有矛盾则回复"无矛盾"。"""

    check_result = chat([{"role": "user", "content": prompt}], temperature=0)
    conflicts = [] if "无矛盾" in check_result else [check_result]
    result = {"task": "soul_check", "status": "ok", "conflicts": conflicts}
    db.log_maintenance(persona_id, "soul_check", result)
    return result


def run_all(persona_id: int) -> None:
    """Entry point for scheduled cron call."""
    db = Database()
    print(f"[Maintenance] Running for persona {persona_id}")
    print(run_emotion_decay(persona_id, db))
    print(run_proactive_check(persona_id, db))


if __name__ == "__main__":
    import sys
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_all(pid)
