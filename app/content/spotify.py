import os
import spotipy
import streamlit as st

from spotipy.oauth2 import SpotifyClientCredentials

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
os.environ['SPOTIPY_CLIENT_ID'] = st.secrets['spotify']['client_id']
os.environ['SPOTIPY_CLIENT_SECRET'] = st.secrets['spotify']['client_secret']


@st.cache_resource
def build_spotify_client():
    return spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())


spotify = build_spotify_client()


@st.cache_data
def generate_spotify_query(_llm, _memory, user_data, text):
    last_item = st.session_state.last_recommended_item if 'last_recommended_item' in st.session_state.keys() else ''
    spotify_query_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template_file(
            template_file=os.path.join(file_path, '../prompts/content/spotify.yaml'),
            input_variables=[
                'style', 'target_mood', 'mental_energy', 'fitness_level',
                'motion_state', 'current_item'
            ]
        ).format(
            style=user_data['conversational_style'],
            target_mood=mood_matrix.get(user_data['target_mood']),
            mental_energy=user_data['mental_energy'],
            fitness_level=user_data['fitness_level'],
            motion_state=user_data['motion_state'],
            current_item=last_item
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    spotify_chatrecs = ConversationChain(memory=_memory, prompt=spotify_query_prompt, llm=_llm)
    return spotify_chatrecs.predict(input=text)


@st.cache_data
def search_spotify(query):
    if len(query) > 200:
        query = query[:200]
    try:
        return spotify.search(query, limit=5, type='track')
    except spotipy.exceptions.SpotifyException:
        return {'tracks': {'total': 0}}


def parse_spotify_search_results(results, recommendation_history=None):
    if results['tracks']['total'] == 0:
        return []
    else:
        tracks = []
        for track in results['tracks']['items']:
            tracks.append({
                'channel': 'spotify',
                'content_type': 'music',
                'creator': track['artists'][0]['name'],
                'upload_date': track['album']['release_date'],
                'content_source': track['album']['name'],
                'content_id': track['preview_url'],
                'content_title': track['name'],
                'content_description': track['album']['name'],
                'content_image': track['album']['images'][0]['url'],
                'content_url': track['external_urls']['spotify']
            })
        return tracks


def recommend_from_spotify(llm, memory, user_data, query_text, weaviate_client):
    spotify_query = generate_spotify_query(llm, memory, user_data, query_text)
    st.write(spotify_query)
    search_results = search_spotify(spotify_query)
    history = basic_recommendation_search(
        weaviate_client, user_data['username'], 'spotify', spotify_query)
    return parse_spotify_search_results(search_results, history)
