import os
import streamlit as st

import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2 import service_account

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
absolute_path = os.path.dirname(__file__)
client_secrets_file = os.path.join(absolute_path, "../.streamlit/youtube-api.json")

credentials = service_account.Credentials.from_service_account_file(client_secrets_file, scopes=scopes)
youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

# request = youtube.search().list(
#     part="snippet",
#     maxResults=1,
#     q="surfing"
# )
# response = request.execute()
#
# print(response)

st.video('https://www.youtube.com/watch?v=OFvXuyITwBI')

