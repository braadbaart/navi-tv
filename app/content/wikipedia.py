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
    return wikipedia.search(query, results=3)


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
                'content_excerpt': page.summary,
                'content_image': page.images[0] if len(page.images) > 0 else '',
                'content_url': page.url
            })
        except wikipedia.PageError:
            pass
    return content_items


def resolve_wikipedia_topic(style, current_mood, mental_energy, fitness_level, motion_state):
    if style == 'millenial':
        return 'trivia'
    elif current_mood == 'happy':
        return 'entertainment'
    elif mental_energy == 'depleted':
        return 'history'
    elif fitness_level == 'neutral':
        return 'science'
    elif motion_state == 'sitting down':
        return 'geography'
    else:
        return 'mystery'


def recommend_from_wikipedia(
        llm, memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
):
    topic = resolve_wikipedia_topic(style, current_mood, mental_energy, fitness_level, motion_state)
    wikipedia_query = generate_wikipedia_query(llm, memory, topic, query_text)
    st.write(wikipedia_query)
    search_results = search_wikipedia(wikipedia_query)
    st.write(search_results)
    return parse_wikipedia_search_results(search_results)



