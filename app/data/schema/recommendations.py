recommendation_objects = {
    'classes': [
        {
            'class': 'RecommendationUser',
            'description': 'A content recommendation user.',
            'moduleConfig': {
                'ref2vec-centroid': {
                    'referenceProperties': [
                        'recommendation', 'hasLiked', 'notInterested', 'clickedNextItem', 'changedTune', 'hasRefreshed'
                    ],
                    'method': 'mean'
                },
            },
            'vectorizer': 'ref2vec-centroid',
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
                'vectorCacheMaxObjects': 20000,
                'flatSearchCutoff': 40000,
                'distance': 'cosine'
            },
            'properties': [
                {
                    'name': 'username',
                    'dataType': ['text'],
                    'description': 'The username of the user who received the recommendation.'
                },
                {
                    'name': 'recommendation',
                    'dataType': ['ContentRecommendation'],
                    'description': 'A recommendation that was shown.',
                },
                {
                    'name': 'hasLiked',
                    'dataType': ['ContentRecommendation'],
                    'description': 'A recommendation that was liked.',
                },
                {
                    'name': 'notInterested',
                    'dataType': ['ContentRecommendation'],
                    'description': 'A recommendation that was not interesting.'
                },
                {
                    'name': 'clickedNextItem',
                    'dataType': ['ContentRecommendation'],
                    'description': 'A recommendation where the user clicked next item.'
                },
                {
                    'name': 'changedTune',
                    'dataType': ['ContentRecommendation'],
                    'description': 'A recommendation where the user changed the tune.'
                },
                {
                    'name': 'hasRefreshed',
                    'dataType': ['ContentRecommendation'],
                    'description': 'A recommendation where the user refreshed the entire page.'
                }
            ],
        },
        {
            'class': 'ContentRecommendation',
            'description': 'A content recommendation.',
            'moduleConfig': {
                'text2vec-contextionary': {
                    'vectorizeClassName': False,
                }
            },
            'vectorizer': 'text2vec-contextionary',
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
                'vectorCacheMaxObjects': 20000,
                'flatSearchCutoff': 40000,
                'distance': 'cosine'
            },
            'properties': [
                {
                    'name': 'username',
                    'dataType': ['text'],
                    'description': 'The user_data of the user who received the recommendation.',
                    'moduleConfig': {
                        'text2vec-contextionary': {
                            'skip': True,
                            'vectorizePropertyName': False
                        }
                    }
                },
                {
                    'name': 'channel',
                    'dataType': ['text'],
                    'description': 'The channel the recommendation was shown in.',
                    'moduleConfig': {
                        'text2vec-contextionary': {
                            'skip': True,
                            'vectorizePropertyName': False
                        }
                    }
                },
                {
                    'name': 'title',
                    'dataType': ['text'],
                    'description': 'The recommendation title.',
                    'moduleConfig': {
                        'text2vec-contextionary': {
                            'skip': False,
                            'vectorizePropertyName': False
                        }
                    }
                },
                {
                    'name': 'creator',
                    'dataType': ['text'],
                    'description': 'The recommendation creator.',
                    'moduleConfig': {
                        'text2vec-contextionary': {
                            'skip': False,
                            'vectorizePropertyName': False
                        }
                    }
                },
                {
                    'name': 'description',
                    'dataType': ['text'],
                    'description': 'The content description.',
                    'moduleConfig': {
                        'text2vec-contextionary': {
                            'skip': False,
                            'vectorizePropertyName': False
                        }
                    }
                },
                {
                    'name': 'user_action',
                    'dataType': ['text'],
                    'description': 'The user action that was taken on the recommendation.',
                    'moduleConfig': {
                        'text2vec-contextionary': {
                            'skip': True,
                            'vectorizePropertyName': False
                        }
                    }
                },
                {
                    'name': 'datetime',
                    'dataType': ['text'],
                    'description': 'The datetime of the recommendation interaction.'
                },
                {
                    'name': 'timestamp',
                    'dataType': ['int'],
                    'description': 'The timestamp of the recommendation interaction.'
                }
            ]
        }
    ]}
