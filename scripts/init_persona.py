# scripts/init_persona.py
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.db import Database
from scripts.memory_manager import MemoryManager
from scripts.questionnaire import run_questionnaire


CONSENT_MESSAGE = """
╔══════════════════════════════════════════════════════════╗
║           Digital Persona — 数字副本启用说明              ║
╠══════════════════════════════════════════════════════════╣
║  启用后，本系统将：                                        ║
║  · 在本地存储你的记忆、价值观和情绪数据                     ║
║  · 每小时后台运行情绪维护任务                              ║
║  · 每天整合记忆                                           ║
║  · 每周检查灵魂一致性                                      ║
║                                                          ║
║  所有数据保存在本地，不会上传到任何服务器。                  ║
╚══════════════════════════════════════════════════════════╝
"""


def init(name: str | None = None) -> int | None:
    print(CONSENT_MESSAGE)
    consent = input("是否启用？(yes/no): ").strip().lower()
    if consent not in ("yes", "y", "是"):
        print("已取消，未写入任何数据。")
        return None

    if not name:
        name = input("\n请输入副本的姓名: ").strip()
    if not name:
        print("姓名不能为空，已退出。")
        return None

    db = Database()
    result = run_questionnaire(persona_id=0, db=db)  # temp id=0

    persona_id: int | None = None
    try:
        # Create persona with extracted baselines
        persona_id = db.create_persona(
            name=name,
            base_emotion=result["base_emotion"],
            base_sadness=result["base_sadness"],
            base_anger=result["base_anger"]
        )

        # Re-save answers with correct persona_id (questionnaire used temp id=0)
        with sqlite3.connect(db.db_path) as conn:
            conn.execute(
                "UPDATE questionnaire_answers SET persona_id=? WHERE persona_id=0",
                (persona_id,)
            )

        # Save values profile
        db.save_values_profile(
            persona_id,
            core_values=result["core_values"],
            red_lines=result["red_lines"],
            scenarios=result["scenarios"]
        )

        # Initialize emotion state
        db.init_emotion_state(persona_id)

        # Vectorize all answers into ChromaDB
        print("\n正在向量化记忆...")
        mm = MemoryManager(persona_id=persona_id)
        answers = db.get_answers(persona_id)
        for ans in answers:
            text = f"问：{ans['question']}\n答：{ans['answer']}"
            mm.add(ans["dimension"], text, {"dimension": ans["dimension"]})

    except Exception as exc:
        # Clean up orphaned temp rows and partially created persona
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("DELETE FROM questionnaire_answers WHERE persona_id=0")
            if persona_id is not None:
                conn.execute("DELETE FROM personas WHERE id=?", (persona_id,))
        print(f"\n创建失败：{exc}")
        return None

    print(f"\n✓ 副本 [{name}] 已成功创建！(ID: {persona_id})")
    print(f"  记忆条数：{mm.count()}")
    print(f"  情绪基线：即时={result['base_emotion']} 悲伤={result['base_sadness']} 愤怒={result['base_anger']}")
    print(f"  核心价值观：{', '.join(result['core_values'])}")

    register_cron_tasks(persona_id)
    return persona_id


def register_cron_tasks(persona_id: int) -> list[dict]:
    """Print cron task definitions for manual registration via Claude Code CronCreate."""
    base = str(Path(__file__).parent.parent)
    tasks = [
        {
            "name": f"persona_{persona_id}_hourly",
            "schedule": "0 * * * *",
            "command": f"python {base}/scripts/maintenance.py {persona_id}"
        },
        {
            "name": f"persona_{persona_id}_daily",
            "schedule": "0 3 * * *",
            "command": (
                f"python -c \"import sys; sys.path.insert(0,'{base}'); "
                f"from scripts.maintenance import run_memory_consolidation; "
                f"from scripts.db import Database; run_memory_consolidation({persona_id}, Database())\""
            )
        },
        {
            "name": f"persona_{persona_id}_weekly",
            "schedule": "0 4 * * 0",
            "command": (
                f"python -c \"import sys; sys.path.insert(0,'{base}'); "
                f"from scripts.maintenance import run_soul_consistency_check; "
                f"from scripts.db import Database; run_soul_consistency_check({persona_id}, Database())\""
            )
        }
    ]
    print("\n定时任务已就绪（需在 Claude Code 中通过 CronCreate 注册）：")
    for t in tasks:
        print(f"  · {t['name']}: {t['schedule']}")
    return tasks


if __name__ == "__main__":
    name_arg = sys.argv[1] if len(sys.argv) > 1 else None
    init(name_arg)
