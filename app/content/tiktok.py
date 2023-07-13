import os
import TikTokApi
import streamlit as st

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain

from app.user_interactions import mood_matrix


file_path = os.path.dirname(__file__)


@st.cache_data
def generate_tiktok_query(_llm, _memory, style_, mood_, energy_, fitness_, motion_, text):
    last_item = st.session_state.last_recommended_item if 'last_recommended_item' in st.session_state.keys() else ''
    tiktok_query_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template_file(
            template_file=os.path.join(file_path, '../prompts/content/tiktok.yaml'),
            input_variables=[
                'style', 'target_mood', 'mental_energy', 'fitness_level',
                'motion_state', 'current_video'
            ]
        ).format(
            style=style_,
            target_mood=mood_matrix.get(mood_),
            mental_energy=energy_,
            fitness_level=fitness_,
            motion_state=motion_,
            current_video=last_item
        ),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])
    tiktok_chatrecs = ConversationChain(memory=_memory, prompt=tiktok_query_prompt, llm=_llm)
    return tiktok_chatrecs.predict(input=text)


def parse_tiktok_search_results(search_results):
    content_items = []
    for res in search_results:
        if res['id']['kind'] == 'youtube#video':
            content_items.append({
                'channel': 'tiktok',
                'content_type': 'video',
                'content_id': res['id']['videoId'],
                'title': res['snippet']['title'],
                'creator': res['snippet']['channelTitle'],
                'upload_date': res['snippet']['publishedAt']
            })
    return content_items


def recommend_from_tiktok(
        llm, memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
):
    search_query = generate_tiktok_query(
        llm, memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text)
    search_results = []
    with TikTokApi.TikTokApi() as tiktok:
        for video in tiktok.search.videos(search_query, count=10):
            search_results.append(video)
    return parse_tiktok_search_results(search_results)
