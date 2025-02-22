import json
import requests
import urllib.parse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

# URL del file JSON online
URL = 'https://vavoo.to/channels'

app = FastAPI()

# Abilita CORS per consentire le richieste da Stremio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permetti a qualsiasi dominio di accedere
    allow_credentials=True,
    allow_methods=["*"],  # Permetti tutti i metodi (GET, POST, ecc.)
    allow_headers=["*"],  # Permetti tutti gli header
)

# Funzione per generare la lista dei canali italiani con encoding corretto
def get_italian_channels():
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        channels = []
        for entry in data:
            if entry['country'] == 'Italy':
                encoded_url = urllib.parse.quote(f"https://vavoo.to/play/{entry['id']}/index.m3u8", safe='')
                stream_url = (
                    f"https://[MEDIA_FLOW_PROXY]/proxy/hls/manifest.m3u8?"
                    f"api_password=[PASSWORD]&d={encoded_url}"
                    f"&h_user-agent={urllib.parse.quote('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36')}"
                    f"&h_referer={urllib.parse.quote('https://newembedplay.xyz/')}"
                    f"&h_origin={urllib.parse.quote('https://newembedplay.xyz')}"
                )
                channels.append({
                    "id": f"tv:{entry['id']}",  # Modifica formato ID
                    "name": entry['name'],
                    "url": stream_url
                })
        return channels
    else:
        return []

# Endpoint per l'installazione su Stremio
@app.get("/manifest.json")
def get_manifest():
    return {
        "id": "org.stremio.italian.channels",
        "version": "1.0.0",
        "name": "Italian Channels",
        "description": "Catalogo IPTV Italiano per Stremio",
        "types": ["movie", "tv"],
        "catalogs": [{
            "id": "italian_channels",
            "name": "Italian IPTV",
            "type": "tv"
        }],
        "resources": ["catalog", "stream", "meta"],
        "idPrefixes": ["tv:"],  # Permette a Stremio di riconoscere i canali TV
        "logo": "https://i.imgur.com/3Tv3KQ1.png"
    }

# Endpoint per il catalogo dei canali
@app.get("/catalog/tv/italian_channels.json")
def get_catalog():
    channels = get_italian_channels()
    return {
        "metas": [
            {
                "id": channel["id"],
                "name": channel["name"],
                "type": "tv"
            }
            for channel in channels
        ]
    }

# Endpoint per la ricerca nei canali
@app.get("/catalog/tv/italian_channels/search={query}.json")
def search_catalog(query: str):
    channels = get_italian_channels()
    results = [
        {
            "id": channel["id"],
            "name": channel["name"],
            "type": "tv"
        }
        for channel in channels if query.lower() in channel["name"].lower()
    ]
    return {"metas": results}

# Endpoint per ottenere lo stream di un canale
@app.get("/stream/tv/{channel_id}.json")
def get_stream(channel_id: str):
    channels = get_italian_channels()
    for channel in channels:
        if channel["id"] == channel_id:
            return {
                "streams": [{
                    "url": channel["url"]
                }]
            }
    return {"streams": []}

# Endpoint per ottenere i dettagli di un canale (Meta)
@app.get("/meta/tv/{channel_id}.json")
def get_meta(channel_id: str):
    channels = get_italian_channels()
    for channel in channels:
        if channel["id"] == channel_id:
            return {
                "meta": {
                    "id": channel["id"],
                    "name": channel["name"],
                    "type": "tv",
                    "poster": "https://i.imgur.com/3Tv3KQ1.png",
                    "background": "https://i.imgur.com/3Tv3KQ1.png",
                    "logo": "https://i.imgur.com/3Tv3KQ1.png",
                    "description": f"Guarda {channel['name']} in streaming su Stremio.",
                    "genres": ["Live TV"],
                    "streams": [{"url": channel["url"]}]
                }
            }
    return {"error": "Canale non trovato", "meta": None}
