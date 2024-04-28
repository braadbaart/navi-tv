Navi TV web app
---------------

Streamlit research testbed for an LLM-driven conversational content recommendation system.

>> **Note**: This is an unfinished research project. It is full of bugs and holes!

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

#### Development

Requires docker and a text editor.

1. Copy `.streamlint/secrets-template.toml` to `.streamlint/secrets.toml` and fill in the secrets. 
2. Copy `.streamlit/youtube-api-example-config.json` to `.streamlit/youtube-api.json` and fill in the YouTube API config.
3. Run `OPENAI_APIKEY=<your-api-key> docker-compose up -d`.

The Streamlit app should now be available at `http://localhost:8501`.

Happy hacking!
