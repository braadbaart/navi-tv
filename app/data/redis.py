import streamlit as st

from langchain.memory import RedisChatMessageHistory
from langchain.schema import messages_to_dict

def get_chat_history():
    return RedisChatMessageHistory(
        session_id=st.session_state.user_data['username'],
        url=f'redis://{st.secrets["redis"]["host"]}:{st.secrets["redis"]["port"]}/1',
        key_prefix=':conv'
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
