"""Download orchestration - ties Deezer/YouTube to the file system and task queue."""
import os
import platform
from os.path import basename
from zipfile import ZipFile, ZIP_DEFLATED

from app.deezer import (
    TYPE_TRACK, TYPE_ALBUM, TYPE_PLAYLIST,
    get_song_infos_from_deezer_website, download_song, get_file_extension,
    parse_deezer_playlist, get_deezer_favorites, get_album_data,
    deezer_search,
)
from app.youtubedl import youtubedl_download


# Cache album artist lookups
_album_artist_cache = {}


def clean_filename(name: str) -> str:
    """Remove characters invalid on Windows/Linux filesystems."""
    name = name.replace("\t", " ")
    if any(platform.win32_ver()):
        name = name.replace('"', "'")
        bad = '<>:"/\\|?*'
    else:
        bad = '/:"?'
    return "".join(c for c in name if c not in bad)


import threading

class AlbumCache:
    def __init__(self):
        self.albums_dir = None
        self._cache = set()
        self._lock = threading.Lock()
        self._initialized = False

    def setup(self, albums_dir):
        with self._lock:
            self.albums_dir = albums_dir
            self._initialized = False

    def update_dir(self, albums_dir):
        with self._lock:
            self.albums_dir = albums_dir
            self._initialized = False

    def initialize(self):
        with self._lock:
            if self._initialized:
                return
            self._scan()
            self._initialized = True

    def _scan(self):
        downloaded = set()
        if not self.albums_dir or not os.path.exists(self.albums_dir):
            self._cache = downloaded
            return
        try:
            for artist_entry in os.scandir(self.albums_dir):
                if artist_entry.is_dir():
                    for album_entry in os.scandir(artist_entry.path):
                        if album_entry.is_dir():
                            artist_name = artist_entry.name.lower().strip()
                            album_name = album_entry.name.lower().strip()
                            downloaded.add((artist_name, album_name))
        except Exception as e:
            print(f"Error scanning albums directory: {e}")
        self._cache = downloaded

    def is_downloaded(self, artist: str, album: str) -> bool:
        if not self._initialized:
            self.initialize()
        clean_artist = clean_filename(artist).lower().strip()
        clean_album = clean_filename(album).lower().strip()
        with self._lock:
            return (clean_artist, clean_album) in self._cache

    def add(self, artist: str, album: str):
        if not self._initialized:
            self.initialize()
        clean_artist = clean_filename(artist).lower().strip()
        clean_album = clean_filename(album).lower().strip()
        with self._lock:
            self._cache.add((clean_artist, clean_album))


album_cache = AlbumCache()


def _song_filename(song: dict) -> str:
    ext = get_file_extension()
    track_num = None
    try:
        raw = song.get("TRACK_NUMBER", "")
        if str(raw).strip():
            track_num = int(raw)
    except Exception:
        pass

    title = song.get("SNG_TITLE", "Unknown")
    if track_num and track_num > 0:
        return clean_filename(f"{track_num:02d} - {title}.{ext}")
    return clean_filename(f"{title}.{ext}")


def download_track(track_id: int, config, queue=None):
    """Download a single track to Songs/."""
    song = get_song_infos_from_deezer_website(TYPE_TRACK, track_id)
    filename = _song_filename(song)
    out = os.path.join(config["download_dirs"]["songs"], filename)
    if not os.path.exists(out):
        download_song(song, out)
    else:
        print(f"Skipping (exists): {out}")
    return out


