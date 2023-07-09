import wikipediaapi
import streamlit as st


@st.cache_resource
def build_wikipedia_client():
    return wikipediaapi.Wikipedia('en')


@st.cache_data
def search_wikipedia(wikipedia, query):
    return wikipedia.page(query)


def recommend_from_wikipedia(
        llm, memory, style, current_mood, mental_energy, fitness_level, motion_state, query_text
):
    wikipedia = build_wikipedia_client()
    results = search_wikipedia(wikipedia, query_text)
    return results.summary
