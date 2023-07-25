import os
import streamlit as st

from datetime import datetime as dt, timedelta
from newsapi import NewsApiClient

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain

from app.user_interactions import topic_matrix, resolve_news_article_subject


file_path = os.path.dirname(__file__)


@st.cache_data
def generate_newsapi_query(_llm, _memory, user_data, text):
    last_item = st.session_state.last_recommended_item if 'last_recommended_item' in st.session_state.keys() else ''
    newsapi_query_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template_file(
            template_file=os.path.join(file_path, '../prompts/content/newsapi.yaml'),
            input_variables=['style', 'topic', 'subject', 'current_item']
        ).format(
            style=user_data['conversational_style'],
            topic=topic_matrix.get(user_data['target_mood']),
            subject=resolve_news_article_subject(user_data),
            current_item=last_item
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    news_chatrecs = ConversationChain(memory=_memory, prompt=newsapi_query_prompt, llm=_llm)
    return news_chatrecs.predict(input=text)


@st.cache_resource
def build_newsapi_client():
    return NewsApiClient(api_key=st.secrets['newsapi']['api_key'])


newsapi_client = build_newsapi_client()


@st.cache_data
def search_newsapi(query, date_range=2, max_results=10):
    earliest_date = (dt.now() - timedelta(days=date_range)).strftime('%Y-%M-%d')
    return newsapi_client.get_everything(
        q=query, language='en', from_param=earliest_date, page_size=max_results, sort_by='relevancy'
    )


def parse_newsapi_response(response, recommendation_history=None):
    return [
        {
            'channel': 'newsapi',
            'content_type': 'text',
            'creator': article['author'],
            'upload_date': article['publishedAt'],
            'content_source': article['source']['name'],
            'content_id': article['url'],
            'content_title': article['title'],
            'content_description': article['description'],
            'content_image': article['urlToImage'],
            'content_url': article['url']
        }
        for article in response['articles']
    ]


def recommend_from_newsapi(llm, memory, user_data, query_text, weaviate_client):
    topic = topic_matrix.get(user_data['target_mood'])
    if 'user_feedback' in st.session_state.keys():
        subject = st.session_state.user_feedback
    else:
        subject = resolve_news_article_subject(user_data)
    current_articles = search_newsapi(f'{topic} {subject} {query_text}')
    history = []
    return parse_newsapi_response(current_articles, recommendation_history=history)
