mood_matrix = {
    'anger': 'surprised',
    'joy': 'excited',
    'fear': 'sad',
    'sadness': 'happy',
    'love': 'surprised'
}

topic_matrix = {
    'anger': 'politics',
    'joy': 'music',
    'fear': 'health',
    'sad': 'sports',
    'love': 'entertainment',
    'surprised': 'technology',
    'excited': 'business',
    'happy': 'science',
    'afraid': 'travel',
}


def resolve_news_article_subject(user_data):
    if user_data['mental_energy'] == 'depleted':
        return 'politics'
    elif user_data['mental_energy'] == 'fully charged':
        return 'music'
    elif user_data['fitness_level'] == 'tired':
        return 'health'
    elif user_data['fitness_level'] == 'ready to go':
        return 'sports'
    elif 'down' in user_data['motion_state']:
        return 'entertainment'
    elif user_data['motion_state'] == 'moving':
        return 'technology'
    else:
        return 'business'
