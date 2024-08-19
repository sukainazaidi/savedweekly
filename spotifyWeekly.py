import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

#initialize flask app
app = Flask(__name__)   #initialize flask

#set the name of session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'dslriftuhy3qewt2h487yhbfcw'
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_weekly', external = True))

@app.route('/saveWeekly')
def save_weekly():
    try:
        token_info = get_token()
    except:
        print('User not logged in')
        return redirect('/')
    
    sp = spotipy.Spotify(auth = token_info['access_token'])
    user_id = sp.current_user()['id']

    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None
    current_playlists = sp.current_user_playlists()['items']
    for playlist in current_playlists:
        if(playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']
    
    if not discover_weekly_playlist_id:
        return 'Discover Weekly not found'
    
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    discover_weekly_playlist_id = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist_id['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)
    return 'Success!'


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return redirect(url_for('login', external = False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = "b599998e6b4445e6ba85f4859daa8f94",
        client_secret = "48b1023ce3534f9281b55ead92d9dc6c",
        redirect_uri = url_for('redirect_page', _external = True),
        scope = 'user-library-read playlist-modify-public playlist-modify-private'
        )

app.run(debug = True)