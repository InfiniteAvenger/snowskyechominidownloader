"""Spotify playlist parsing - fetches song names to search on Deezer."""
import re
import time
import hmac
import hashlib
from time import sleep
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Callable

import requests

_TOTP_SECRET = bytearray([53, 53, 48, 55, 49, 52, 53, 56, 53, 52, 56, 55,
                          52, 57, 57, 53, 57, 50, 50, 52, 56, 51, 48, 51, 50, 57, 51, 52, 55])

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://open.spotify.com/",
    "Origin": "https://open.spotify.com",
}


def _generate_totp() -> Tuple[str, int]:
    counter = int(time.time()) // 30
    digest = hmac.new(_TOTP_SECRET, counter.to_bytes(8, byteorder="big"), hashlib.sha1).digest()
    offset = digest[-1] & 15
    truncated = (
        (digest[offset] & 127) << 24
        | (digest[offset + 1] & 255) << 16
        | (digest[offset + 2] & 255) << 8
        | (digest[offset + 3] & 255)
    )
    return str(truncated % 1_000_000).zfill(6), counter * 30_000


def _parse_uri(uri: str) -> dict:
    u = urlparse(uri)
    if not u.scheme and not u.netloc:
        return {"type": "playlist", "id": u.path}
    if u.scheme == "spotify":
        parts = uri.split(":")
    else:
        parts = u.path.split("/")
    if parts[1] == "embed":
        parts = parts[1:]
    if len(parts) >= 3 and parts[1] in ("album", "track", "playlist"):
        return {"type": parts[1], "id": parts[2]}
    raise ValueError(f"Unsupported Spotify URL: {uri}")


def _api_get(url, token, proxy):
    headers = dict(_HEADERS)
    headers["Authorization"] = f"Bearer {token}"
    r = requests.get(url, headers=headers, proxies={"https": proxy} if proxy else None, timeout=10)
    if r.status_code == 429:
        wait = int(r.headers.get("Retry-After", "5")) + 1
        print(f"Rate limited, waiting {wait}s")
        sleep(wait)
        return None
    r.raise_for_status()
    return r.json()


def _parse_track(track: dict) -> str:
    artist = track["artists"][0]["name"]
    name = track["name"]
    return re.sub(r"\([^)]*\)", "", f"{artist} {name}").strip()


def get_songs_from_spotify_website(playlist_url: str, proxy: str = None) -> list[str]:
    """Parse a Spotify playlist/album/track URL and return list of 'artist title' strings."""
    info = _parse_uri(playlist_url)

    totp, ts = _generate_totp()
    params = {"reason": "init", "productType": "web-player", "totp": totp, "totpVer": 5, "ts": ts}

    r = requests.get("https://open.spotify.com/get_access_token", headers=_HEADERS, params=params,
                      proxies={"https": proxy} if proxy else None)
    r.raise_for_status()
    token = r.json()["accessToken"]

    results = []
    if info["type"] == "playlist":
        url = f"https://api.spotify.com/v1/playlists/{info['id']}/tracks?limit=100&additional_types=track"
        while url:
            data = _api_get(url, token, proxy)
            if data is None:
                data = _api_get(url, token, proxy)
                if data is None:
                    break
            for item in data.get("items", []):
                if item.get("track"):
                    results.append(_parse_track(item["track"]))
            url = data.get("next")
    elif info["type"] == "track":
        data = _api_get(f"https://api.spotify.com/v1/tracks/{info['id']}", token, proxy)
        if data:
            results.append(_parse_track(data))
    elif info["type"] == "album":
        data = _api_get(f"https://api.spotify.com/v1/albums/{info['id']}/tracks", token, proxy)
        if data:
            for t in data.get("items", []):
                results.append(_parse_track(t))

    return [r for r in results if r]