def download_album(album_id: int, config, queue=None):
    """Download an album to Albums/Artist/AlbumTitle/."""
    songs = get_song_infos_from_deezer_website(TYPE_ALBUM, album_id)
    if songs and queue:
        first_song = songs[0]
        album_title = first_song.get("ALB_TITLE", "Unknown Album")
        artist_name = first_song.get("ART_NAME", "Unknown Artist")
        pic_id = first_song.get("ALB_PICTURE")
        img_url = f"https://e-cdns-images.dzcdn.net/images/cover/{pic_id}/250x250.jpg" if pic_id else ""
        queue.update_metadata(title=album_title, artist=artist_name, img_url=img_url)

    downloaded = []
    for i, song in enumerate(songs):
        if queue:
            track_title = song.get("SNG_TITLE", "Unknown Track")
            queue.report_progress(i, len(songs), f"Downloading: {track_title}")
        try:
            # Determine artist (prefer album artist over track artist)
            aid = song.get("ALB_ID")
            artist = song.get("ART_NAME", "Unknown Artist")
            if aid:
                cached = _album_artist_cache.get(aid)
                if cached:
                    artist = cached
                else:
                    try:
                        info = get_album_data(aid)
                        if info and info.get("ART_NAME"):
                            artist = info["ART_NAME"]
                            _album_artist_cache[aid] = artist
                    except Exception:
                        pass

            album_title = song.get("ALB_TITLE", "Unknown Album")
            album_dir = os.path.join(
                config["download_dirs"]["albums"],
                clean_filename(artist),
                clean_filename(album_title),
            )
            os.makedirs(album_dir, exist_ok=True)

            filename = _song_filename(song)
            out = os.path.join(album_dir, filename)
            if not os.path.exists(out):
                # Force album artist in metadata
                song_copy = dict(song)
                song_copy["ART_NAME"] = artist
                download_song(song_copy, out)
            downloaded.append(out)
        except Exception as e:
            print(f"Warning: {e}")

    if downloaded and songs:
        first_song = songs[0]
        aid = first_song.get("ALB_ID")
        resolved_artist = first_song.get("ART_NAME", "Unknown Artist")
        if aid and _album_artist_cache.get(aid):
            resolved_artist = _album_artist_cache[aid]
        album_title_str = first_song.get("ALB_TITLE", "Unknown Album")
        album_cache.add(resolved_artist, album_title_str)

    return downloaded


def download_playlist(playlist_id: str, config, queue=None):
    """Download a Deezer playlist to Playlists/PlaylistName/."""
    name, songs, img_url = parse_deezer_playlist(playlist_id)
    playlist_dir = os.path.join(config["download_dirs"]["playlists"], clean_filename(name))
    os.makedirs(playlist_dir, exist_ok=True)

    if queue:
        queue.update_metadata(title=name, artist="Deezer Playlist", img_url=img_url, description=f"Downloading playlist: {name}")

    downloaded = []
    for i, song in enumerate(songs):
        if queue:
            track_title = song.get("SNG_TITLE", "Unknown Track")
            queue.report_progress(i, len(songs), f"Downloading: {track_title}")
        try:
            filename = _song_filename(song)
            out = os.path.join(playlist_dir, filename)
            if not os.path.exists(out):
                download_song(song, out)
            downloaded.append(out)
        except Exception as e:
            print(f"Warning: {e}")

    # Create m3u8
    if downloaded:
        m3u = os.path.join(playlist_dir, f"00 {clean_filename(name)}.m3u8")
        with open(m3u, "w", encoding="utf-8") as f:
            for s in downloaded:
                if os.path.exists(s):
                    f.write(basename(s) + "\n")
    return downloaded


def download_spotify_playlist(playlist_name: str, playlist_url: str, config, queue=None):
    """Download Spotify playlist by searching each song on Deezer."""
    from app.spotify import get_songs_from_spotify_website
    proxy = config.get("proxy", "server", fallback="").strip() or None
    songs = get_songs_from_spotify_website(playlist_url, proxy)
    playlist_dir = os.path.join(config["download_dirs"]["playlists"], clean_filename(playlist_name))
    os.makedirs(playlist_dir, exist_ok=True)

    if queue:
        queue.update_metadata(title=playlist_name, artist="Spotify Playlist", description=f"Downloading Spotify playlist: {playlist_name}")

    downloaded = []
    for i, song_query in enumerate(songs):
        if queue:
            queue.report_progress(i, len(songs), f"Searching: {song_query}")
        try:
            results = deezer_search(song_query, TYPE_TRACK)
            if not results:
                print(f"Not found on Deezer: {song_query}")
                continue
            track_id = results[0]["id"]
            song = get_song_infos_from_deezer_website(TYPE_TRACK, track_id)
            if queue:
                track_title = song.get("SNG_TITLE", "Unknown Track")
                queue.report_progress(i, len(songs), f"Downloading: {track_title}")
                if song.get("ALB_PICTURE"):
                    pic_id = song.get("ALB_PICTURE")
                    s_img = f"https://e-cdns-images.dzcdn.net/images/cover/{pic_id}/250x250.jpg"
                    queue.update_metadata(img_url=s_img)

            filename = _song_filename(song)
            out = os.path.join(playlist_dir, filename)
            if not os.path.exists(out):
                download_song(song, out)
            downloaded.append(out)
        except Exception as e:
            print(f"Warning ({song_query}): {e}")
    return downloaded


