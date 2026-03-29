# Respond

Generate a persona reply using the three-layer pipeline.

```bash
python -c "
from scripts.db import Database
from scripts.memory_manager import MemoryManager
from scripts.respond import ResponsePipeline
db = Database()
persona = db.get_persona(PERSONA_ID)
values = db.get_values_profile(PERSONA_ID)
state = db.get_emotion_state(PERSONA_ID)
mm = MemoryManager(persona_id=PERSONA_ID)
memories = mm.recall('USER_MESSAGE')
pipeline = ResponsePipeline()
pipeline.load(persona, values, state)
result = pipeline.run('USER_MESSAGE', memories)
print(result)
"
```
