import os
import wikipedia
import streamlit as st

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain

from app.data.recommendations import basic_recommendation_search

file_path = os.path.dirname(__file__)


@st.cache_data
def generate_wikipedia_query(_llm, _memory, topic_, text):
    last_item = st.session_state.last_recommended_item if 'last_recommended_item' in st.session_state.keys() else ''
    wikipedia_query_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template_file(
            template_file=os.path.join(file_path, '../prompts/content/wikipedia.yaml'),
            input_variables=['topic', 'current_item']
        ).format(
            topic=topic_,
            current_item=last_item
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    wikipedia_chatrecs = ConversationChain(memory=_memory, prompt=wikipedia_query_prompt, llm=_llm)
    return wikipedia_chatrecs.predict(input=text)


@st.cache_data
def search_wikipedia(query):
    if len(query) > 300:
        query = query[:300]
    try:
        return wikipedia.search(query, results=3)
    except wikipedia.DisambiguationError:
        return []


def parse_wikipedia_search_results(search_results):
    content_items = []
    for result in search_results:
        try:
            page = wikipedia.page(result)
            content_items.append({
                'channel': 'wikipedia',
                'content_type': 'text',
                'creator': 'wikipedia',
                'upload_date': '',
                'content_source': 'wikipedia',
                'content_id': page.pageid,
                'content_title': result,
                'content_description': page.summary,
                'content_image': page.images[0] if len(page.images) > 0 else '',
                'content_url': page.url
            })
        except wikipedia.PageError or wikipedia.DisambiguationError:
            pass
    return content_items


def resolve_wikipedia_topic(user_data):
    if user_data['conversational_style'] == 'millenial':
        return 'trivia'
    elif user_data['target_mood'] == 'happy':
        return 'entertainment'
    elif user_data['mental_energy'] == 'depleted':
        return 'history'
    elif user_data['fitness_level'] == 'neutral':
        return 'science'
    elif user_data['motion_state'] == 'sitting down':
        return 'geography'
    else:
        return 'mystery'


def recommend_from_wikipedia(llm, memory, user_data, query_text, weaviate_client):
    topic = resolve_wikipedia_topic(user_data)
    wikipedia_query = generate_wikipedia_query(llm, memory, topic, query_text)
    st.write(wikipedia_query)
    search_results = search_wikipedia(wikipedia_query)
    history = basic_recommendation_search(
        weaviate_client, user_data['username'], 'wikipedia', wikipedia_query)
    return parse_wikipedia_search_results(search_results)



