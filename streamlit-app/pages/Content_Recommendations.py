import os
import json
import redis
import numpy as np
import streamlit as st

import googleapiclient.discovery
import googleapiclient.errors

from datetime import datetime as dt

from google.oauth2 import service_account

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory, RedisChatMessageHistory
from langchain.schema import messages_to_dict


file_path = os.path.dirname(__file__)

st.write(st.session_state)

username = 'grumpy_old_fool'


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
mood_matrix = {
    'anger': 'Surprised',
    'joy': 'Excited',
    'fear': 'Sad',
    'sadness': 'Happy',
    'love': 'Surprised'
}


@st.cache_resource
def get_youtube_recommendation_memory():
    user_conversation_memory = ConversationBufferWindowMemory(return_messages=True, k=2)
    return user_conversation_memory


llm = ChatOpenAI(openai_api_key=st.secrets['llms']['openai_api_key'], temperature=0.7)
youtube_recommendations = get_youtube_recommendation_memory()


@st.cache_resource
def build_youtube_api():
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    absolute_path = os.path.dirname(__file__)
    client_secrets_file = os.path.join(absolute_path, "../.streamlit/youtube-api.json")
    credentials = service_account.Credentials.from_service_account_file(client_secrets_file, scopes=scopes)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)


youtube = build_youtube_api()
channels = ['youtube', 'spotify', 'tiktok']


def get_user_content_history_titles(user, num_messages=100):
    content_history = contentdb.hgetall(user)
    titles = []
    for k, v in content_history.items():
        pc = json.loads(v)
        if pc['engagement']['clicked_on_item']:
            titles.append(f'{pc["content_metadata"]["title"]} ({pc["content_metadata"]["creator"]})')
    return ' and '.join(titles[-num_messages:])


def get_chat_history():
    return RedisChatMessageHistory(session_id=username, url='redis://localhost:6379/1', key_prefix=':conv').messages


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
    'Emotion',
    ['Surprised', 'Sad', 'Happy', 'Excited', 'Angry', 'Afraid'],
)
current_mood = st.session_state.user_emotion if 'user_emotion' in st.session_state.keys() else mood

fitness_level = st.selectbox(
    'Fitness level',
    ['Neutral', 'Tired', 'Ready to go']
)

mental_energy = st.selectbox(
    'Mental energy',
    ['Neutral', 'Depleted', 'Fully charged']
)

motion_state = st.selectbox(
    'Motion state',
    ['Sitting down', 'Lying down', 'Seated for a long time', 'Just got up', 'Walking', 'Running']
)

style = st.session_state.conversational_style if 'conversational_style' in st.session_state else 'exciting'


def search_youtube(generated_query):
    st.session_state.interaction_start_time = dt.now().timestamp()
    query = generated_query.split('\n')[-1].replace('For example:', '') \
        if len(generated_query.split('\n')) > 0 else generated_query
    request = youtube.search().list(
        part="snippet",
        maxResults=10,
        q=query
    )
    return request.execute().get('items')


def generate_youtube_query(style_, mood_, energy_, fitness_, motion_, interests_, conversation_ending_):
    current_video = st.session_state.current_youtube_video if 'current_youtube_video' in st.session_state.keys() else ''
    youtube_query_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template_file(
            template_file=os.path.join(file_path, '../prompts/content/youtube.yaml'),
            input_variables=[
                'style', 'target_mood', 'mental_energy', 'fitness_level',
                'motion_state', 'channel_interests', 'current_video'
            ]
        ).format(
            style=style_,
            target_mood=mood_matrix.get(mood_),
            mental_energy=energy_,
            fitness_level=fitness_,
            motion_state=motion_,
            channel_interests=interests_,
            current_video=current_video
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    youtube_chatrecs = ConversationChain(memory=youtube_recommendations, prompt=youtube_query_prompt, llm=llm)
    return youtube_chatrecs.predict(input=conversation_ending_)


def parse_youtube_video_search_results(youtube_search_results):
    content_items = []
    for res in youtube_search_results:
        if res['id']['kind'] == 'youtube#video':
            content_items.append({
                'content_id': res['id']['videoId'],
                'title': res['snippet']['title'],
                'creator': res['snippet']['channelTitle'],
                'upload_date': res['snippet']['publishedAt']
            })
    return content_items


user_content_history = get_user_content_history_titles(username)
youtube_search_query = generate_youtube_query(
   style, current_mood, mental_energy, fitness_level, motion_state, user_content_history, conversation_ending
)
st.write(youtube_search_query)
youtube_videos = search_youtube(youtube_search_query)
st.session_state.recommended_videos = parse_youtube_video_search_results(youtube_videos)


def load_next_content_item():
    if 'recommended_videos' in st.session_state:
        if len(st.session_state.recommended_videos) > 0:
            content_item = st.session_state.recommended_videos.pop()
            contentdb.hset(
                username,
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
                    'content_id': content_item['content_id'],
                    'content_metadata': {
                        'type': 'youtube_video',
                        'title': content_item['title'],
                        'creator': content_item['creator'],
                        'upload_date': content_item['upload_date']
                    },
                    'engagement': {
                        'clicked_on_item': st.session_state.clicked_on_item
                    },
                    'user_datetime': dt.now().strftime('%Y-%m-%dT%H:%M:%S')
                })
            )
            st.video(f'https://www.youtube.com/watch?v={content_item["content_id"]}')
            st.session_state.current_youtube_video = first_video['title']


if st.button('Show me!'):
    if len(st.session_state.recommended_videos) > 0:
        first_video = st.session_state.recommended_videos.pop()
        st.session_state.current_youtube_video = first_video['title']
        st.video(f'https://www.youtube.com/watch?v={first_video["content_id"]}')
        st.session_state.interaction_start_time = dt.now().timestamp()
        if st.button('Watched'):
            st.session_state.clicked_on_item = True
            load_next_content_item()
        else:
            st.session_state.clicked_on_item = False
        st.button('Next item', on_click=load_next_content_item)
    else:
        st.button('Refresh', on_click=st.experimental_rerun())
