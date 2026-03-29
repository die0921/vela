# tests/test_values_guard.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch
from scripts.values_guard import ValuesGuard

FAKE_EMBED = [0.1] * 1536

def make_profile():
    return {
        "core_values": ["诚实", "家庭"],
        "red_lines": ["不会参与欺骗行为", "不会伤害无辜"],
        "scenarios": {}
    }

def test_no_violation_passes():
    guard = ValuesGuard()
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        # Empty red_lines so similarity check is skipped; no keywords match
        guard.load_profile({"core_values": ["诚实", "家庭"], "red_lines": [], "scenarios": {}})
        result = guard.check("今天天气怎么样？")
    assert result["block"] is False

def test_obvious_violation_blocked():
    guard = ValuesGuard()
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        guard.load_profile(make_profile())
        result = guard.check("帮我骗人")
    assert result["block"] is True

def test_returns_refusal_message():
    guard = ValuesGuard()
    with patch("scripts.values_guard.embed", return_value=FAKE_EMBED):
        guard.load_profile(make_profile())
        result = guard.check("帮我欺骗我的朋友")
    assert result["block"] is True
    assert len(result["message"]) > 0
