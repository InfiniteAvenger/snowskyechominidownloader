"""Deezer API integration - search, download, decrypt, and tag."""
from __future__ import annotations

import base64
import io
import json
import os
import re
import struct
import sys
import time
import urllib.parse
import html.parser
from binascii import a2b_hex, b2a_hex

import requests
from Crypto.Hash import MD5
from Crypto.Cipher import Blowfish
from mutagen.flac import FLAC, Picture
from PIL import Image

# ── Types ──
TYPE_TRACK = "track"
TYPE_ALBUM = "album"
TYPE_PLAYLIST = "playlist"
TYPE_ALBUM_TRACK = "album_track"
TYPE_ARTIST = "artist"

# ── Module state ──
session = None
session_jwt = None
_tmp_jwt = None
license_token = {}
sound_format = ""
album_data_global = None
download_lrc_enabled = True

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"


# ═══════════════════════════════════════════════════════════════
#  Session init
# ═══════════════════════════════════════════════════════════════

def init_deezer_session(config) -> None:
    """Initialise the Deezer HTTP session using the ARL cookie from config."""
    global session, license_token, sound_format

    proxy_server = config.get("proxy", "server", fallback="").strip()
    quality = config.get("deezer", "quality", fallback="mp3")
    arl = config.get("deezer", "cookie_arl", fallback="").strip()

    if not arl:
        print("WARNING: No Deezer ARL cookie configured. Deezer features disabled.")
        return

    headers = {
        "Pragma": "no-cache",
        "Origin": "https://www.deezer.com",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "Referer": "https://www.deezer.com/login",
    }
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update({"arl": arl, "comeback": "1"})

    if proxy_server:
        print(f"Using proxy {proxy_server}")
        session.proxies.update({"https": proxy_server})

    # Get license token and set quality
    try:
        lt, wsq = _get_user_data()
        license_token = lt
        _set_song_quality(quality, wsq)
    except Exception as e:
        print(f"WARNING: Could not init Deezer session: {e}")
        session = None
        return

    _init_lrc_session(config)
    print(f"Deezer session ready (quality: {sound_format})")


def _get_user_data():
    r = session.get("https://www.deezer.com/ajax/gw-light.php?method=deezer.getUserData&input=3&api_version=1.0&api_token=")
    data = r.json()["results"]
    opts = data["USER"]["OPTIONS"]
    return opts["license_token"], opts["web_sound_quality"]


def _set_song_quality(quality_config: str, web_sound_quality: dict):
    global sound_format
    flac_ok = web_sound_quality.get("lossless") is True
    if flac_ok and quality_config == "flac":
        sound_format = "FLAC"
    elif flac_ok:
        sound_format = "MP3_320"
    else:
        if quality_config == "flac":
            print("WARNING: FLAC not supported (no premium?). Falling back to MP3.")
        sound_format = "MP3_128"


def get_file_extension() -> str:
    return "flac" if sound_format == "FLAC" else "mp3"


def _init_lrc_session(config):
    """Set up the JWT session for synchronized lyrics if cookies are configured."""
    global session_jwt, _tmp_jwt
    has_jwt = config.has_option("deezer", "cookie_fixed_jwt")
    has_rd = config.has_option("deezer", "cookie_refresh_token_D")
    has_rt = config.has_option("deezer", "cookie_refresh_token")

    if has_jwt and has_rd and has_rt:
        jwt = config.get("deezer", "cookie_fixed_jwt", raw=True).strip('"')
        rd = config.get("deezer", "cookie_refresh_token_D", raw=True).strip('"')
        rt = config.get("deezer", "cookie_refresh_token", raw=True).strip('"')
        if jwt and rd and rt:
            session_jwt = requests.Session()
            _tmp_jwt = jwt
            arl = config.get("deezer", "cookie_arl")
            session_jwt.cookies.set("arl", arl, domain="deezer.com")
            session_jwt.cookies.set("refresh-token", rt, domain="deezer.com")
            session_jwt.cookies.set("refresh-token-deezer", rd, domain="deezer.com")
            session_jwt.cookies.set("jwt", jwt, domain="deezer.com")
            session_jwt.cookies.set("jwt-Deezer", jwt, domain="deezer.com")
            print("Lyrics (LRC) session ready")
            return
    print("Lyrics (LRC) disabled — cookies not configured")


