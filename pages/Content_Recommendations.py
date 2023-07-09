import os
import json
import redis
import numpy as np
import streamlit as st

from datetime import datetime as dt

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory, RedisChatMessageHistory
from langchain.schema import messages_to_dict

from app.content.youtube import recommend_from_youtube
from app.content.spotify import recommend_from_spotify
from app.content.tiktok import recommend_from_tiktok
from app.content.newsapi import recommend_from_newsapi
from app.content.wikipedia import recommend_from_wikipedia


file_path = os.path.dirname(__file__)
st.session_state.username = 'grumpy_old_fool'


@st.cache_resource
def init_userdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=0)


userdb = init_userdb_connection()


@st.cache_resource
def init_recdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=2)


recdb = init_recdb_connection()


@st.cache_resource
def init_contentdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=3)


contentdb = init_contentdb_connection()


@st.cache_data
def get_recommendation_memory(user):
    user_conversation_memory = ConversationBufferWindowMemory(return_messages=True, k=4)
    return user_conversation_memory


llm = ChatOpenAI(openai_api_key=st.secrets['llms']['openai_api_key'], temperature=0.7)
content_memory = get_recommendation_memory(st.session_state.username)


channels = ['youtube', 'spotify', 'tiktok', 'news']


def get_user_content_history_titles(user, num_messages=100):
    content_history = contentdb.hgetall(user)
    titles = []
    for k, v in content_history.items():
        pc = json.loads(v)
        if pc['engagement']['clicked_on_item']:
            titles.append(f'{pc["content_metadata"]["title"]} ({pc["content_metadata"]["creator"]})')
    return ' and '.join(titles[-num_messages:])


def get_chat_history():
    return RedisChatMessageHistory(session_id=st.session_state.username, url='redis://localhost:6379/1', key_prefix=':conv').messages


def parse_chat_message(messages):
    if len(messages) > 2:
        decoded_user_messages = [m for m in messages_to_dict(messages)]
        conversation_end = []
        for message in decoded_user_messages[-2:]:
            conversation_end.append(f'{message["type"]}: {message["data"]["content"]}')
        return ' || '.join(conversation_end)
    else:
        return '🤷'


chat_history = get_chat_history()
conversation_ending = parse_chat_message(chat_history)

mood = st.selectbox(
    'Target mood',
    ['surprised', 'sad', 'happy', 'excited', 'angry', 'afraid'],
)
current_mood = st.session_state.user_emotion if 'user_emotion' in st.session_state.keys() else mood

fitness_level = st.selectbox(
    'Fitness level',
    ['neutral', 'tired', 'ready to go']
)

mental_energy = st.selectbox(
    'Mental energy',
    ['neutral', 'depleted', 'fully charged']
)

motion_state = st.selectbox(
    'Motion state',
    ['sitting down', 'lying down', 'seated for a long time', 'just got up', 'standing', 'walking', 'running']
)

style = st.session_state.conversational_style if 'conversational_style' in st.session_state else 'exciting'


def display_content(content_item):
    if content_item['channel'] == 'youtube':
        st.video(f'https://www.youtube.com/watch?v={content_item["content_id"]}')
    elif content_item['channel'] == 'spotify':
        st.audio(f'https://open.spotify.com/track/{content_item["content_id"]}')
    elif content_item['channel'] == 'tiktok':
        st.video(f'https://www.tiktok.com/@{content_item["content_id"]}')
    elif content_item['channel'] == 'news':
        st.write(f'{content_item["content_title"]}')
        st.write(f'{content_item["content_excerpt"]}')
        st.write(f'{content_item["content_url"]}')
    else:
        st.write(f'{content_item["content_title"]}')
        st.write(f'{content_item["content_excerpt"]}')
        st.write(f'{content_item["content_url"]}')


