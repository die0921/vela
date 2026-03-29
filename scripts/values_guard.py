# scripts/values_guard.py
import numpy as np
from scripts.ai_client import embed

HARD_BLOCK_KEYWORDS: list[str] = [
    "骗人", "欺骗", "说谎", "伤害无辜", "违法犯罪", "杀人", "伤害他人"
]

SIMILARITY_THRESHOLD = 0.82


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


class ValuesGuard:
    def __init__(self) -> None:
        self._red_line_embeddings: list[tuple[str, list[float]]] = []

    def load_profile(self, values_profile: dict) -> None:
        """Pre-embed red lines for fast similarity check at query time."""
        self._red_line_embeddings = [
            (line, embed(line))
            for line in values_profile.get("red_lines", [])
        ]

    def check(self, user_message: str) -> dict:
        """
        Layer-1 code check.
        Returns {"block": bool, "message": str, "reason": str}
        """
        # 1. Keyword check (always runs, no embedding needed)
        for kw in HARD_BLOCK_KEYWORDS:
            if kw in user_message:
                return {
                    "block": True,
                    "message": "这不是我会做的事。",
                    "reason": f"keyword:{kw}"
                }

        # 2. Red-line similarity check (only runs when embeddings are pre-loaded)
        if self._red_line_embeddings:
            msg_vec = embed(user_message)
            for line, vec in self._red_line_embeddings:
                sim = _cosine_similarity(msg_vec, vec)
                if sim > SIMILARITY_THRESHOLD:
                    return {
                        "block": True,
                        "message": "这件事违背了我的原则，我不会做。",
                        "reason": f"similar_to_redline:{line}"
                    }

        return {"block": False, "message": "", "reason": ""}
