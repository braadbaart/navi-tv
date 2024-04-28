import os
import json
import redis
import weaviate
import numpy as np
import streamlit as st

from datetime import datetime as dt

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory

from app.content.youtube import recommend_from_youtube
from app.content.spotify import recommend_from_spotify
from app.content.newsapi import recommend_from_newsapi
from app.content.wikipedia import recommend_from_wikipedia

from app.data.redis import get_chat_history, parse_chat_message
from app.data.recommendations import \
    create_uuid_from_string, create_content_recommendation_schema,\
    create_recommendation_user, store_recommendation

file_path = os.path.dirname(__file__)
user_data = {'username': 'ok_boomer'}
st.session_state.clicked_on_item = False
st.session_state.not_interested = False
st.session_state.change_channel = False


@st.cache_resource
def init_userdb_connection():
    return redis.StrictRedis(host=st.secrets['redis']['host'], port=st.secrets['redis']['port'], db=0)


userdb = init_userdb_connection()


@st.cache_data
def get_user_data(username, _target_mood, _fitness_level, _mental_energy, _motion_state):
    userdata = userdb.hgetall(username)
    if 'username' in userdata.keys():
        if 'user_rec_id' not in userdata.keys():
            userdata['user_rec_id'] = create_uuid_from_string(username)
            userdb.hset(username, 'user_rec_id', userdata['user_rec_id'])
    else:
        userdb.hset(username, 'username', username)
        rec_id = create_uuid_from_string(username)
        userdb.hset(username, 'user_rec_id', rec_id)
        userdata = {'username': username, 'user_rec_id': rec_id}
    if 'conversational_style' not in userdata.keys():
        userdata['conversational_style'] = 'goat crazy'
    userdata['target_mood'] = _target_mood
    userdata['fitness_level'] = _fitness_level
    userdata['mental_energy'] = _mental_energy
    userdata['motion_state'] = _motion_state
    return userdata


target_mood = st.selectbox('Target mood', ['happy', 'surprised', 'sad',  'excited', 'angry', 'afraid'],)
fitness_level = st.selectbox('Fitness level', ['neutral', 'tired', 'ready to go'])
mental_energy = st.selectbox('Mental energy', ['neutral', 'depleted', 'fully charged'])
motion_state = st.selectbox(
    'Motion state',
    ['sitting down', 'lying down', 'seated for a long time', 'just got up', 'standing', 'walking', 'running']
)

st.session_state.user_data = get_user_data(
    user_data['username'], target_mood, fitness_level, mental_energy, motion_state
)


@st.cache_resource
def init_contentdb_connection():
    return redis.StrictRedis(host=st.secrets['redis']['host'], port=st.secrets['redis']['port'], db=2)


contentdb = init_contentdb_connection()


@st.cache_resource
def init_recommendationdb_client(user_data_):
    client = weaviate.Client(
        url=f'http://{st.secrets["weaviate"]["host"]}:{st.secrets["weaviate"]["port"]}',
        additional_headers={
            'X-OpenAI-Api-Key': st.secrets['llms']['openai_api_key']
        }
    )
    create_content_recommendation_schema(client)
    create_recommendation_user(client, user_data_)
    return client


recdb= init_recommendationdb_client(st.session_state.user_data)


def log_content_interaction(user_data_, user_action=None, content=None):
    if content:
        content_metadata = {
            'type': content['content_type'],
            'title': content['content_title'],
            'creator': content['creator'],
            'upload_date': content['upload_date']
        }
        if user_action and content:
            store_recommendation(recdb, user_data_, content, user_action)
    else:
        content_metadata = {}
    contentdb.hset(
        user_data['username'],
        int(dt.now().timestamp()),
        json.dumps({
            'channel': content['channel'],
            'target_mood': user_data_['target_mood'],
            'fitness_level': user_data_['fitness_level'],
            'context': {
                'day_of_week': dt.now().isoweekday(),
                'hour_of_day': dt.now().strftime('%H'),
                'motion_state': user_data_['motion_state'],
                'mental_energy': user_data_['mental_energy']
            },
            'content_metadata': content_metadata,
            'user_action': user_action,
            'user_datetime': dt.now().strftime('%Y-%m-%dT%H:%M:%S')
        })
    )


@st.cache_data
def get_recommendation_memory(username):
    user_conversation_memory = ConversationBufferWindowMemory(return_messages=True, k=10)
    return user_conversation_memory


llm = ChatOpenAI(openai_api_key=st.secrets['llms']['openai_api_key'], temperature=0.7)
content_memory = get_recommendation_memory(st.session_state.user_data['username'])


channels = ['youtube', 'spotify', 'news', 'wikipedia']


chat_history = get_chat_history()
conversation_ending = parse_chat_message(chat_history)


