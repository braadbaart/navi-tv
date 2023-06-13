import os
import redis
import streamlit as st

import googleapiclient.discovery
import googleapiclient.errors

from datetime import datetime as dt
from google.oauth2 import service_account

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

st.write(st.session_state)

username = 'grumpy_old_fool'

@st.cache_resource
def init_userdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=0)


userdb = init_userdb_connection()


@st.cache_resource
def init_recdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=2)


recdb = init_recdb_connection()


@st.cache_resource
def init_contentdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=3)


contentdb = init_contentdb_connection()


api_service_name = "youtube"
api_version = "v3"
absolute_path = os.path.dirname(__file__)
client_secrets_file = os.path.join(absolute_path, "../.streamlit/youtube-api.json")

credentials = service_account.Credentials.from_service_account_file(client_secrets_file, scopes=scopes)
youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

channels = ['youtube']


def get_user_content_history(user, num_messages=10):
    return contentdb.lrange(user, start=-num_messages, end=-1)



contentdb.xadd(
            username,
            {
                'channel': st.session_state.recommended_channel,
                'mood': '',
                'energy_level': '',
                'topic': '',
                'context': {
                    'hour_of_day': '',
                    'motion_state': '',
                    'mental_energy': ''
                },
                'content_id': st.session_state.content_id,
                'content_metadata': {
                    'type': 'video',
                    'duration': '10m',
                    'title': ''
                },
                'user_action': 'next',
                'engagement': {
                    'viewing_time': ''
                },
                'timestamp': dt.now().strftime('%Y-%m-%dT%H:%M:%S')
            }
        )


# request = youtube.search().list(
#     part="snippet",
#     maxResults=1,
#     q="surfing"
# )
# response = request.execute()
#
# print(response)

st.video('https://www.youtube.com/watch?v=OFvXuyITwBI')

def load_next_content_item():
    return True

st.button('Next item', on_click=load_next_content_item)
