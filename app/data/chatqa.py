import weaviate
import streamlit as st

from datetime import datetime as dt


def create_chat_schema():
    class_obj = {
        'class': 'ChatQAPair',
        'description': 'A chat between the AI and the user.',
        'moduleConfig': {
            'text2vec-openai': {
                'skip': False,
                'vectorizeClassName': False,
                'vectorizePropertyName': False
            }
        },
        'vectorizer': 'text2vec-openai',
        'properties': [
            {
                'name': 'username',
                'dataType': ['text'],
                'moduleConfig': {
                    'text2vec-openai': {
                        'skip': True,
                        'vectorizePropertyName': False,
                        'vectorizeClassName': False
                    }
                }
            },
            {
                'name': 'datetime',
                'dataType': ['text'],
                'moduleConfig': {
                    'text2vec-openai': {
                        'skip': True,
                        'vectorizePropertyName': False,
                        'vectorizeClassName': False
                    }
                }
            },
            {
                'name': 'timestamp',
                'dataType': ['int'],
                'moduleConfig': {
                    'text2vec-openai': {
                        'skip': True,
                        'vectorizePropertyName': False,
                        'vectorizeClassName': False
                    }
                }
            },
            {
                'name': 'chat',
                'dataType': ['text']
            },
        ],
        'vectorIndexType': 'hnsw',
        'vectorIndexConfig': {
            'skip': False,
            'cleanupIntervalSeconds': 300,
            'pq': {
                'enabled': False,
                'bitCompression': False,
                'segments': 0,
                'centroids': 256,
                'encoder': {
                    'type': 'kmeans',
                    'distribution': 'log-normal'
                }
            },
            'maxConnections': 64,
            'efConstruction': 128,
            'ef': -1,
            'dynamicEfMin': 100,
            'dynamicEfMax': 500,
            'dynamicEfFactor': 8,
            'vectorCacheMaxObjects': 2000000,
            'flatSearchCutoff': 40000,
            'distance': 'cosine'
        }
    }

    client = weaviate.Client(
        url=f'http://{st.secrets["weaviate"]["host"]}:{st.secrets["weaviate"]["port"]}',
        additional_headers={
            'X-OpenAI-Api-Key': st.secrets['llms']['openai_api_key']
        }
    )

    try:
        client.schema.create_class(class_obj)
    except:
        print('Weaviate schema class already exists')


def store_qa_pair(client, username, user_prompt, agent_response, user_prompt_dt):
    client.data_object.create(
         {
            'username': username,
            'chat': f'Human: {user_prompt}\nAI: {agent_response}',
            'timestamp': int(dt.now().timestamp()),
            'datetime': user_prompt_dt
         },
         'ChatQAPair'
    )


def chat_similarity_search(client, username, user_prompt, timestamp, max_distance=0.15):
    try:
        response = client.query\
            .get('ChatQAPair', ['chat', 'timestamp', 'datetime'])\
            .with_where({
                'path': ['username'],
                'operator': 'Equal',
                'valueText': username
            })\
            .with_near_text({'concepts': [user_prompt]}) \
            .with_limit(3) \
            .with_additional(['distance']) \
            .do()
        query_results = sorted(response['data']['Get']['ChatQAPair'], key=lambda x: x['timestamp'])
        if len(query_results) > 0:
            prompt_input = ''
            for chat in query_results:
                if (timestamp - chat['timestamp']) < (60 * 60 * 24 * 30) \
                        and chat['_additional']['distance'] < max_distance:
                    prompt_input += chat['chat'] + '\n'
            # make sure we don't hit the 4096 token limit for OpenAI's APIs
            if len(prompt_input) > 1000:
                return prompt_input[:1000]
            else:
                return prompt_input
        else:
            return None
    except ValueError:
        return None