def download_favorites(user_id: str, config, queue=None):
    """Download a user's Deezer favorites."""
    fav_ids = get_deezer_favorites(user_id)
    fav_dir = os.path.join(config["download_dirs"]["playlists"], f"favorites_{user_id}")
    os.makedirs(fav_dir, exist_ok=True)

    if queue:
        queue.update_metadata(title=f"Favorites ({user_id})", artist="Deezer Favorites", description=f"Downloading favorites: {user_id}")

    downloaded = []
    for i, tid in enumerate(fav_ids):
        if queue:
            queue.report_progress(i, len(fav_ids), "Fetching next favorite...")
        try:
            song = get_song_infos_from_deezer_website(TYPE_TRACK, tid)
            if queue:
                track_title = song.get("SNG_TITLE", "Unknown Track")
                queue.report_progress(i, len(fav_ids), f"Downloading: {track_title}")
                if song.get("ALB_PICTURE"):
                    pic_id = song.get("ALB_PICTURE")
                    s_img = f"https://e-cdns-images.dzcdn.net/images/cover/{pic_id}/250x250.jpg"
                    queue.update_metadata(img_url=s_img)

            filename = _song_filename(song)
            out = os.path.join(fav_dir, filename)
            if not os.path.exists(out):
                download_song(song, out)
            downloaded.append(out)
        except Exception as e:
            print(f"Warning: {e}")
    return downloaded


def download_youtube(url: str, config, queue=None):
    """Download audio from a URL via yt-dlp."""
    ytdlp_cmd = config.get("youtubedl", "command", fallback="yt-dlp")
    proxy = config.get("proxy", "server", fallback="").strip() or None
    proxy_flag = f' --proxy {proxy}' if proxy else ""

    if queue:
        queue.update_metadata(title="YouTube Video", artist="Fetching metadata...", description="Downloading YouTube Audio")
        try:
            import subprocess
            from shlex import quote
            meta_cmd = f'{ytdlp_cmd}{proxy_flag} --simulate --print "%(title)s\\n%(thumbnail)s\\n%(uploader)s" {quote(url)}'
            p = subprocess.Popen(meta_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = p.communicate()
            if p.returncode == 0:
                lines = [line.strip() for line in stdout.decode("utf-8", errors="ignore").split("\n") if line.strip()]
                if len(lines) >= 3:
                    title, thumbnail, uploader = lines[0], lines[1], lines[2]
                elif len(lines) == 2:
                    title, thumbnail, uploader = lines[0], lines[1], "YouTube"
                elif len(lines) == 1:
                    title, thumbnail, uploader = lines[0], "", "YouTube"
                else:
                    title, thumbnail, uploader = "YouTube Video", "", "YouTube"
                
                queue.update_metadata(title=title, artist=uploader, img_url=thumbnail, description=f"Downloading YouTube: {title}")
        except Exception as e:
            print(f"Warning: {e}")

    dest = config["download_dirs"]["youtubedl"]
    return youtubedl_download(url, dest, ytdlp_cmd, proxy)


def create_zip(files: list, config) -> str:
    """Create a zip file from a list of files."""
    if not files:
        return ""
    parent = basename(os.path.dirname(files[0]))
    zip_path = os.path.join(config["download_dirs"]["zips"], f"{parent}.zip")
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
        for f in files:
            if os.path.exists(f):
                zf.write(f, arcname=os.path.join(parent, basename(f)))
    return zip_path
