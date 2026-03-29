import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


def _client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("AI_API_KEY", ""),
        base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    )


def embed(text: str) -> list[float]:
    """Return embedding vector for text."""
    model = os.getenv("EMBED_MODEL", "text-embedding-3-small")
    response = _client().embeddings.create(input=text, model=model)
    return response.data[0].embedding


def chat(messages: list[dict], temperature: float = 0.7) -> str:
    """Send messages and return assistant reply text."""
    model = os.getenv("AI_MODEL", "gpt-4o")
    response = _client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


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
    import json
    try:
        return json.loads(result.strip())
    except Exception:
        return {"violates": False, "severity": 0, "reason": ""}
