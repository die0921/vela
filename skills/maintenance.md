# Maintenance

Four scheduled tasks that keep the persona healthy.

| Task | Frequency | Command |
|------|-----------|---------|
| Emotion decay | Hourly | `python scripts/maintenance.py PERSONA_ID` |
| Proactive check | Hourly | `python scripts/maintenance.py PERSONA_ID` |
| Memory consolidation | Daily | `python -c "from scripts.maintenance import run_memory_consolidation; from scripts.db import Database; run_memory_consolidation(PERSONA_ID, Database())"` |
| Soul consistency check | Weekly | `python -c "from scripts.maintenance import run_soul_consistency_check; from scripts.db import Database; run_soul_consistency_check(PERSONA_ID, Database())"` |
