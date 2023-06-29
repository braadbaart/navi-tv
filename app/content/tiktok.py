import TikTokApi
import streamlit as st


@st.cache_resource
def build_tiktok_client():
    return TikTokApi.TikTokApi()


@st.cache_data
def search_tiktok_video(tiktok, search_term, creator):
    tiktok_videos = tiktok.search_for_hashtags(search_term, count=10)
    return [video for video in tiktok_videos if video['author']['uniqueId'] == creator]


def recommend_from_tiktok(
        llm, memory, user_content_history, style, current_mood, mental_energy, fitness_level, motion_state, query_text
):
    tiktok = build_tiktok_client()
    results = search_tiktok_video(tiktok, query_text, creator='@david')
    return results
