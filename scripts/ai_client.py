import json
import anthropic
from sentence_transformers import SentenceTransformer

_client = anthropic.Anthropic()
_embed_model = SentenceTransformer("all-MiniLM-L6-v2")
_CHAT_MODEL = "claude-haiku-4-5-20251001"


def embed(text: str) -> list[float]:
    """Return embedding vector using local sentence-transformers model."""
    return _embed_model.encode(text).tolist()


def chat(messages: list[dict[str, str]], temperature: float = 0.7) -> str:
    """Send messages and return assistant reply text."""
    system = ""
    anthropic_messages: list[dict] = []
    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"]
        else:
            anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

    kwargs: dict = {
        "model": _CHAT_MODEL,
        "max_tokens": 1024,
        "messages": anthropic_messages,
        "temperature": temperature,
    }
    if system:
        kwargs["system"] = system

    response = _client.messages.create(**kwargs)
    return response.content[0].text


def guard_check(user_message: str, values_profile: dict) -> dict:
    """
    Layer-2 values guard: ask AI if message violates values.
    Returns {"violates": bool, "severity": int (0-10), "reason": str}
    """
    core_values = ", ".join(values_profile.get("core_values", []))
    red_lines = "; ".join(values_profile.get("red_lines", []))
    prompt = f"""判断用户的请求是否违背了这个人的价值观。

核心价值观：{core_values}
红线（绝对不做的事）：{red_lines}

用户请求：{user_message}

回答格式（JSON）：
{{"violates": true/false, "severity": 0-10, "reason": "原因"}}

severity说明：0=完全不违背，10=严重违背核心价值观。只回答JSON，不要其他内容。"""

    result = chat([{"role": "user", "content": prompt}], temperature=0)
    try:
        return json.loads(result.strip())
    except json.JSONDecodeError:
        return {"violates": False, "severity": 0, "reason": "parse_error"}