def load_next_query_result():
    if 'recommended_items' in st.session_state:
        if len(st.session_state.recommended_items) > 0:
            clicked_on_item = \
                False if 'clicked_on_item' not in st.session_state.keys() else st.session_state.clicked_on_item
            contentdb.hset(
                st.session_state.username,
                dt.now().timestamp(),
                json.dumps({
                    'channel': st.session_state.content_item['channel'],
                    'mood': mood,
                    'fitness_level': fitness_level,
                    'context': {
                        'day_of_week': dt.now().isoweekday(),
                        'hour_of_day': dt.now().strftime('%H'),
                        'motion_state': motion_state,
                        'mental_energy': mental_energy
                    },
                    'content_id': st.session_state.content_item['content_id'],
                    'content_metadata': {
                        'source': st.session_state.content_item['channel'],
                        'title': st.session_state.content_item['title'],
                        'creator': st.session_state.content_item['creator'],
                        'upload_date': st.session_state.content_item['upload_date']
                    },
                    'engagement': {
                        'clicked_on_item': clicked_on_item
                    },
                    'user_datetime': dt.now().strftime('%Y-%m-%dT%H:%M:%S')
                })
            )
            if 'content_item' in st.session_state.keys():
                st.session_state.last_recommended_item = st.session_state.content_item['title']
            st.session_state.content_item = st.session_state.recommended_items.pop()


def resolve_query_text():
    if 'user_feedback' in st.session_state.keys():
        return st.session_state.user_feedback
    elif 'conversation_ending' in st.session_state.keys():
        return st.session_state.conversation_ending
    else:
        return ''


def run_new_query():
    if 'content_item' in st.session_state.keys():
        st.session_state.last_recommended_item = st.session_state.content_item['title']
    st.session_state.current_channel = 'youtube' #np.random.choice(channels)
    query_text = resolve_query_text()
    if st.session_state.current_channel == 'youtube':
        st.session_state.recommended_items = recommend_from_youtube(
            llm, content_memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
        )
    elif st.session_state.current_channel == 'spotify':
        st.session_state.recommended_items = recommend_from_spotify(
            llm, content_memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
        )
    elif st.session_state.current_channel == 'tiktok':
        st.session_state.recommended_items = recommend_from_tiktok(
            llm, content_memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
        )
    elif st.session_state.current_channel == 'news':
        st.session_state.recommended_items = recommend_from_newsapi(
            llm, content_memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
        )
    else:
        st.session_state.recommended_items = recommend_from_wikipedia(
            llm, content_memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
        )

    if 'recommended_items' in st.session_state and len(st.session_state.recommended_items) > 0:
        st.session_state.content_item = st.session_state.recommended_items.pop()
        clicked_on_item = \
            False if 'clicked_on_item' not in st.session_state.keys() else st.session_state.clicked_on_item
        contentdb.hset(
            st.session_state.username,
            dt.now().timestamp(),
            json.dumps({
                'channel': 'youtube',
                'mood': mood,
                'fitness_level': fitness_level,
                'context': {
                    'day_of_week': dt.now().isoweekday(),
                    'hour_of_day': dt.now().strftime('%H'),
                    'motion_state': motion_state,
                    'mental_energy': mental_energy
                },
                'content_id': st.session_state.content_item['content_id'],
                'content_metadata': {
                    'type': 'youtube_video',
                    'title': st.session_state.content_item['title'],
                    'creator': st.session_state.content_item['creator'],
                    'upload_date': st.session_state.content_item['upload_date']
                },
                'engagement': {
                    'clicked_on_item': clicked_on_item
                },
                'user_datetime': dt.now().strftime('%Y-%m-%dT%H:%M:%S')
            })
        )
        st.session_state.last_youtube_video = st.session_state.content_item['title']
        st.session_state.content_item = st.session_state.recommended_items.pop()


if 'recommended_items' in st.session_state.keys() and len(st.session_state.recommended_items) > 0:
    if 'content_item' in st.session_state.keys():
        st.session_state.last_recommended_item = st.session_state.content_item['title']
    next_recommended_content_item = st.session_state.recommended_items.pop()
    st.session_state.content_item = next_recommended_content_item
    content_memory.chat_memory.add_ai_message(next_recommended_content_item['title'])
    display_content(next_recommended_content_item)
    st.session_state.interaction_start_time = dt.now().timestamp()
    if st.button('Interacted', on_click=load_next_query_result()):
        st.session_state.clicked_on_item = True
    else:
        st.session_state.clicked_on_item = False
    st.button('Next item', on_click=load_next_query_result())
    st.text_input('Change the tune: ', value='', key='user_feedback', on_change=run_new_query)
    if 'user_feedback' in st.session_state.keys():
        content_memory.chat_memory.add_user_message(st.session_state.user_feedback)
else:
    st.button('Refresh', on_click=run_new_query)

st.write(st.session_state)
