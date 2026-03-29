import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch
from scripts.memory_manager import MemoryManager

FAKE_EMBED = [0.1] * 1536

@pytest.fixture
def mm(tmp_path):
    with patch("scripts.memory_manager.embed", return_value=FAKE_EMBED):
        return MemoryManager(persona_id=1, chroma_path=str(tmp_path / "chroma"))

def test_add_and_recall(mm):
    with patch("scripts.memory_manager.embed", return_value=FAKE_EMBED):
        mm.add("memory", "我小时候住在农村", {"dimension": "memory"})
        results = mm.recall("农村生活")
        assert len(results) >= 1
        assert "农村" in results[0]["text"]

def test_count(mm):
    with patch("scripts.memory_manager.embed", return_value=FAKE_EMBED):
        mm.add("memory", "第一条记忆", {})
        mm.add("memory", "第二条记忆", {})
        assert mm.count() == 2
