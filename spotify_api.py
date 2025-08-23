from dotenv import load_dotenv
import os
import base64
import json
from requests import post, get

load_dotenv()

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
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers= headers)
    json_result = json.loads(result.content)["artists"]["items"]
    
    if len(json_result) == 0:
        print("No artist with this name exsists...")
        return None
    
    return json_result[0]

def get_songs(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_artist_details(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    return result.json()



token = get_token()
user_input = input("Enter the artist's name to search: ")
result = search_for_artist(token, user_input)
print(result["name"])
artist_id = result["id"]
songs = get_songs(token, artist_id)
details = get_artist_details(token, artist_id)

print("Artist Name:", details["name"])
print("Followers:", details["followers"]["total"])
print("Popularity:", details["popularity"])
print("Spotify URL:", details["external_urls"]["spotify"])

print("\nGenres:")
for genre in details["genres"]:
    print("-", genre)




#for idx, detail in enumerate(details):
    #print(f"{idx + 1}, {detail}")
#for idx, song in enumerate(songs):
    #print(f"{idx + 1}, {song['name']}")
