# Snowsky Echo Mini Downloader

A lightweight, modern web-based audio downloader and tagging utility optimized for the **Snowsky Echo Mini** and other portable music players. Search Deezer, import from YouTube and other sources, and download fully tagged, well-organized music straight to your device, all from a clean browser interface running on your own machine.

---

## Screenshots

**Artist and album search with live download status**

Search by track, album, or artist. Green checkmark badges show what is already on your device, and the playlist below expands to reveal individual tracks with their own download and preview controls.

![Artist search view](screenshots/search-artist-view.png)

**Album browsing with cover art and release years**

Browse an artist's full discography with embedded cover art, release years, and one-click album downloads. Sort results by relevance and toggle between dark and light themes from the top bar.

![Album search view](screenshots/search-album-view.png)

---

## Features

- **Search and Download** — Search songs, albums, or artists directly on Deezer and download high-quality tracks with a single click.
- **Accurate Metadata and Tags** — Automatically retrieves and embeds metadata (title, artist, album, year, track number, disc number, and cover art) for MP3 (ID3v2) and FLAC (Vorbis comments).
- **Synchronized Lyrics** — Optionally fetches and saves synchronized lyrics (`.lrc` files) alongside your tracks.
- **Real-Time Status Synchronization** — Clock badges (queued) and checkmark badges (already downloaded) update in real time next to songs and albums as background download tasks progress.
- **Smart Directory Structuring** — Grouping logic automatically organizes your downloads to match the layout of the Echo Mini:
  - `Albums/<Artist>/<Album Name>/` — forces a single album artist in directory names and tags to prevent album splitting.
  - `Songs/` — single tracks.
  - `Playlists/` — M3U8 playlist compilations.
  - `Youtube-dl/` — video and audio ripped from external sources.
  - `Zips/` — archived albums and playlists.
- **YouTube and URL Importing** — Paste YouTube, SoundCloud, or Vimeo links to download audio instantly using integrated `yt-dlp` resolution.
- **Playlist Downloads** — Supports downloading entire Deezer playlists, Spotify playlists (automatically mapped to Deezer matches), or a user's Deezer Favorites.
- **Search Sorting Controls** — Sort search results by relevance and filter by tracks, albums, or artists.
- **Modern Interface** — A responsive UI with:
  - Sleek dark and light theme toggle.
  - Compact centered and full-width layouts.
  - Compact, standard, and large density display sizing.
  - Graceful drive-disconnection warnings (for example, if your Echo Mini drive `G:\` is unplugged).
- **Automated Fallback Download Pipeline** — If a track is unavailable on Deezer (for example, licensing restrictions on free accounts), the app automatically routes it through fallback channels:
  - **YouTube Music Fallback** — the default fallback that searches YouTube, downloads and extracts the audio, then tags it with full Deezer metadata and cover art.
  - **Soulseek Fallback** (disabled by default) — configurable via settings. When enabled, searches and downloads the track using the `sldl` CLI tool.

---

## Setup and Installation

### 1. Prerequisites

Make sure you have **Python 3.9+** installed and added to your system `PATH`.

### 2. Clone the Repository

```bash
git clone https://github.com/InfiniteAvenger/snowskyechominidownloader.git
cd snowskyechominidownloader
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

1. Copy the template configuration file:
   ```bash
   copy config.example.ini config.ini
   ```
2. Open `config.ini` in a text editor and configure the options below.
3. Set your output drive letter, for example `base = G:\` if your Echo Mini mounts on drive `G`.
4. Retrieve your Deezer **ARL cookie**:
   - Open your web browser and go to [Deezer](https://www.deezer.com).
   - Log into your account.
   - Open Developer Tools (`F12`, or right-click then Inspect).
   - Go to the **Application** or **Storage** tab, then **Cookies**, then `https://www.deezer.com`.
   - Find the cookie named **`arl`** and copy its value.
   - Paste it in `config.ini` under the `[deezer]` section:
     ```ini
     cookie_arl = <your_arl_cookie_here>
     ```

#### Configuration Reference

| Section | Key | Description |
| --- | --- | --- |
| `[download_dirs]` | `base` | Root output directory, typically your Echo Mini drive letter. Subdirectories for songs, albums, playlists, etc. are derived from it. |
| `[http]` | `host`, `port` | Address the local web server binds to. Defaults to `127.0.0.1:5001`. |
| `[proxy]` | `server` | Optional proxy, for example `https://user:pass@host:port` or `socks5://127.0.0.1:9050`. |
| `[threadpool]` | `workers` | Maximum number of parallel downloads. Defaults to `4`. |
| `[deezer]` | `cookie_arl` | Your Deezer ARL cookie (required for Deezer downloads). |
| `[deezer]` | `quality` | `mp3` or `flac`. FLAC requires Deezer Premium. |
| `[deezer]` | `cookie_*` (JWT/refresh) | Optional cookies that enable synchronized `.lrc` lyric downloads. |
| `[youtubedl]` | `command` | Path to the `yt-dlp` executable. If it is on your `PATH`, simply use `yt-dlp`. |

### 5. Soulseek Fallback Setup (Optional)

To use Soulseek fallbacks when Deezer downloads fail:

1. Open the web interface settings (gear icon).
2. Toggle on **Enable Soulseek fallback**.
3. Enter your Soulseek **username** and **password** (credentials are saved locally in `settings.json` and kept out of Git).
4. Make sure the `sldl` CLI executable is on your system `PATH`, or specify its location in **sldl Command / Path**.

---

## Usage

1. Double-click **`run.bat`** (or run `python run.py` in your terminal).
2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5001
   ```
3. Use the tabs to get started:
   - **Search** — find tracks, albums, and artists on Deezer.
   - **YouTube** — paste a YouTube, SoundCloud, or Vimeo link to import audio.
   - **Playlists** — download Deezer or Spotify playlists, or your Deezer Favorites.
   - **Queue** — watch active and pending downloads progress in real time.

Downloads run as background jobs, so you can keep searching and queuing while files are written to your device.

---

## Project Structure

```
SnowskyEchoFileDownloader/
├── app/                  Application package (server, routes, download logic)
├── screenshots/          Interface screenshots used in this README
├── config.example.ini    Configuration template (copy to config.ini)
├── requirements.txt      Python dependencies
├── run.py                Entry point
└── run.bat               Windows launcher
```

---

## Notes

- `config.ini` and `settings.json` hold your personal credentials and are kept out of version control. Never commit them.
- FLAC downloads and synchronized lyrics require a Deezer Premium account and the corresponding cookies.
- This tool is intended for personal use with content you are entitled to access.

---

## Acknowledgments

This project drew inspiration from [Alexeido/deezer2EchoMini](https://github.com/Alexeido/deezer2EchoMini) and began as a loose fork of it, growing into a distinct project with additional features and a more polished interface. Thanks to the original author for the groundwork.
