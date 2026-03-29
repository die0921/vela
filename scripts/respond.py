# scripts/respond.py
from scripts.values_guard import ValuesGuard
from scripts.emotion_engine import EmotionEngine
from scripts.ai_client import chat, guard_check

_ENGINE = EmotionEngine()


def _build_system_prompt(
    persona: dict,
    values_profile: dict,
    emotion_state: dict,
    memories: list[dict],
) -> str:
    name = persona["name"]
    core_values = "、".join(values_profile.get("core_values", []))
    red_lines = "\n".join(f"- {r}" for r in values_profile.get("red_lines", []))
    ie = emotion_state["instant_emotion"]
    sad = emotion_state["sadness"]
    ang = emotion_state["anger"]

    behavior = _ENGINE.get_behavior_instruction(emotion_state)
    memory_text = "\n".join(f"- {m['text']}" for m in memories) if memories else "（暂无相关记忆）"

    return f"""你是 {name}。

【你的价值观】
核心价值：{core_values}
红线（绝对不做）：
{red_lines}

【当前情绪状态】
即时情绪：{ie}/100
悲伤程度：{sad}/100（越低越悲伤）
愤怒程度：{ang}/100（越低越愤怒）

【行为指令】
{behavior}

【相关记忆】
{memory_text}

用第一人称回答。不知道的说不知道。违背价值观的直接拒绝。保持真实自然，像一个真实的人在聊天。"""


class ResponsePipeline:
    def __init__(self) -> None:
        self._guard = ValuesGuard()
        self._persona: dict | None = None
        self._values: dict | None = None
        self._state: dict | None = None

    def load(self, persona: dict, values_profile: dict, emotion_state: dict) -> None:
        """Load persona context. Must be called before run()."""
        self._persona = persona
        self._values = values_profile
        self._state = emotion_state
        self._guard.load_profile(values_profile)

    def run(self, user_message: str, memories: list[dict] | None = None) -> dict:
        """
        Three-layer pipeline.
        Returns {"blocked": bool, "reply": str, "anger_delta": int, "topic_sentiment": float}
        """
        if self._persona is None or self._values is None or self._state is None:
            raise RuntimeError("ResponsePipeline.load() must be called before run()")
        if memories is None:
            memories = []

        # Layer 1: code-level keyword + similarity check
        l1 = self._guard.check(user_message)
        if l1["block"]:
            return {
                "blocked": True,
                "reply": l1["message"],
                "anger_delta": -20,
                "topic_sentiment": -0.5,
            }

        # Layer 2: AI values guard
        l2 = guard_check(user_message, self._values)
        if l2.get("violates"):
            severity = l2.get("severity", 5)
            anger_delta = -int(severity * 2.5)
            return {
                "blocked": True,
                "reply": "这件事违背了我的原则，我不会做。",
                "anger_delta": anger_delta,
                "topic_sentiment": -0.3,
            }

        # Layer 3: main reply with emotion-aware system prompt
        system_prompt = _build_system_prompt(
            self._persona, self._values, self._state, memories
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        reply = chat(messages)
        return {
            "blocked": False,
            "reply": reply,
            "anger_delta": 0,
            "topic_sentiment": 0.0,
        }
