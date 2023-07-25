import os
import streamlit as st
import googleapiclient.discovery
import googleapiclient.errors

from google.oauth2 import service_account
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain

from app.user_interactions import mood_matrix
from app.data.recommendations import basic_recommendation_search


file_path = os.path.dirname(__file__)


@st.cache_resource
def build_youtube_api():
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    absolute_path = os.path.dirname(__file__)
    client_secrets_file = os.path.join(absolute_path, "../../.streamlit/youtube-api.json")
    credentials = service_account.Credentials.from_service_account_file(client_secrets_file, scopes=scopes)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)


youtube = build_youtube_api()


@st.cache_data
def search_youtube(generated_query):
    query = generated_query.split('\n')[-1].replace('For example:', '') \
        if len(generated_query.split('\n')) > 0 else generated_query
    request = youtube.search().list(
        part="snippet",
        maxResults=5,
        q=query
    )
    return request.execute().get('items')


@st.cache_data
def generate_youtube_query(_llm, _memory, user_data, text):
    last_item = st.session_state.last_recommended_item if 'last_recommended_item' in st.session_state.keys() else ''
    youtube_query_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template_file(
            template_file=os.path.join(file_path, '../prompts/content/youtube.yaml'),
            input_variables=[
                'style', 'target_mood', 'mental_energy', 'fitness_level',
                'motion_state', 'current_video'
            ]
        ).format(
            style=user_data['conversational_style'],
            target_mood=mood_matrix.get(user_data['target_mood']),
            mental_energy=user_data['mental_energy'],
            fitness_level=user_data['fitness_level'],
            motion_state=user_data['motion_state'],
            current_video=last_item
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    youtube_chatrecs = ConversationChain(memory=_memory, prompt=youtube_query_prompt, llm=_llm)
    return youtube_chatrecs.predict(input=text)


def parse_youtube_video_search_results(youtube_search_results, similar_videos=None):
    content_items = []
    for res in youtube_search_results:
        if res['id']['kind'] == 'youtube#video':
            content_items.append({
                'channel': 'youtube',
                'content_type': 'video',
                'content_id': res['id']['videoId'],
                'creator': res['snippet']['channelTitle'],
                'content_source': res['snippet']['thumbnails']['default']['url'],
                'content_title': res['snippet']['title'],
                'content_description': res['snippet']['description'],
                'upload_date': res['snippet']['publishedAt']
            })
    return content_items


def recommend_from_youtube(llm, memory, user_data, query_text, weaviate_client):
    youtube_search_query = generate_youtube_query(llm, memory, user_data, query_text)
    st.write(youtube_search_query)
    youtube_videos = search_youtube(youtube_search_query)
    similar_videos = basic_recommendation_search(
        weaviate_client, user_data['username'], 'youtube', youtube_search_query)
    return parse_youtube_video_search_results(youtube_videos)
