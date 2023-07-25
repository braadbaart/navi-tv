chatqa_schema = {
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
