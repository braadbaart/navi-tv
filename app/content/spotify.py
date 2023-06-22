import os
import spotipy
import streamlit as st


def build_spotify_client(file_path):
    return spotipy.Spotify(
        auth_manager=spotipy.SpotifyOAuth(
            client_id=st.secrets['spotify']['client_id'],
            client_secret=st.secrets['spotify']['client_secret'],
            redirect_uri=st.secrets['spotify']['redirect_uri'],
            scope='user-library-read,playlist-modify-public,playlist-modify-private',
            cache_path=os.path.join(file_path, 'spotify_cache.json')
        )
    )


def search_spotify(spotify, query):
    return spotify.search(query, limit=1, type='track')


def parse_spotify_search_results(results):
    if results['tracks']['total'] == 0:
        return None
    return results['tracks']['items'][0]['uri']


def display_spotify_track_in_app(spotify, track_uri):
    track = spotify.track(track_uri)
    st.write(track['name'], 'by', track['artists'][0]['name'])
    st.image(track['album']['images'][0]['url'])
    st.write(track['external_urls']['spotify'])
    st.write(track['preview_url'])