# ═══════════════════════════════════════════════════════════════
#  Search
# ═══════════════════════════════════════════════════════════════

def deezer_search(query: str, search_type: str) -> list:
    """Search Deezer for tracks, albums, or artists. Returns list of result dicts."""
    if session is None:
        return []
    if search_type not in (TYPE_TRACK, TYPE_ALBUM, TYPE_ALBUM_TRACK, TYPE_ARTIST):
        return []

    encoded = urllib.parse.quote_plus(query)
    try:
        if search_type == TYPE_ALBUM_TRACK:
            data = get_song_infos_from_deezer_website(TYPE_ALBUM, encoded)
        elif search_type == TYPE_ARTIST:
            data = _search_artist_discography(encoded)
            return _format_results(data, TYPE_ALBUM)  # artist search returns albums
        elif search_type == TYPE_ALBUM:
            data = _search_albums(encoded)
        else:
            resp = session.get(f"https://api.deezer.com/search/{search_type}?q={encoded}&limit=100")
            resp.raise_for_status()
            data = resp.json().get("data", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []

    return _format_results(data, search_type)


def _search_artist_discography(encoded_query: str) -> list:
    """Search for an artist by name and return their full discography."""
    resp = session.get(f"https://api.deezer.com/search/artist?q={encoded_query}&limit=1")
    resp.raise_for_status()
    artists = resp.json().get("data", [])
    if not artists:
        return []
    artist = artists[0]
    albums = _get_artist_albums(artist["id"])
    for album in albums:
        if "artist" not in album:
            album["artist"] = artist
        elif not album["artist"].get("name"):
            album["artist"]["name"] = artist["name"]
    return albums


def _search_albums(encoded_query: str) -> list:
    """Album search with artist discography supplementation."""
    resp = session.get(f"https://api.deezer.com/search/album?q={encoded_query}&limit=100")
    resp.raise_for_status()
    data = resp.json().get("data", [])
    seen = {item["id"] for item in data}
    artist_ids = set()
    artist_names = {}

    try:
        # Artist search
        ar = session.get(f"https://api.deezer.com/search/artist?q={encoded_query}&limit=3")
        ar.raise_for_status()
        for a in ar.json().get("data", []):
            artist_ids.add(a["id"])
            artist_names[a["id"]] = a["name"]

        # Track search to find dominant artist
        from collections import Counter
        tr = session.get(f"https://api.deezer.com/search/track?q={encoded_query}&limit=30")
        tr.raise_for_status()
        counts = Counter()
        for t in tr.json().get("data", []):
            counts[t["artist"]["id"]] += 1
            artist_names[t["artist"]["id"]] = t["artist"]["name"]
        if counts:
            top_id, top_n = counts.most_common(1)[0]
            threshold = min(3, top_n)
            for aid, n in counts.items():
                if n >= threshold and aid not in artist_ids:
                    artist_ids.add(aid)

        # Fetch discographies
        for aid in artist_ids:
            albums = _get_artist_albums(aid)
            for album in albums:
                if album["id"] not in seen:
                    if "artist" not in album:
                        album["artist"] = {"name": artist_names.get(aid, ""), "id": aid}
                    elif not album["artist"].get("name"):
                        album["artist"]["name"] = artist_names.get(aid, "")
                    data.append(album)
                    seen.add(album["id"])
    except Exception as e:
        print(f"Could not supplement album search: {e}")

    return data


def _get_artist_albums(artist_id) -> list:
    albums = []
    url = f"https://api.deezer.com/artist/{artist_id}/albums?limit=100"
    try:
        while url:
            r = session.get(url)
            r.raise_for_status()
            d = r.json()
            albums.extend(d.get("data", []))
            url = d.get("next")
    except Exception as e:
        print(f"Could not fetch artist albums: {e}")
    return albums


def _format_results(data, search_type) -> list:
    results = []
    if not data:
        return results
    for item in data:
        if not isinstance(item, dict):
            continue
        r = {}
        if search_type == TYPE_ALBUM:
            artist_dict = item.get("artist") or {}
            artist_name = artist_dict.get("name", "Unknown Artist") if isinstance(artist_dict, dict) else "Unknown Artist"
            r = {
                "id": str(item.get("id", "")),
                "id_type": TYPE_ALBUM,
                "album": item.get("title", "Unknown Album"),
                "album_id": item.get("id", ""),
                "img_url": item.get("cover_small", ""),
                "artist": artist_name,
                "title": "",
                "preview_url": "",
            }
        elif search_type == TYPE_TRACK:
            album_dict = item.get("album") or {}
            album_title = album_dict.get("title", "Unknown Album") if isinstance(album_dict, dict) else "Unknown Album"
            album_cover = album_dict.get("cover_small", "") if isinstance(album_dict, dict) else ""
            album_id = album_dict.get("id", "") if isinstance(album_dict, dict) else ""
            
            artist_dict = item.get("artist") or {}
            artist_name = artist_dict.get("name", "Unknown Artist") if isinstance(artist_dict, dict) else "Unknown Artist"
            
            r = {
                "id": str(item.get("id", "")),
                "id_type": TYPE_TRACK,
                "title": item.get("title", "Unknown Title"),
                "img_url": album_cover,
                "album": album_title,
                "album_id": album_id,
                "artist": artist_name,
                "preview_url": item.get("preview", ""),
            }
        elif search_type == TYPE_ALBUM_TRACK:
            pic_id = item.get("ALB_PICTURE")
            img_url = f"https://e-cdns-images.dzcdn.net/images/cover/{pic_id}/250x250.jpg" if pic_id else ""
            
            r = {
                "id": str(item.get("SNG_ID", "")),
                "id_type": TYPE_TRACK,
                "title": item.get("SNG_TITLE", "Unknown Title"),
                "img_url": img_url,
                "album": item.get("ALB_TITLE", "Unknown Album"),
                "album_id": item.get("ALB_ID", ""),
                "artist": item.get("ART_NAME", "Unknown Artist"),
                "preview_url": next((m.get("HREF", "") for m in item.get("MEDIA", []) if isinstance(m, dict) and m.get("TYPE") == "preview"), ""),
            }
        results.append(r)
    return results


# ═══════════════════════════════════════════════════════════════
#  Crypto
# ═══════════════════════════════════════════════════════════════

def _md5hex(data: bytes) -> bytes:
    h = MD5.new()
    h.update(data)
    return b2a_hex(h.digest())


def _calc_bf_key(song_id: str) -> str:
    key = b"g4el58wc0zvf9na1"
    sid_md5 = _md5hex(song_id.encode())
    return "".join(chr(sid_md5[i] ^ sid_md5[i + 16] ^ key[i]) for i in range(16))


def _bf_decrypt(data: bytes, key: str) -> bytes:
    iv = a2b_hex("0001020304050607")
    c = Blowfish.new(key.encode(), Blowfish.MODE_CBC, iv)
    return c.decrypt(data)


def _decrypt_file(response, key: str, fo):
    block_size = 2048
    for i, data in enumerate(response.iter_content(block_size)):
        if not data:
            break
        if (i % 3) == 0 and len(data) == block_size:
            data = _bf_decrypt(data, key)
        fo.write(data)


# ═══════════════════════════════════════════════════════════════
#  Song URL + Download
# ═══════════════════════════════════════════════════════════════

def _get_song_url(track_token: str) -> str:
    r = requests.post(
        "https://media.deezer.com/v1/get_url",
        json={
            "license_token": license_token,
            "media": [{"type": "FULL", "formats": [{"cipher": "BF_CBC_STRIPE", "format": sound_format}]}],
            "track_tokens": [track_token],
        },
        headers={"User-Agent": USER_AGENT},
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("data") or "errors" in data["data"][0]:
        msg = data["data"][0]["errors"][0]["message"] if data.get("data") else "Unknown error"
        raise RuntimeError(f"Could not get download URL: {msg}")
    return data["data"][0]["media"][0]["sources"][0]["url"]


def download_song(song: dict, output_file: str) -> None:
    """Download, decrypt, and tag a song."""
    global album_data_global
    is_flac = sound_format == "FLAC"

    # Pre-fetch album data for better FLAC tags
    if is_flac and song.get("ALB_ID"):
        if album_data_global is None or "GENRES" not in album_data_global:
            try:
                get_song_infos_from_deezer_website(TYPE_ALBUM, song["ALB_ID"])
            except Exception:
                pass

    try:
        url = _get_song_url(song["TRACK_TOKEN"])
    except Exception as e:
        if "FALLBACK" in song:
            song = song["FALLBACK"]
            try:
                url = _get_song_url(song["TRACK_TOKEN"])
            except Exception:
                raise
        else:
            raise

    key = _calc_bf_key(song["SNG_ID"])
    with session.get(url, stream=True) as resp:
        resp.raise_for_status()
        with open(output_file, "w+b") as fo:
            if not is_flac:
                _write_id3v2(fo, song)
                _decrypt_file(resp, key, fo)
                _write_id3v1(fo, song)
            else:
                _decrypt_file(resp, key, fo)

    if is_flac and os.path.exists(output_file):
        _add_vorbis_tags(song, output_file)

    _download_lrc(song["SNG_ID"], output_file)
    print(f"Downloaded: {output_file}")


# ═══════════════════════════════════════════════════════════════
#  ID3 tags (MP3)
# ═══════════════════════════════════════════════════════════════

def _write_id3v1(fo, song):
    def sg(key):
        try:
            return song.get(key, "").encode("utf-8")
        except Exception:
            return b""

    def ag(key):
        try:
            return album_data_global.get(key, "").encode("utf-8")
        except Exception:
            return b""

    try:
        track_num = int(sg("TRACK_NUMBER").decode() or "0")
    except Exception:
        track_num = 0

    data = struct.pack(
        "3s30s30s30s4s28sBHB",
        b"TAG", sg("SNG_TITLE"), sg("ART_NAME"), sg("ALB_TITLE"),
        ag("PHYSICAL_RELEASE_DATE"), ag("LABEL_NAME"), 0, track_num, 255,
    )
    fo.write(data)


def _write_id3v2(fo, song):
    def make28bit(x):
        return ((x << 3) & 0x7F000000) | ((x << 2) & 0x7F0000) | ((x << 1) & 0x7F00) | (x & 0x7F)

    def maketag(tag, content):
        return struct.pack(">4sLH", tag.encode("ascii"), len(content), 0) + content

    def makeutf8(txt):
        return f"\x03{txt}".encode()

    def makepic(data):
        return b"".join([b"\x00", b"image/jpeg", b"\0", b"\x03", b""[:64], b"\0", data])

    def sg(key):
        return song.get(key, "")

    def ag(key):
        try:
            return album_data_global.get(key, "") if album_data_global else ""
        except Exception:
            return ""

    try:
        track = f"{int(sg('TRACK_NUMBER')):02d}"
        tracks_total = ag("TRACKS")
        if tracks_total:
            track += f"/{int(tracks_total):02d}"
    except Exception:
        track = "00"

    id3 = [
        maketag("TRCK", makeutf8(track)),
        maketag("TLEN", makeutf8(str(int(sg("DURATION") or 0) * 1000))),
        maketag("TALB", makeutf8(sg("ALB_TITLE"))),
        maketag("TPE1", makeutf8(sg("ART_NAME"))),
        maketag("TPE2", makeutf8(sg("ART_NAME"))),
        maketag("TIT2", makeutf8(sg("SNG_TITLE"))),
        maketag("TSRC", makeutf8(sg("ISRC"))),
        maketag("TPOS", makeutf8(sg("DISK_NUMBER"))),
    ]

    try:
        year = ag("PHYSICAL_RELEASE_DATE")[:4]
        if year:
            id3.append(maketag("TYER", makeutf8(year)))
    except Exception:
        pass

    try:
        pic_data = _download_picture(sg("ALB_PICTURE"))
        if pic_data:
            id3.append(maketag("APIC", makepic(pic_data)))
    except Exception:
        pass

    id3data = b"".join(id3)
    hdr = struct.pack(">3sHBL", b"ID3", 0x300, 0x00, make28bit(len(id3data)))
    fo.write(hdr)
    fo.write(id3data)


# ═══════════════════════════════════════════════════════════════
#  Vorbis tags (FLAC)
# ═══════════════════════════════════════════════════════════════

def _add_vorbis_tags(song: dict, output_file: str):
    try:
        audio = FLAC(output_file)
        audio.clear()

        tag_map = {
            "TITLE": "SNG_TITLE", "ARTIST": "ART_NAME", "ALBUM": "ALB_TITLE",
            "TRACKNUMBER": "TRACK_NUMBER", "DISCNUMBER": "DISK_NUMBER",
            "ISRC": "ISRC",
        }
        for tag, key in tag_map.items():
            if key in song:
                audio[tag] = str(song[key])

        # Genres
        genres = _collect_genres(song)
        if genres:
            audio["GENRE"] = genres

        # Dates
        release_date = _get_release_date(song)
        if release_date:
            year = release_date[:4]
            audio["DATE"] = release_date
            audio["YEAR"] = year
            audio["ORIGINALDATE"] = release_date
            audio["ORIGINALYEAR"] = year

        # Label
        label = _get_label(song)
        if label:
            audio["ORGANIZATION"] = label
            audio["PUBLISHER"] = label

        # Cover art
        if "ALB_PICTURE" in song:
            try:
                pic_data = _download_picture(song["ALB_PICTURE"])
                if pic_data:
                    # Resize to 750x750
                    img = Image.open(io.BytesIO(pic_data))
                    img = img.resize((750, 750), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=90, optimize=True, progressive=False)
                    pic_data = buf.getvalue()

                    pic = Picture()
                    pic.type = 3
                    pic.mime = "image/jpeg"
                    pic.desc = "Cover (Front)"
                    pic.data = pic_data
                    pic.width = 750
                    pic.height = 750
                    pic.depth = 24
                    audio.add_picture(pic)
            except Exception as e:
                print(f"Could not add cover art: {e}")

        audio.save()
    except Exception as e:
        print(f"ERROR adding Vorbis tags: {e}")


def tag_mp3_file(song: dict, output_file: str):
    """Tag an existing MP3 file with song metadata using mutagen."""
    try:
        from mutagen.mp3 import EasyMP3
        from mutagen.id3 import ID3, APIC
        from PIL import Image
        import io

        audio = EasyMP3(output_file)
        try:
            audio.delete()
        except Exception:
            pass

        audio['title'] = song.get('SNG_TITLE', 'Unknown Title')
        audio['artist'] = song.get('ART_NAME', 'Unknown Artist')
        audio['album'] = song.get('ALB_TITLE', 'Unknown Album')
        
        track = song.get('TRACK_NUMBER', '0')
        audio['tracknumber'] = str(track)
        
        disc = song.get('DISK_NUMBER', '1')
        audio['discnumber'] = str(disc)

        genres = _collect_genres(song)
        if genres:
            audio['genre'] = genres

        release_date = _get_release_date(song)
        if release_date:
            audio['date'] = release_date

        audio.save()

        # Write cover art
        if "ALB_PICTURE" in song:
            try:
                pic_data = _download_picture(song["ALB_PICTURE"])
                if pic_data:
                    img = Image.open(io.BytesIO(pic_data))
                    img = img.resize((750, 750), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=90, optimize=True, progressive=False)
                    pic_data = buf.getvalue()

                    id3 = ID3(output_file)
                    id3.add(APIC(
                        encoding=3, # UTF-8
                        mime='image/jpeg',
                        type=3, # cover front
                        desc='Cover (Front)',
                        data=pic_data
                    ))
                    id3.save()
            except Exception as pic_err:
                print(f"Could not add cover art to fallback MP3: {pic_err}")

    except Exception as e:
        print(f"Error tagging fallback MP3: {e}")


def _collect_genres(song: dict) -> list:
    genres = []
    # From song
    for g in song.get("GENRES", []):
        if "name" in g:
            genres.append(g["name"])
    # From album data
    if not genres and album_data_global:
        for g in album_data_global.get("GENRES", []):
            if "name" in g:
                genres.append(g["name"])
    # From API
    if not genres and "ALB_ID" in song:
        try:
            r = requests.get(f"https://api.deezer.com/album/{song['ALB_ID']}")
            if r.ok:
                for g in r.json().get("genres", {}).get("data", []):
                    if "name" in g:
                        genres.append(g["name"])
        except Exception:
            pass
    # Flatten semicolons, deduplicate
    final = []
    for g in genres:
        for part in g.split(";"):
            part = part.strip()
            if part and part not in final:
                final.append(part)
    return final


def _get_release_date(song: dict) -> str | None:
    for src in [song, album_data_global or {}]:
        for key in ["ORIGINAL_RELEASE_DATE", "PHYSICAL_RELEASE_DATE"]:
            val = src.get(key)
            if val:
                return val
    return None


def _get_label(song: dict) -> str | None:
    # Try API first
    if "ALB_ID" in song:
        try:
            r = requests.get(f"https://api.deezer.com/album/{song['ALB_ID']}")
            if r.ok:
                label = r.json().get("label")
                if label:
                    return label
        except Exception:
            pass
    for src in [song, album_data_global or {}]:
        if "LABEL_NAME" in src:
            return src["LABEL_NAME"]
    return None


def _download_picture(pic_id: str) -> bytes | None:
    if not pic_id:
        return None
    url = f"https://e-cdns-images.dzcdn.net/images/cover/{pic_id}/1200x1200.jpg"
    try:
        r = session.get(url)
        r.raise_for_status()
        return r.content
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
#  Lyrics (LRC)
# ═══════════════════════════════════════════════════════════════

def _update_jwt():
    global session_jwt, _tmp_jwt
    if not session_jwt:
        return
    try:
        payload = _tmp_jwt.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        exp = json.loads(base64.urlsafe_b64decode(payload)).get("exp", 0)
        if exp - int(time.time()) > 60:
            return  # still valid
    except Exception:
        pass
    try:
        r = session_jwt.post(
            "https://auth.deezer.com/login/renew?jo=p&rto=c&i=c",
            headers={"Origin": "https://www.deezer.com", "Referer": "https://www.deezer.com/",
                     "Accept": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        if r.ok:
            new_jwt = r.json().get("jwt")
            if new_jwt:
                session_jwt.cookies.set("jwt", new_jwt, domain="deezer.com")
                session_jwt.cookies.set("jwt-Deezer", new_jwt, domain="deezer.com")
                _tmp_jwt = new_jwt
    except Exception:
        pass


def _download_lrc(track_id, output_file: str):
    if not session_jwt or not download_lrc_enabled:
        return
    _update_jwt()
    query = (
        "query GetLyrics($trackId: String!) {\n"
        "  track(trackId: $trackId) {\n"
        "    lyrics {\n"
        "      synchronizedLines { lrcTimestamp line }\n"
        "      text\n"
        "    }\n"
        "  }\n"
        "}"
    )
    try:
        r = requests.post(
            "https://pipe.deezer.com/api",
            json={"operationName": "GetLyrics", "variables": {"trackId": str(track_id)}, "query": query},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://www.deezer.com",
                "Referer": "https://www.deezer.com/",
                "Authorization": f"Bearer {_tmp_jwt}",
                "User-Agent": USER_AGENT,
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        lyrics = data.get("data", {}).get("track", {}).get("lyrics")
        if not lyrics:
            return
        lines = lyrics.get("synchronizedLines")
        if lines:
            lrc = "\n".join(f"{ln['lrcTimestamp']}{ln['line']}" for ln in lines if ln.get("lrcTimestamp") and ln.get("line") is not None)
        elif lyrics.get("text"):
            lrc = lyrics["text"]
        else:
            return
        lrc_path = os.path.splitext(output_file)[0] + ".lrc"
        with open(lrc_path, "w", encoding="utf-8") as f:
            f.write(lrc)
    except Exception as e:
        print(f"Could not download lyrics for {track_id}: {e}")


# ═══════════════════════════════════════════════════════════════
#  Page scraping helpers
# ═══════════════════════════════════════════════════════════════

class _ScriptExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self._curtag = None

    def handle_starttag(self, tag, attrs):
        self._curtag = tag.lower()

    def handle_data(self, data):
        if self._curtag == "script":
            self.scripts.append(data)

    def handle_endtag(self, tag):
        self._curtag = None


def get_song_infos_from_deezer_website(search_type, song_id):
    """Scrape Deezer website for song/album data."""
    global album_data_global
    url = f"https://www.deezer.com/us/{search_type}/{song_id}"
    resp = session.get(url)
    if resp.status_code == 404:
        raise Exception(f"404 for {url}")
    if "MD5_ORIGIN" not in resp.text:
        raise Exception("Not logged in to Deezer — update your ARL cookie")

    parser = _ScriptExtractor()
    parser.feed(resp.text)
    parser.close()

    songs = []
    for script in parser.scripts:
        m = re.search(r'{"DATA":.*', script)
        if not m:
            continue
        state = json.loads(m.group())
        album_data_global = state.get("DATA")

        if album_data_global and "GENRES" not in album_data_global:
            album_data_global["GENRES"] = []

        data = state.get("DATA", {})
        dtype = data.get("__TYPE__", "")

        if dtype in ("playlist", "album"):
            for s in state.get("SONGS", {}).get("data", []):
                _enrich_song(s, data if dtype == "album" else None)
                songs.append(s)
        elif dtype == "song":
            _enrich_song(data, album_data_global)
            songs.append(data)

    if search_type == TYPE_ALBUM and state.get("DATA"):
        album_data_global = state["DATA"]

    return songs[0] if search_type == TYPE_TRACK else songs


def _enrich_song(song: dict, album_src: dict | None):
    """Copy album metadata into song dict if missing."""
    if not album_src:
        return
    for key in ["ORIGINAL_RELEASE_DATE", "PHYSICAL_RELEASE_DATE", "LABEL_NAME", "GENRES"]:
        if key in album_src and key not in song:
            song[key] = album_src[key]


def get_album_data(album_id) -> dict | None:
    """Fetch album data without modifying global state."""
    try:
        url = f"https://www.deezer.com/us/album/{album_id}"
        resp = session.get(url)
        if resp.status_code == 404:
            return None
        parser = _ScriptExtractor()
        parser.feed(resp.text)
        parser.close()
        for script in parser.scripts:
            m = re.search(r'{"DATA":.*', script)
            if m:
                state = json.loads(m.group())
                if "DATA" in state and state["DATA"].get("__TYPE__") == "album":
                    return state["DATA"]
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════════════
#  Playlists & Favorites
# ═══════════════════════════════════════════════════════════════

def parse_deezer_playlist(playlist_id: str):
    """Return (playlist_name, list_of_songs, img_url) for a Deezer playlist."""
    playlist_id = re.search(r"\d+", playlist_id).group(0)

    csrf_url = "https://www.deezer.com/ajax/gw-light.php?method=deezer.getUserData&input=3&api_version=1.0&api_token="
    csrf = session.post(csrf_url).json()["results"]["checkForm"]

    url = f"https://www.deezer.com/ajax/gw-light.php?method=deezer.pagePlaylist&input=3&api_version=1.0&api_token={csrf}"
    data = {"playlist_id": int(playlist_id), "start": 0, "tab": 0, "header": True, "lang": "en", "nb": 500}
    resp = session.post(url, json=data).json()

    if resp.get("error"):
        raise Exception(f"Deezer API error: {resp['error']}")

    results = resp["results"]
    name = results["DATA"]["TITLE"]
    songs = results["SONGS"]["data"]
    
    pic_id = results.get("DATA", {}).get("PLAYLIST_PICTURE") or results.get("DATA", {}).get("PICTURE")
    if pic_id:
        img_url = f"https://e-cdns-images.dzcdn.net/images/playlist/{pic_id}/250x250.jpg"
    elif songs and songs[0].get("ALB_PICTURE"):
        pic_id = songs[0].get("ALB_PICTURE")
        img_url = f"https://e-cdns-images.dzcdn.net/images/cover/{pic_id}/250x250.jpg"
    else:
        img_url = ""

    print(f"Playlist '{name}': {len(songs)} songs")
    return name, songs, img_url


def get_deezer_favorites(user_id: str) -> list:
    """Get favorite track IDs for a Deezer user."""
    resp = session.get(f"https://api.deezer.com/user/{user_id}/tracks?limit=10000000000")
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise Exception(f"API error: {data['error']}")

    while "next" in data:
        r = session.get(data["next"])
        r.raise_for_status()
        more = r.json()
        data["data"] += more.get("data", [])
        if "next" in more:
            data["next"] = more["next"]
        else:
            del data["next"]

    return [s["id"] for s in data["data"]]
