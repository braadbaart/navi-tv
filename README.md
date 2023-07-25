Navi demo web app
-----------------

Streamlit research testbed for the Navi app ML engine.

**Conversational**

- Memory
- Relevance, recency, importance (RRI) ML model

**Content**

- History
- User engagement
- RRI vector
- Device context (audio / bluetooth, device in motion, …)
- Mood - detected with pre-trained (but user fine-tuned?) ML model
- Channel selector ML model
- Prompt generation NLP models - one per channel

Architecture sketch: content recommendations

- Learn (and update) the RRI vector from conversations with the user
- Use mood, device context and user content history & engagement to select channel
- Generate prompt for channel and return list of content titles
- Use the RRI vector to filter content titles & descriptions

Use prompt tuning to improve and personalise the prompt generation NLP models.

**AI trainer**

AutoGPT capabilities to automate mundane repetitive tasks for users.
