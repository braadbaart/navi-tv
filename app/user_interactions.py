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


def resolve_news_article_subject(mental_energy, fitness_level, motion_state):
    if mental_energy == 'depleted':
        return 'politics'
    elif mental_energy == 'fully charged':
        return 'music'
    elif fitness_level == 'tired':
        return 'health'
    elif fitness_level == 'ready to go':
        return 'sports'
    elif motion_state == 'still':
        return 'entertainment'
    elif motion_state == 'moving':
        return 'technology'
    else:
        return 'business'
