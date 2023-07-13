import os
import wikipediaapi
import streamlit as st

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain


file_path = os.path.dirname(__file__)


@st.cache_resource
def build_wikipedia_client():
    return wikipediaapi.Wikipedia('Navi demo', 'en')


wiki_client = build_wikipedia_client()


@st.cache_data
def generate_wikipedia_query(_llm, _memory, style_, text):
    last_item = st.session_state.last_recommended_item if 'last_recommended_item' in st.session_state.keys() else ''
    wikipedia_query_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template_file(
            template_file=os.path.join(file_path, '../prompts/content/wikipedia.yaml'),
            input_variables=[
                'style', 'target_mood', 'mental_energy', 'fitness_level',
                'motion_state', 'current_video'
            ]
        ).format(
            style=style_,
            current_item=last_item
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    wikipedia_chatrecs = ConversationChain(memory=_memory, prompt=wikipedia_query_prompt, llm=_llm)
    return wikipedia_chatrecs.predict(input=text)


def parse_wikipedia_search_results(search_results):
    content_items = []
    for result in search_results:
        content_items.append({
            'channel': 'wikipedia',
            'content_type': 'article',
            'content_id': result.pageid,
            'title': result.title,
            'creator': '',
            'upload_date': ''
        })
    return content_items


@st.cache_data
def search_wikipedia(query):
    return wiki_client.page(query)


def recommend_from_wikipedia(
        llm, memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
):
    wikipedia_query = generate_wikipedia_query(
        llm, memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
    )
    results = search_wikipedia(wikipedia_query)
    return results.summary



