import weaviate
import streamlit as st

from datetime import datetime as dt


def create_content_recommendation_schema():
    class_obj = {
        'class': 'ContentRecommendation',
        'description': 'A content recommendation and user reaction.',
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
                'name': 'recommendation',
                'dataType': ['text']
            },
            {
                'name': 'user_reaction',
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


def store_recommendation_response_pair(client, username, recommendation, result, recommendation_dt):
    client.data_object.create(
         {
            'username': username,
            'recommendation': recommendation,
            'user_reaction': result,
            'timestamp': int(dt.now().timestamp()),
            'datetime': recommendation_dt
         },
         'ContentRecommendation'
    )


def recommendation_similarity_search(client, username, recommendation, timestamp, max_distance=0.15):
    try:
        response = client.query\
            .get('ContentRecommendation', ['recommendation', 'timestamp', 'datetime'])\
            .with_where({
                'path': ['username'],
                'operator': 'Equal',
                'valueText': username
            })\
            .with_near_text({'concepts': [recommendation]}) \
            .with_limit(5) \
            .with_additional(['distance']) \
            .do()
        query_results = sorted(response['data']['Get']['ContentRecommendation'], key=lambda x: x['timestamp'])
        if len(query_results) > 0:
            recommendations = []
            for rec in query_results:
                if (timestamp - rec['timestamp']) < (60 * 60 * 24 * 30) \
                        and rec['_additional']['distance'] < max_distance:
                    recommendations.append(rec['recommendation'])
            return recommendations
        else:
            return []
    except ValueError:
        return []
