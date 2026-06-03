# Snowsky Echo Mini Downloader

A lightweight, modern web-based audio downloader and tagging utility optimized for the **Snowsky Echo Mini** and other portable music players.

---

## Features

- **Search & Download**: Search songs, albums, or artists directly on Deezer. Download high-quality tracks with single clicks.
- **Accurate Metadata & Tags**: Automatically retrieves and embeds metadata (Title, Artist, Album, Year, Track number, Disc number, and embedded Cover Art) for MP3 (ID3v2) and FLAC (Vorbis comments).
- **Synchronized Lyrics**: Automatically fetches and saves synchronized lyrics (`.lrc` files) alongside your tracks.
- **Real-Time Status Synchronization**: Clock badges (queued) and checkmark badges (already downloaded) update in real-time next to songs and albums as background download tasks progress.
- **Smart Directory Structuring**: Grouping logic automatically organizes your downloads to match the layout of the Echo Mini:
  - `Albums/<Artist>/<Album Name>/` (Forces a single album artist in directory names and tags to prevent album splitting).
  - `Songs/` (Single tracks).
  - `Playlists/` (M3U8 playlist compilations).
  - `Youtube-dl/` (Video/audio ripped from external sources).
  - `Zips/` (Archived albums/playlists).
- **YouTube & URL Importing**: Paste YouTube, SoundCloud, or Vimeo links to download audio instantly using integrated `yt-dlp` resolution.
- **Playlist Downloads**: Supports downloading entire Deezer playlists, Spotify playlists (automatically mapped to Deezer matches), or a user's Deezer Favorites.
- **Modern Interface**: responsive UI with:
  - Sleek Dark / Light theme toggle.
  - Compact Centered / Full-width layouts.
  - Compact, Standard, and Large density display sizing.
  - Graceful drive-disconnection warnings (e.g. if your Echo Mini drive `G:\` is unplugged).
- **Automated Fallback Download Pipeline**: If a track is unavailable on Deezer (e.g. licensing restrictions for Free accounts), the app automatically routes it through fallback channels:
  - **Soulseek Fallback** (disabled by default): Configurable via settings. If enabled, searches and downloads the track using the `sldl` CLI tool.
  - **YouTube Music Fallback**: Default fallback that searches YouTube, downloads and extracts the audio, and tags it with full Deezer metadata and cover art.

---

## Setup & Installation

### 1. Prerequisites
Make sure you have Python 3.9+ installed and added to your system environment variables (`PATH`).

### 2. Clone the Repository
```bash
git clone https://github.com/InfiniteAvenger/snowskyechominidownloader.git
cd snowskyechominidownloader
```

### 3. Install Dependencies
Install Python requirements:
```bash
pip install -r requirements.txt
```

### 4. Configuration
1. Copy the template configuration file:
   ```bash
   copy config.example.ini config.ini
   ```
2. Open `config.ini` in a text editor.
3. Configure your drive letter (e.g. `base = G:\` if your Echo Mini mounts on drive `G`).
4. Retrieve your Deezer **ARL Cookie**:
   - Open your web browser and go to [Deezer](https://www.deezer.com).
   - Log into your account.
   - Open Developer Tools (`F12` or right-click -> Inspect).
   - Go to the **Application** or **Storage** tab -> **Cookies** -> `https://www.deezer.com`.
   - Find the cookie named **`arl`** and copy its value.
   - Paste it in `config.ini` under the `[deezer]` section:
     ```ini
     cookie_arl = <your_arl_cookie_here>
     ```

### 5. Soulseek Fallback Setup (Optional)
To use Soulseek fallbacks when Deezer downloads fail:
1. Open the web interface settings (gear icon).
2. Toggle on **Enable Soulseek fallback**.
3. Input your Soulseek **Username** and **Password** (credentials are saved locally in `settings.json` and kept out of Git).
4. Make sure you have the `sldl` CLI executable on your system path, or specify the custom path in **sldl Command / Path**.

---

## Usage

1. Double-click **`run.bat`** (or execute `python run.py` in your terminal).
2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5001
   ```
3. Search for music or import URLs to begin downloading background jobs!
