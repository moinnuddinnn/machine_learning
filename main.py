from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import os, base64
from requests import post, get

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

users = {}

# Spotify Auth
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    return result.json()["access_token"]

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# ------------------- ARTIST FUNCTIONS -------------------

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    result = get(url + query, headers=headers)
    items = result.json()["artists"]["items"]
    return items[0] if items else None

def get_artist_details(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = get_auth_header(token)
    return get(url, headers=headers).json()

def get_songs(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    return get(url, headers=headers).json()["tracks"]

def get_discography_all(token, artist_id):
    """Fetch ALL albums & singles for an artist (handles pagination + dedupe)."""
    headers = get_auth_header(token)
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?include_groups=album,single&limit=50&market=US"

    all_items = []
    seen_ids = set()

    while url:
        resp = get(url, headers=headers).json()
        items = resp.get("items", [])
        for it in items:
            if it["id"] not in seen_ids:
                seen_ids.add(it["id"])
                all_items.append(it)
        url = resp.get("next")

    from datetime import datetime
    def parse_release(item):
        d = item.get("release_date", "0000-00-00")
        p = item.get("release_date_precision", "day")
        if p == "year":
            d = f"{d}-12-31"
        elif p == "month":
            d = f"{d}-28"
        try:
            return datetime.fromisoformat(d)
        except Exception:
            return datetime.min

    all_items.sort(key=parse_release, reverse=True)
    return all_items

def split_albums_singles(items):
    """Split items into Albums and Singles based on album_group/album_type."""
    albums, singles = [], []
    for it in items:
        grp = it.get("album_group") or it.get("album_type")
        if grp == "album":
            albums.append(it)
        elif grp == "single":
            singles.append(it)
    return albums, singles

# ------------------- TRENDING ARTISTS -------------------

def get_trending_artists(token, region="international", min_followers=5000000, limit=10):
    """Fetch trending artists by followers in a region (approx via genre search)."""
    headers = get_auth_header(token)
    url = "https://api.spotify.com/v1/search"

    # Basic region-to-genre mapping
    region_queries = {
        "international": "genre:pop",
        "us": "genre:hip-hop",
        "uk": "genre:rock",
        "india": "genre:bollywood"
    }

    query = f"?q={region_queries.get(region, 'genre:pop')}&type=artist&limit=50"
    resp = get(url + query, headers=headers).json()
    artists = resp.get("artists", {}).get("items", [])

    # Filter + sort
    trending = [a for a in artists if a["followers"]["total"] >= min_followers]
    trending.sort(key=lambda x: x["followers"]["total"], reverse=True)

    return trending[:limit]

# ------------------- RECOMMENDATIONS -------------------

def get_recommendations(token, artist_ids, limit_per_artist=5):
    """Given a list of artist IDs, fetch related artists as recommendations."""
    headers = get_auth_header(token)
    recommended = []

    for aid in artist_ids:
        url = f"https://api.spotify.com/v1/artists/{aid}/related-artists"
        resp = get(url, headers=headers).json()
        items = resp.get("artists", [])[:limit_per_artist]
        recommended.extend(items)

    # Deduplicate by artist ID
    seen = set()
    unique_recs = []
    for artist in recommended:
        if artist["id"] not in seen:
            seen.add(artist["id"])
            unique_recs.append(artist)

    return unique_recs



# ------------------- ROUTES -------------------

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return "User already exists!"
        users[username] = password
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        return "Invalid credentials!"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("welcome"))

@app.route("/index", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    artist_data, songs, albums, singles = None, [], [], []
    trending_artists = []
    recommendations = []
    selected_artist_ids = []
    token = get_token()

    if request.method == "POST":
        # Artist search
        artist_name = request.form.get("artist_name")
        if artist_name:
            result = search_for_artist(token, artist_name)
            if result:
                artist_id = result["id"]
                selected_artist_ids.append(artist_id)
                artist_data = get_artist_details(token, artist_id)
                songs = get_songs(token, artist_id)[:5]
                discog = get_discography_all(token, artist_id)
                albums, singles = split_albums_singles(discog)

        # If user selects additional artists for recommendations
        # (You can extend the form to allow selecting up to 3 artists)
        for i in range(1, 4):
            aid = request.form.get(f"artist{i}_id")
            if aid:
                selected_artist_ids.append(aid)

    # Always fetch trending artists
    trending_artists = get_trending_artists(token, region="international", min_followers=5000000, limit=10)

    # Fetch recommendations based on selected artists
    if selected_artist_ids:
        recommendations = get_recommendations(token, selected_artist_ids, limit_per_artist=5)

    return render_template(
        "index.html",
        artist=artist_data,
        songs=songs,
        albums=albums,
        singles=singles,
        trending=trending_artists,
        recommendations=recommendations
    )

@app.route("/recommend", methods=["POST", "GET"])
def recommend():
    if "user" not in session:
        return redirect(url_for("login"))

    token = get_token()
    # Get selected artist IDs from the form
    selected_artists = request.form.getlist("seed_artist")  # e.g., ["id1", "id2", "id3"]
    
    recommended_tracks = []
    if selected_artists:
        recommended_tracks = get_recommendations(token, selected_artists, limit=10)

    return render_template(
        "recommend.html",
        recommended_tracks=recommended_tracks
    )


if __name__ == "__main__":
    app.run(debug=True)
