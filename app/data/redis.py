import json
import streamlit as st

from langchain.memory import RedisChatMessageHistory
from langchain.schema import messages_to_dict


def get_user_content_history_titles(db, user, num_messages=100):
    content_history = db.hgetall(user)
    titles = []
    for k, v in content_history.items():
        pc = json.loads(v)
        if pc['engagement']['clicked_on_item']:
            titles.append(f'{pc["content_metadata"]["title"]} ({pc["content_metadata"]["creator"]})')
    return ' and '.join(titles[-num_messages:])


def get_chat_history():
    return RedisChatMessageHistory(
        session_id=st.session_state.username, url='redis://localhost:6379/1', key_prefix=':conv'
    ).messages


def parse_chat_message(messages):
    if len(messages) > 2:
        decoded_user_messages = [m for m in messages_to_dict(messages)]
        conversation_end = []
        for message in decoded_user_messages[-2:]:
            conversation_end.append(f'{message["type"]}: {message["data"]["content"]}')
        return ' || '.join(conversation_end)
    else:
        return '🤷'
