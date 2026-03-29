# Update Emotion

After each interaction, update the three emotion indices.

```bash
python -c "
from scripts.db import Database
from scripts.emotion_engine import EmotionEngine
db = Database()
state = db.get_emotion_state(PERSONA_ID)
persona = db.get_persona(PERSONA_ID)
engine = EmotionEngine()
new_state = engine.update(state, persona, topic_sentiment=SENTIMENT, events=EVENTS)
db.update_emotion_state(PERSONA_ID, **new_state)
print(new_state)
"
```

topic_sentiment: float -1.0 to 1.0 based on message tone.
events: list of triggered events e.g. [{"type": "values_violation", "severity": 7}]
