import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

# Initialize Flask app
app = Flask(__name__)   # Create a new Flask web application

# Set the name of session cookie and secret key for Flask session management
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie' 
app.secret_key = '<YOURKEY>' 
TOKEN_INFO = 'token_info' 

# Route for the login page
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url() 
    return redirect(auth_url)  # Redirect user to Spotify login page

# Route for the Spotify redirect page
@app.route('/redirect')
def redirect_page():
    session.clear()  # Clear the session data
    code = request.args.get('code')  # Get the authorization code from the URL
    token_info = create_spotify_oauth().get_access_token(code)  # Exchange code for an access token
    session[TOKEN_INFO] = token_info  # Store the token information in the session
    return redirect(url_for('save_weekly', external=True))  # Redirect to the save_weekly function

# Route to save Discover Weekly playlist to Saved Weekly playlist
@app.route('/saveWeekly')
def save_weekly():
    try:
        token_info = get_token()  # Retrieve and refresh the token if necessary
    except:
        print('User not logged in')
        return redirect('/')  # Redirect to login if user is not authenticated
    
    sp = spotipy.Spotify(auth=token_info['access_token'])  # Create Spotify client with the access token
    user_id = sp.current_user()['id']  # Get the user's Spotify ID

    discover_weekly_playlist_id = None  
    saved_weekly_playlist_id = None  
    current_playlists = sp.current_user_playlists()['items']  # Get all current user playlists

    # Loop through the playlists to find Discover Weekly and Saved Weekly
    for playlist in current_playlists:
        if playlist['name'] == 'Discover Weekly':
            discover_weekly_playlist_id = playlist['id']  
        if playlist['name'] == 'Saved Weekly':
            saved_weekly_playlist_id = playlist['id']  
    
    if not discover_weekly_playlist_id:
        return 'Discover Weekly not found'  
    
    # If Saved Weekly playlist does not exist, create it
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)  # Create a new playlist called 'Saved Weekly'
        saved_weekly_playlist_id = new_playlist['id']  # Get the new playlist ID
    
    discover_weekly_playlist_id = sp.playlist_items(discover_weekly_playlist_id)  # Get items from Discover Weekly playlist
    song_uris = []  # List of song URIs

    # Loop through songs in Discover Weekly and extract their URIs
    for song in discover_weekly_playlist_id['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)  # Add URI to the list

    # Add songs from Discover Weekly to Saved Weekly playlist
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)
    return 'Success!'  

# Function to retrieve and refresh token if it has expired
def get_token():
    token_info = session.get(TOKEN_INFO, None)  # Get token info from the session
    if not token_info:
        return redirect(url_for('login', external=False))  # Redirect to login if no token is found

    now = int(time.time())  # Get the current time
    is_expired = token_info['expires_at'] - now < 60  # Check if the token is expired

    if is_expired:
        spotify_oauth = create_spotify_oauth()  # Create a new SpotifyOAuth object
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])  # Refresh the access token

    return token_info  # Return the token information

# Function to create a SpotifyOAuth object with necessary credentials and scope
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="<YOUR_CLIENT_ID>", 
        client_secret="<YOUR_CLIENT_SECRET>",  
        redirect_uri=url_for('redirect_page', _external=True),  # Redirect URI after authentication
        scope='user-library-read playlist-modify-public playlist-modify-private'  # Scope for required permissions
    )

app.run(debug=True)  # Run the Flask app in debug mode
