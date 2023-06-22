import os
import json
import redis
import streamlit as st

from datetime import datetime as dt


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

from app.content.youtube import build_youtube_api, search_youtube, parse_youtube_video_search_results


file_path = os.path.dirname(__file__)
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
    'anger': 'surprised',
    'joy': 'excited',
    'fear': 'sad',
    'sadness': 'happy',
    'love': 'surprised'
}


@st.cache_data
def get_youtube_recommendation_memory(user):
    user_conversation_memory = ConversationBufferWindowMemory(return_messages=True, k=4)
    return user_conversation_memory


llm = ChatOpenAI(openai_api_key=st.secrets['llms']['openai_api_key'], temperature=0.7)
youtube_recommendations = get_youtube_recommendation_memory(username)


youtube = build_youtube_api()
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


@st.cache_data
def generate_youtube_query(style_, mood_, energy_, fitness_, motion_, interests_, text):
    previous_video = st.session_state.last_youtube_video if 'last_youtube_video' in st.session_state.keys() else ''
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
            current_video=previous_video
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    youtube_chatrecs = ConversationChain(memory=youtube_recommendations, prompt=youtube_query_prompt, llm=llm)
    return youtube_chatrecs.predict(input=text)


user_content_history = get_user_content_history_titles(username)
query_text = conversation_ending if 'user_feedback' not in st.session_state.keys() else st.session_state.user_feedback
youtube_search_query = generate_youtube_query(
   style, current_mood, mental_energy, fitness_level, motion_state, user_content_history, query_text
)
st.write(youtube_search_query)
youtube_videos = search_youtube(youtube_search_query)
st.session_state.recommended_videos = parse_youtube_video_search_results(youtube_videos)


def load_next_content_item():
    if 'recommended_videos' in st.session_state:
        if len(st.session_state.recommended_videos) > 0:
            st.session_state.content_item = st.session_state.recommended_videos.pop()
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
                    'content_id': st.session_state.content_item['content_id'],
                    'content_metadata': {
                        'type': 'youtube_video',
                        'title': st.session_state.content_item['title'],
                        'creator': st.session_state.content_item['creator'],
                        'upload_date': st.session_state.content_item['upload_date']
                    },
                    'engagement': {
                        'clicked_on_item': st.session_state.clicked_on_item
                    },
                    'user_datetime': dt.now().strftime('%Y-%m-%dT%H:%M:%S')
                })
            )
            st.video(f'https://www.youtube.com/watch?v={st.session_state.content_item["content_id"]}')
            st.session_state.last_youtube_video = st.session_state.content_item['title']


if len(st.session_state.recommended_videos) > 0:
    st.session_state.content_item = st.session_state.recommended_videos.pop()
    st.session_state.last_youtube_video = st.session_state.content_item['title']
    youtube_recommendations.chat_memory.add_ai_message(st.session_state.content_item['title'])
    st.video(f'https://www.youtube.com/watch?v={st.session_state.content_item["content_id"]}')
    st.session_state.interaction_start_time = dt.now().timestamp()
    if st.button('Watched', on_click=load_next_content_item):
        st.session_state.clicked_on_item = True
    else:
        st.session_state.clicked_on_item = False
    st.button('Next item', on_click=load_next_content_item)
    st.text_input('Change the tune: ', value='', key='user_feedback', on_change=load_next_content_item)
    if 'user_feedback' in st.session_state.keys():
        youtube_recommendations.chat_memory.add_user_message(st.session_state.user_feedback)
else:
    st.button('Refresh', on_click=load_next_content_item)

st.write(st.session_state)
