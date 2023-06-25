import os
import streamlit as st
import googleapiclient.discovery
import googleapiclient.errors

from google.oauth2 import service_account


@st.cache_resource
def build_youtube_api():
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    absolute_path = os.path.dirname(__file__)
    client_secrets_file = os.path.join(absolute_path, "../../.streamlit/youtube-api.json")
    credentials = service_account.Credentials.from_service_account_file(client_secrets_file, scopes=scopes)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)


youtube = build_youtube_api()


@st.cache_data()
def search_youtube(generated_query):
    query = generated_query.split('\n')[-1].replace('For example:', '') \
        if len(generated_query.split('\n')) > 0 else generated_query
    request = youtube.search().list(
        part="snippet",
        maxResults=5,
        q=query
    )
    return request.execute().get('items')


def parse_youtube_video_search_results(youtube_search_results):
    content_items = []
    for res in youtube_search_results:
        if res['id']['kind'] == 'youtube#video':
            content_items.append({
                'content_type': 'youtube_video',
                'content_id': res['id']['videoId'],
                'title': res['snippet']['title'],
                'creator': res['snippet']['channelTitle'],
                'upload_date': res['snippet']['publishedAt']
            })
    return content_items