def display_content(item):
    if item['channel'] == 'youtube':
        st.video(f'https://www.youtube.com/watch?v={item["content_id"]}')
    elif item['channel'] == 'spotify':
        st.image(item['content_image'])
        st.markdown(f'**__{item["content_title"]}__**' + ' by ' + item['creator']
                    + ', on \"' + item['content_source'] + '\"')
        st.audio(item['content_id'])
        st.write(item['content_url'])
    elif item['channel'] == 'news':
        st.write(f'{item["content_title"]}')
        st.write(f'{item["content_excerpt"]}')
        st.write(f'{item["content_url"]}')
    elif item['channel'] == 'wikipedia':
        st.image(item['content_image'])
        st.markdown(f'**{item["content_title"]}**')
        st.markdown(f'{item["content_excerpt"]}')
        st.write(f'{item["content_url"]}')
    else:
        st.markdown(f'**{item["content_title"]}**')
        st.markdown(f'{item["content_excerpt"]}')
        st.write(f'{item["content_url"]}')


def load_next_query_result():
    if 'recommended_items' in st.session_state.keys() and len(st.session_state.recommended_items) > 1:
        del st.session_state.recommended_items[0]
    else:
        run_new_query()


def resolve_query_text():
    query_text = ''
    if 'user_feedback' in st.session_state.keys():
        query_text = st.session_state.user_feedback
        del st.session_state.user_feedback
    elif 'conversation_ending' in st.session_state.keys():
        query_text = st.session_state.conversation_ending
        del st.session_state.conversation_ending
    return query_text


def set_channel(change_channel=False):
    if change_channel and 'current_channel' in st.session_state.keys():
        channel_options = []
        probabilities = []
        excess_probability = 0.0
        for c, p in zip(channels, [0.6, 0.3, 0.05, 0.05]):
            if c != st.session_state.current_channel:
                channel_options.append(c)
                probabilities.append(p)
            else:
                excess_probability += p
        probabilities[0] = probabilities[0] + excess_probability
        return np.random.choice(channel_options, p=probabilities)
    else:
        return np.random.choice(channels, p=[0.6, 0.3, 0.05, 0.05])


def run_new_query(change_channel=False):
    if 'user_feedback' in st.session_state.keys() and 'current_channel' in st.session_state.keys():
        current_channel = st.session_state.current_channel
    elif change_channel or 'change_channel' in st.session_state.keys() and st.session_state.change_channel:
        current_channel = set_channel(change_channel=True)
        st.session_state.current_channel = current_channel
    else:
        current_channel = np.random.choice(channels)
        st.session_state.current_channel = current_channel
    query_text = resolve_query_text()
    if current_channel == 'youtube':
        st.session_state.recommended_items = recommend_from_youtube(
            llm, content_memory, st.session_state.user_data, query_text, recdb
        )
    elif current_channel == 'spotify':
        st.session_state.recommended_items = recommend_from_spotify(
            llm, content_memory, st.session_state.user_data, query_text, recdb
        )
    elif current_channel == 'news':
        st.session_state.recommended_items = recommend_from_newsapi(
            llm, content_memory, st.session_state.user_data, query_text, recdb
        )
    elif current_channel == 'wikipedia':
        st.session_state.recommended_items = recommend_from_wikipedia(
            llm, content_memory, st.session_state.user_data, query_text, recdb
        )
    else:
        try:
            st.session_state.change_channel = True
            run_new_query(change_channel=True)
        except ValueError:
            st.session_state.clear()


if 'recommended_items' not in st.session_state.keys() or len(st.session_state.recommended_items) == 0:
    run_new_query(change_channel=True)
content_item = st.session_state.recommended_items[0]
log_content_interaction(st.session_state.user_data, user_action=None, content=content_item)
content_memory.chat_memory.add_ai_message(content_item['content_title'])
st.session_state.last_content_item = content_item['content_title']
display_content(content_item)
st.session_state.interaction_start_time = int(dt.now().timestamp())
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    if st.button('Liked', on_click=load_next_query_result):
        content_memory.chat_memory.add_user_message('liked')
        st.session_state.clicked_on_item = True
        log_content_interaction(st.session_state.user_data, 'hasLiked', content_item)
    else:
        st.session_state.clicked_on_item = False
with col2:
    if st.button('Not interested', on_click=load_next_query_result):
        content_memory.chat_memory.add_user_message('not_interested')
        st.session_state.not_interested = True
        log_content_interaction(st.session_state.user_data, 'notInterested', content_item)
    else:
        st.session_state.not_interested = False
with col3:
    if st.button('Next item', on_click=load_next_query_result):
        content_memory.chat_memory.add_user_message('next_item')
        log_content_interaction(st.session_state.user_data, 'clickedNextItem', content_item)
with col4:
    if st.button('Refresh', on_click=st.session_state.clear):
        content_memory.chat_memory.add_user_message('refresh')
        st.session_state.change_channel = True
        log_content_interaction(st.session_state.user_data, 'hasRefreshed', content_item)
    else:
        st.session_state.change_channel = False
st.text_input('Change the tune: ', value='', key='user_feedback', on_change=run_new_query)
if 'user_feedback' in st.session_state.keys() and st.session_state.user_feedback != '':
    st.write('Running new query..')
    content_memory.chat_memory.add_user_message(st.session_state.user_feedback)
    log_content_interaction(
        st.session_state.user_data, 'changedTune', content_item
    )
