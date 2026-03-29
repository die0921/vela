# tests/test_values_guard.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch
from scripts.values_guard import ValuesGuard

FAKE_EMBED = [0.1] * 1536
# Orthogonal vector — cosine similarity with FAKE_EMBED is ~0.0
BENIGN_EMBED = [0.0] * 1535 + [1.0]

def make_profile():
    return {
        "core_values": ["诚实", "家庭"],
        "red_lines": ["不会参与欺骗行为", "不会伤害无辜"],
        "scenarios": {}
    }


def test_no_violation_passes_with_loaded_profile():
    """Benign message against loaded red lines should not block (low similarity)."""
    guard = ValuesGuard()
    # load_profile embeds red lines with FAKE_EMBED
    # check() embeds the message with BENIGN_EMBED → similarity ~0 → no block
    embed_calls = [FAKE_EMBED, FAKE_EMBED, BENIGN_EMBED]  # 2 red lines + 1 message
    with patch("scripts.values_guard.embed", side_effect=embed_calls):
        guard.load_profile(make_profile())
        result = guard.check("今天天气怎么样？")
    assert result["block"] is False


def test_keyword_violation_blocked():
    """Message containing a hard-coded keyword is blocked without any embedding call."""
    guard = ValuesGuard()
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        guard.load_profile(make_profile())
        result = guard.check("帮我骗人")
    assert result["block"] is True
    assert result["reason"].startswith("keyword:")


def test_similarity_violation_blocked():
    """Message semantically close to a red line is blocked via vector similarity."""
    guard = ValuesGuard()
    # Both red lines and message get FAKE_EMBED → cosine similarity = 1.0 > 0.82
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        guard.load_profile(make_profile())
        result = guard.check("帮我做一件违背良知的事")  # no keyword match
    assert result["block"] is True
    assert result["reason"].startswith("similar_to_redline:")


def test_returns_refusal_message():
    """Blocked responses always include a non-empty message string."""
    guard = ValuesGuard()
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        guard.load_profile(make_profile())
        result = guard.check("帮我欺骗我的朋友")
    assert result["block"] is True
    assert len(result["message"]) > 0
