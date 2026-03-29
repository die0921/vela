# Recall Memory

Retrieve relevant memories for a user message.

```bash
python -c "
from scripts.memory_manager import MemoryManager
mm = MemoryManager(persona_id=PERSONA_ID)
results = mm.recall('USER_MESSAGE', top_k=5)
for r in results:
    print(r['text'])
"
```

Return the top 5 results to include in the response prompt.
