import streamlit as st

from newsapi import NewsApiClient


@st.cache_resource
def build_newsapi_client():
    return NewsApiClient(api_key=st.secrets['newsapi']['api_key'])


@st.cache_data
def search_newsapi(newsapi, query):
    return newsapi.get_everything(q=query, language='en', sort_by='relevancy')
