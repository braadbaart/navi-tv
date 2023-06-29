import streamlit as st

from newsapi import NewsApiClient


@st.cache_resource
def build_newsapi_client():
    return NewsApiClient(api_key=st.secrets['newsapi']['api_key'])


@st.cache_data
def search_newsapi(newsapi, query):
    return newsapi.get_everything(q=query, language='en', sort_by='relevancy')


def recommend_from_newsapi(
        llm, memory, user_content_history, style, current_mood, mental_energy, fitness_level, motion_state, query_text
):
    newsapi = build_newsapi_client()
    results = search_newsapi(newsapi, query_text)
    return results.get('articles', [])
