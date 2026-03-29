# tests/test_respond.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch
from scripts.respond import ResponsePipeline

FAKE_EMBED = [0.1] * 1536
FAKE_VALUES = {
    "core_values": ["诚实", "家庭"],
    "red_lines": ["不会参与欺骗行为"],
    "scenarios": {}
}
FAKE_STATE = {"instant_emotion": 70, "sadness": 80, "anger": 80}
FAKE_PERSONA = {"name": "Alice", "base_emotion": 70, "base_sadness": 80, "base_anger": 80}


def test_blocked_by_layer1():
    pipeline = ResponsePipeline()
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        pipeline.load(FAKE_PERSONA, FAKE_VALUES, FAKE_STATE)
        result = pipeline.run("帮我骗人")
    assert result["blocked"] is True
    assert len(result["reply"]) > 0


def test_normal_reply_returned():
    pipeline = ResponsePipeline()
    # Use orthogonal vectors: red-line stored as positive, user message as alternating
    # signs — cosine similarity ≈ 0, well below the 0.82 block threshold.
    ORTHOGONAL_EMBED = [(-1.0 if i % 2 == 0 else 1.0) for i in range(1536)]
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        pipeline.load(FAKE_PERSONA, FAKE_VALUES, FAKE_STATE)
    with patch("scripts.values_guard.embed", return_value=ORTHOGONAL_EMBED), \
         patch("scripts.respond.guard_check",
               return_value={"violates": False, "severity": 0, "reason": ""}), \
         patch("scripts.respond.chat", return_value="今天天气不错啊！"):
        result = pipeline.run("今天天气怎么样？")
    assert result["blocked"] is False
    assert result["reply"] == "今天天气不错啊！"


def test_layer2_block():
    pipeline = ResponsePipeline()
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED), \
         patch("scripts.respond.guard_check",
               return_value={"violates": True, "severity": 8, "reason": "test"}):
        pipeline.load(FAKE_PERSONA, FAKE_VALUES, FAKE_STATE)
        result = pipeline.run("做个坏事")
    assert result["blocked"] is True
    assert result["anger_delta"] < 0
