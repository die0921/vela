# scripts/emotion_engine.py

INTERACTION_DELTAS: dict[str, dict[str, int]] = {
    "share_memory":    {"instant_emotion": 10},
    "apologize":       {"anger": 15},
    "share_good_news": {"instant_emotion": 15},
    "send_gift":       {"sadness": 10, "instant_emotion": 20},
    "do_together":     {"instant_emotion": 15},
    "align_values":    {"anger": 10, "instant_emotion": 5},
}

# (low, high, message) — low inclusive, high exclusive
BEHAVIOR_RULES: list[tuple[int, int, str]] = [
    (70, 101, "你现在心情很好，回复热情详细，可以主动分享想法。"),
    (40, 70,  "你现在状态正常，友好地回答。"),
    (20, 40,  "你现在心情不太好，回复简短，不主动找话题。"),
    (10, 20,  "你现在很低落，表达你不想说话，回复极简短。"),
    (0,  10,  "你现在非常低落，可以沉默，或者只回复一两个字，甚至不回应。"),
]

SADNESS_RULES: list[tuple[int, int, str]] = [
    (0,  10,  "你悲伤到了极点，语气里带着哭泣，可以沉默不回应。"),
    (10, 30,  "你很悲伤，语气消极低落。"),
]

ANGER_RULES: list[tuple[int, int, str]] = [
    (0,  10,  "你愤怒到了极点，语气暴躁，可以说出不好听的话，甚至骂人。"),
    (10, 30,  "你很生气，语气冷硬不耐烦。"),
]


def _clamp(value: float) -> int:
    return int(max(0, min(100, value)))


class EmotionEngine:
    def update(
        self,
        state: dict[str, int],
        persona: dict[str, int],
        topic_sentiment: float,
        events: list[dict],
    ) -> dict[str, int]:
        """Update emotion state after one interaction."""
        ie = state["instant_emotion"]
        sad = state["sadness"]
        ang = state["anger"]
        base = persona["base_emotion"]

        ie = ie * 0.85 + base * 0.10 + topic_sentiment * 5

        for event in events:
            if event["type"] == "negative_memory":
                sad -= 10
            elif event["type"] == "values_violation":
                severity = event.get("severity", 5)
                ang -= int(severity * 2.5)
                ie -= 5
            elif event["type"] == "fatigue":
                ie -= 3
            elif event["type"] == "ignored":
                ie -= 1

        return {
            "instant_emotion": _clamp(ie),
            "sadness": _clamp(sad),
            "anger": _clamp(ang),
        }

    def get_behavior_instruction(self, state: dict[str, int]) -> str:
        """Return natural language behavior instruction based on current state."""
        ie = state["instant_emotion"]
        sad = state["sadness"]
        ang = state["anger"]
        parts: list[str] = []

        for lo, hi, msg in BEHAVIOR_RULES:
            if lo <= ie < hi:
                parts.append(msg)
                break

        for lo, hi, msg in SADNESS_RULES:
            if lo <= sad < hi:
                parts.append(msg)
                break

        for lo, hi, msg in ANGER_RULES:
            if lo <= ang < hi:
                parts.append(msg)
                break

        return " ".join(parts) if parts else "正常回应。"

    def apply_interaction(self, state: dict[str, int], action_type: str) -> dict[str, int]:
        """Apply a gameplay interaction and return new state."""
        deltas = INTERACTION_DELTAS.get(action_type, {})
        return {
            "instant_emotion": _clamp(state["instant_emotion"] + deltas.get("instant_emotion", 0)),
            "sadness": _clamp(state["sadness"] + deltas.get("sadness", 0)),
            "anger": _clamp(state["anger"] + deltas.get("anger", 0)),
        }

    def time_decay(
        self,
        state: dict[str, int],
        persona: dict[str, int],
        hours_elapsed: float,
    ) -> dict[str, int]:
        """Natural recovery toward base_emotion over time (2 points/hour, capped at base)."""
        recovery = int(hours_elapsed * 2)
        base = persona["base_emotion"]
        new_ie = min(base, state["instant_emotion"] + recovery)
        return {
            "instant_emotion": _clamp(new_ie),
            "sadness": state["sadness"],
            "anger": state["anger"],
        }
