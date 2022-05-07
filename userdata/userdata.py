import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import config

scope = "user-library-read user-follow-read user-top-read playlist-read-private" 
spotify_details = {'client_id':config.client_id, 'client_secret':config.client_secret, 'redirect':config.redirect_uri}
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=spotify_details['client_id'],
    client_secret=spotify_details['client_secret'],
    redirect_uri=spotify_details['redirect'],  
    open_browser=False,  
    scope=scope,)
)


def offset_api_limit(sp, sp_call):
    results = sp_call
    if 'items' not in results.keys():
        results = results['artists']
    data = results['items']
    while results['next']:
        results = sp.next(results)
        if 'items' not in results.keys():
            results = results['artists']
        data.extend(results['items'])
    return data


def get_artists_df(artists):
    artists_df = pd.DataFrame(artists)
    artists_df['followers'] = artists_df['followers'].apply(lambda x: x['total'])
    return artists_df[['id', 'uri', 'type', 'name', 'genres', 'followers']]


def get_tracks_df(tracks):
    tracks_df = pd.DataFrame(tracks)
    if 'track' in tracks_df.columns.tolist():
        tracks_df = tracks_df.drop('track', 1).assign(**tracks_df['track'].apply(pd.Series))
    tracks_df['album_id'] = tracks_df['album'].apply(lambda x: x['id'])
    tracks_df['album_name'] = tracks_df['album'].apply(lambda x: x['name'])
    tracks_df['album_release_date'] = tracks_df['album'].apply(lambda x: x['release_date'])
    tracks_df['album_tracks'] = tracks_df['album'].apply(lambda x: x['total_tracks'])
    tracks_df['album_type'] = tracks_df['album'].apply(lambda x: x['type'])
    # artists abums
    tracks_df['album_artist_id'] = tracks_df['album'].apply(lambda x: x['artists'][0]['id'])
    tracks_df['album_artist_name'] = tracks_df['album'].apply(lambda x: x['artists'][0]['name'])
    # Artist
    tracks_df['artist_id'] = tracks_df['artists'].apply(lambda x: x[0]['id'])
    tracks_df['artist_name'] = tracks_df['artists'].apply(lambda x: x[0]['name'])
    select_columns = ['id', 'name', 'popularity', 'type', 'is_local', 'explicit', 'duration_ms', 'disc_number',
                      'track_number',
                      'artist_id', 'artist_name', 'album_artist_id', 'album_artist_name',
                      'album_id', 'album_name', 'album_release_date', 'album_tracks', 'album_type']
    if 'added_at' in tracks_df.columns.tolist():
        select_columns.append('added_at')
    return tracks_df[select_columns]


def get_track_audio_df(sp, df):
    df['genres'] = df['artist_id'].apply(lambda x: sp.artist(x)['genres'])
    df['album_genres'] = df['album_artist_id'].apply(lambda x: sp.artist(x)['genres'])
    df['audio_features'] = df['id'].apply(lambda x: sp.audio_features(x))
    df['audio_features'] = df['audio_features'].apply(pd.Series)
    df = df.drop('audio_features', 1).assign(**df['audio_features'].apply(pd.Series))
    return df


def get_all_playlist_tracks_df(sp, sp_call):
    playlists = sp_call
    playlist_data, data = playlists['items'], []
    playlist_ids, playlist_names, playlist_tracks = [], [], []
    for playlist in playlist_data:
        for i in range(playlist['tracks']['total']):
            playlist_ids.append(playlist['id'])
            playlist_names.append(playlist['name'])
            playlist_tracks.append(playlist['tracks']['total'])
        saved_tracks = sp.playlist(playlist['id'], fields="tracks, next")
        results = saved_tracks['tracks']
        data.extend(results['items'])
        while results['next']:
            results = sp.next(results)
            data.extend(results['items'])

    tracks_df = pd.DataFrame(data)
    
    tracks_df['playlist_id'] = playlist_ids
    tracks_df['playlist_name'] = playlist_names
    tracks_df['playlist_tracks'] = playlist_tracks
    
    tracks_df = tracks_df[tracks_df['is_local'] == False]  # remove local tracks (no audio data)
    tracks_df = tracks_df.drop('track', 1).assign(**tracks_df['track'].apply(pd.Series))
    
    tracks_df['album_id'] = tracks_df['album'].apply(lambda x: x['id'])
    tracks_df['album_name'] = tracks_df['album'].apply(lambda x: x['name'])
    tracks_df['album_release_date'] = tracks_df['album'].apply(lambda x: x['release_date'])
    tracks_df['album_tracks'] = tracks_df['album'].apply(lambda x: x['total_tracks'])
    tracks_df['album_type'] = tracks_df['album'].apply(lambda x: x['type'])
    
    tracks_df['album_artist_id'] = tracks_df['album'].apply(lambda x: x['artists'][0]['id'])
    tracks_df['album_artist_name'] = tracks_df['album'].apply(lambda x: x['artists'][0]['name'])
    
    tracks_df['artist_id'] = tracks_df['artists'].apply(lambda x: x[0]['id'])
    tracks_df['artist_name'] = tracks_df['artists'].apply(lambda x: x[0]['name'])
    # playlist_tracks has ['added_at', 'added_by', 'is_local', 'primary_color', 'track', 'video_thumbnail']
    select_columns = ['id', 'name', 'popularity', 'type', 'is_local', 'explicit', 'duration_ms', 'disc_number',
                      'track_number',
                      'artist_id', 'artist_name', 'album_artist_id', 'album_artist_name',
                      'album_id', 'album_name', 'album_release_date', 'album_tracks', 'album_type',
                      'playlist_id', 'playlist_name', 'playlist_tracks',
                      'added_at', 'added_by']
    return tracks_df[select_columns]

#spotify recommendations
def get_recommendations(sp, tracks):
    data = []
    for x in tracks:
        results = sp.recommendations(seed_tracks=[x])  
        data.extend(results['tracks'])
    return data

top_artists = offset_api_limit(sp, sp.current_user_top_artists())
top_artists_df = get_artists_df(top_artists)
top_artists_df.to_csv("spotify/top_artists.csv")
top_tracks = offset_api_limit(sp, sp.current_user_top_tracks())
top_tracks_df = get_tracks_df(top_tracks)
top_tracks_df = get_track_audio_df(sp, top_tracks_df)
top_tracks_df.to_csv("spotify/top_tracks.csv")
