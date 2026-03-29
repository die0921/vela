import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch
from scripts.memory_manager import MemoryManager

FAKE_EMBED = [0.1] * 1536

@pytest.fixture
def mm(tmp_path):
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

def test_get_all(mm):
    with patch("scripts.memory_manager.embed", return_value=FAKE_EMBED):
        mm.add("memory", "记忆A", {"dimension": "memory"})
        mm.add("memory", "记忆B", {"dimension": "memory"})
        all_docs = mm.get_all()
        assert len(all_docs) == 2
        assert all("id" in d and "text" in d and "metadata" in d for d in all_docs)

def test_delete(mm):
    with patch("scripts.memory_manager.embed", return_value=FAKE_EMBED):
        mm.add("memory", "将被删除的记忆", {})
        all_docs = mm.get_all()
        assert len(all_docs) == 1
        doc_id = all_docs[0]["id"]
        mm.delete(doc_id)
        assert mm.count() == 0
