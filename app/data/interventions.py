import weaviate
import streamlit as st

from datetime import datetime as dt


def create_intervention_schema():
    class_obj = {
        'class': 'Intervention',
        'description': 'A behavioural intervention by a Navi agent.',
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
                'name': 'user_data',
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
                'name': 'intervention',
                'dataType': ['text']
            },
            {
                'name': 'user_action',
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


def store_intervention_response(client, username, intervention, user_follow_up_action, intervention_dt):
    client.data_object.create(
         {
            'user_data': username,
            'intervention': intervention,
            'user_action': user_follow_up_action,
            'timestamp': int(dt.now().timestamp()),
            'datetime': intervention_dt
         },
         'Intervention'
    )


def intervention_outcome_search(client, username, intervention, timestamp, max_distance=0.15):
    try:
        response = client.query\
            .get('Intervention', ['intervention', 'timestamp', 'datetime'])\
            .with_where({
                'path': ['user_data'],
                'operator': 'Equal',
                'valueText': username
            })\
            .with_near_text({'concepts': [intervention]}) \
            .with_limit(3) \
            .with_additional(['distance']) \
            .do()
        query_results = sorted(response['data']['Get']['Intervention'], key=lambda x: x['timestamp'])
        if len(query_results) > 0:
            interventions = []
            for intervention in query_results:
                if (timestamp - intervention['timestamp']) < (60 * 60 * 24 * 30) \
                        and intervention['_additional']['distance'] < max_distance:
                    interventions.append(intervention['intervention'])
            return interventions[:1000]
        else:
            return []
    except ValueError:
        return []
