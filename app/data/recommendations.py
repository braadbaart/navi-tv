import uuid
import hashlib
import streamlit as st

from datetime import datetime as dt

from weaviate.exceptions import ObjectAlreadyExistsException


from app.data.schema.recommendations import recommendation_objects


def create_content_recommendation_schema(client):
    try:
        client.schema.create(recommendation_objects)
    except Exception as e:
        print(f'Weaviate content recommendation schema already exists: {e}')


def create_recommendation_user(client, user_data):
    if not client.data_object.get_by_id(user_data['user_rec_id'], class_name='RecommendationUser'):
        client.data_object.create(
            uuid=user_data['user_rec_id'],
            class_name='RecommendationUser',
            data_object={'username': user_data['username']},
        )


def create_uuid_from_string(content_id):
    hex_string = hashlib.md5(content_id.encode('UTF-8')).hexdigest()
    return str(uuid.UUID(hex=hex_string))


def store_recommendation(client, user_data, content, user_action=None):
    recommendation_dt = dt.now()
    content_id = create_uuid_from_string(user_data['username'] + content['content_id'])
    try:
        if not user_action:
            client.data_object.create(
                class_name='ContentRecommendation',
                uuid=content_id,
                data_object={
                    'username': user_data['username'],
                    'channel': content['channel'],
                    'creator': content['creator'],
                    'title': content['content_title'],
                    'description': content['content_description'],
                    'user_action': 'seen',
                    'datetime': recommendation_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': int(recommendation_dt.timestamp())
                },
            )
            client.data_object.reference.add(
                from_class_name='RecommendationUser',
                from_uuid=user_data['user_rec_id'],
                from_property_name='recommendation',
                to_class_name='ContentRecommendation',
                to_uuid=content_id,
            )
        else:
            client.data_object.update(
                uuid=content_id,
                class_name='ContentRecommendation',
                data_object={
                    'user_action': user_action,
                    'datetime': recommendation_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': int(recommendation_dt.timestamp())
                }
            )
            client.data_object.reference.add(
                from_class_name='RecommendationUser',
                from_uuid=user_data['user_rec_id'],
                from_property_name=user_action,
                to_class_name='ContentRecommendation',
                to_uuid=content_id,
            )
    except ObjectAlreadyExistsException:
        client.data_object.update(
            uuid=content_id,
            class_name='ContentRecommendation',
            data_object={
                'user_action': user_action,
                'datetime': recommendation_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': int(recommendation_dt.timestamp())
            }
        )


def basic_recommendation_search(client, username, channel, search_query, max_distance=0.15):
    cleaned_query = search_query.replace(':', '').replace('"', '')
    try:
        response = client.query\
            .get('ContentRecommendation',
                 ['title', 'creator', 'description', 'user_action', 'datetime', 'timestamp'])\
            .with_where({
                'path': ['username'],
                'operator': 'Equal',
                'valueText': username
            }) \
            .with_where({
                'path': ['channel'],
                'operator': 'Equal',
                'valueText': channel
             }) \
            .with_hybrid(query=cleaned_query, alpha=max_distance) \
            .with_limit(10) \
            .do()
        st.write(response)
        if 'data' in response.keys() and response['data']['Get']['ContentRecommendation']:
            query_results = sorted(response['data']['Get']['ContentRecommendation'], key=lambda x: x['timestamp'])
            if len(query_results) > 0:
                return query_results
            else:
                return []
        else:
            return []
    except ValueError:
        return []


# def ref2vec_recommendation_search(client, userdata, search_query):
#     cleaned_query = search_query.replace(':', '')
#     try:
#         response = client.query\
#             .get({
#                 'ContentRecommendation',
#                 '
#         })
