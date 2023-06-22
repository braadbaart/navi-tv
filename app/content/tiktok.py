import TikTokApi
import streamlit as st


@st.cache_resource
def build_tiktok_client():
    return TikTokApi.TikTokApi()


@st.cache_data
def search_tiktok_video(tiktok, search_term, creator):
    tiktok_videos = tiktok.search_for_hashtags(search_term, count=10)
    return [video for video in tiktok_videos if video['author']['uniqueId'] == creator]
