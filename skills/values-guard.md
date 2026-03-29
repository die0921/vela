# Values Guard

Run the three-layer values check before generating a reply.

Layer 1 runs automatically inside `respond.py`.
Layer 2 (AI guard) runs automatically inside `respond.py`.

To check manually:
```bash
python -c "
from scripts.db import Database
from scripts.values_guard import ValuesGuard
from scripts.ai_client import guard_check
db = Database()
vp = db.get_values_profile(PERSONA_ID)
guard = ValuesGuard()
guard.load_profile(vp)
result = guard.check('USER_MESSAGE')
print(result)
"
```
