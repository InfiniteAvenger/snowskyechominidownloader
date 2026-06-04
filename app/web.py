"""Flask web application."""
import atexit
from flask import Flask, render_template, request, jsonify
from markupsafe import escape

from app.deezer import init_deezer_session, deezer_search
from app.queue import TaskQueue
from app.downloader import (
    download_track, download_album, download_playlist,
    download_spotify_playlist, download_favorites,
    download_youtube, create_zip,
)


def create_app(config) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["APP_CONFIG"] = config

    # Load settings.json on boot to sync properties
    import json
    import os
    from app import deezer as deezer_mod
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    settings_path = os.path.join(root_dir, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                deezer_mod.download_lrc_enabled = settings.get("download_lrc", True)
        except Exception:
            pass

    # Init systems
    queue = TaskQueue(workers=config.getint("threadpool", "workers", fallback=4))
    init_deezer_session(config)

    # Setup album cache
    from app.downloader import album_cache
    album_cache.setup(config["download_dirs"]["albums"])

    @atexit.register
    def shutdown():
        queue.shutdown()

    # ── Pages ──

    @app.route("/")
    def index():
        return render_template("index.html")

    # ── Search ──

    @app.route("/api/search", methods=["POST"])
    def search():
        data = request.get_json(force=True)
        query = data.get("query", "").strip()
        search_type = data.get("type", "track")
        if not query:
            return jsonify({"error": "Empty query"}), 400
        results = deezer_search(query, search_type)
        
        # Get active tasks in the queue
        active_queued_items = set()
        with queue._lock:
            for t in queue._tasks:
                if t.state in ("queued", "active"):
                    m_id = t.music_id
                    m_type = t.music_type
                    if m_id and m_type:
                        active_queued_items.add((str(m_id), str(m_type)))

        # Annotate results with downloaded status
        from app.downloader import album_cache
        for item in results:
            artist = item.get("artist", "")
            album = item.get("album", "")
            if artist and album:
                item["downloaded"] = album_cache.is_downloaded(artist, album)
            else:
                item["downloaded"] = False

            # Check if enqueued
            item_id = str(item.get("id") or "")
            item_type = item.get("id_type", "track")
            album_id = str(item.get("album_id") or "")
            
            is_in_queue = (item_id, item_type) in active_queued_items
            if not is_in_queue and item_type == "track" and album_id:
                is_in_queue = (album_id, "album") in active_queued_items
                
            item["in_queue"] = is_in_queue
                
        return jsonify(results)

    # ── Downloads ──

    @app.route("/api/download", methods=["POST"])
    def api_download():
        data = request.get_json(force=True)
        dtype = data.get("type")
        music_id = data.get("music_id")
        make_zip = data.get("create_zip", False)
        title = data.get("title", "")
        artist = data.get("artist", "")
        img_url = data.get("img_url", "")

        if dtype == "track":
            desc = f"Downloading track: {title}"
            task = queue.enqueue(
                desc,
                download_track,
                title=title, artist=artist, img_url=img_url,
                music_id=str(music_id), music_type="track",
                track_id=int(music_id), config=config, queue=queue,
            )
        elif dtype == "album":
            desc = f"Downloading album: {title}"
            def album_job():
                files = download_album(int(music_id), config, queue)
                if make_zip and files:
                    return create_zip(files, config)
                return files
            task = queue.enqueue(
                desc,
                album_job,
                title=title, artist=artist, img_url=img_url,
                music_id=str(music_id), music_type="album"
            )
        else:
            return jsonify({"error": "Invalid type"}), 400

        return jsonify({"task_id": task.id})

    @app.route("/api/youtube", methods=["POST"])
    def api_youtube():
        data = request.get_json(force=True)
        url = data.get("url", "").strip()
        if not url or not url.startswith("http"):
            return jsonify({"error": "Invalid URL"}), 400
        task = queue.enqueue("Downloading via yt-dlp", download_youtube, url=url, config=config, queue=queue, source="youtube")
        return jsonify({"task_id": task.id})

    @app.route("/api/playlist/deezer", methods=["POST"])
    def api_deezer_playlist():
        data = request.get_json(force=True)
        pid = data.get("playlist_url", "").strip()
        make_zip = data.get("create_zip", False)
        if not pid:
            return jsonify({"error": "Empty playlist URL"}), 400

        def job():
            files = download_playlist(pid, config, queue)
            if make_zip and files:
                return create_zip(files, config)
            return files

        task = queue.enqueue("Downloading Deezer playlist", job)
        return jsonify({"task_id": task.id})

    @app.route("/api/playlist/spotify", methods=["POST"])
    def api_spotify_playlist():
        data = request.get_json(force=True)
        name = data.get("playlist_name", "").strip()
        url = data.get("playlist_url", "").strip()
        make_zip = data.get("create_zip", False)
        if not url:
            return jsonify({"error": "Empty playlist URL"}), 400

        def job():
            files = download_spotify_playlist(name or "spotify", url, config, queue)
            if make_zip and files:
                return create_zip(files, config)
            return files

        task = queue.enqueue("Downloading Spotify playlist", job)
        return jsonify({"task_id": task.id})

    @app.route("/api/favorites", methods=["POST"])
    def api_favorites():
        data = request.get_json(force=True)
        uid = data.get("user_id", "").strip()
        make_zip = data.get("create_zip", False)
        if not uid or not uid.isnumeric():
            return jsonify({"error": "Invalid user ID"}), 400

        def job():
            files = download_favorites(uid, config, queue)
            if make_zip and files:
                return create_zip(files, config)
            return files

        task = queue.enqueue("Downloading Deezer favorites", job)
        return jsonify({"task_id": task.id})

    # ── Queue ──

    @app.route("/api/queue")
    def api_queue():
        return jsonify(queue.all_tasks())

    @app.route("/api/queue/clear", methods=["POST"])
    def clear_queue():
        queue.clear_completed()
        return jsonify({"status": "ok"})

    @app.route("/api/queue/retry", methods=["POST"])
    def retry_queue_task():
        data = request.get_json(force=True)
        task_id = int(data.get("task_id", 0))
        success = queue.retry_task(task_id)
        return jsonify({"status": "ok" if success else "error"})

    @app.route("/api/health")
    def api_health():
        from app.deezer import check_arl_health
        return jsonify(check_arl_health())

    # ── Settings ──

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        import json
        import os
        import shutil
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        settings_path = os.path.join(root_dir, "settings.json")
        settings = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception:
                pass

        # Check free disk space
        base_dir = config["download_dirs"]["base"]
        free_space_str = "Unknown"
        if os.path.exists(base_dir):
            try:
                total, used, free = shutil.disk_usage(base_dir)
                free_space_str = f"{free / (1024**3):.1f} GB free"
            except Exception:
                pass
        else:
            free_space_str = "Invalid path / Disconnected"

        return jsonify({
            "output_dir": config["download_dirs"]["base"],
            "quality": config.get("deezer", "quality", fallback="mp3"),
            "layout_mode": settings.get("layout_mode", "compact"),
            "auto_redirect_queue": settings.get("auto_redirect_queue", False),
            "item_size": settings.get("item_size", "standard"),
            "download_lrc": settings.get("download_lrc", True),
            "free_space": free_space_str,
            "soulseek_enabled": settings.get("soulseek_enabled", False),
            "soulseek_username": settings.get("soulseek_username", ""),
            "soulseek_password": settings.get("soulseek_password", ""),
            "sldl_command": settings.get("sldl_command", "sldl")
        })

    @app.route("/api/settings", methods=["POST"])
    def update_settings():
        import os
        import json
        import app.deezer
        data = request.get_json(force=True)
        new_dir = data.get("output_dir", "").strip()
        layout_mode = data.get("layout_mode", "compact")
        auto_redirect_queue = data.get("auto_redirect_queue", False)
        item_size = data.get("item_size", "standard")
        download_lrc = data.get("download_lrc", True)

        soulseek_enabled = data.get("soulseek_enabled", False)
        soulseek_username = data.get("soulseek_username", "").strip()
        soulseek_password = data.get("soulseek_password", "").strip()
        sldl_command = data.get("sldl_command", "sldl").strip()

        app.deezer.download_lrc_enabled = download_lrc

        if new_dir:
            config["download_dirs"]["base"] = new_dir
            # Rebuild sub-dirs
            config["download_dirs"]["songs"] = os.path.join(new_dir, "Songs")
            config["download_dirs"]["albums"] = os.path.join(new_dir, "Albums")
            config["download_dirs"]["playlists"] = os.path.join(new_dir, "Playlists")
            config["download_dirs"]["youtubedl"] = os.path.join(new_dir, "Youtube-dl")
            config["download_dirs"]["zips"] = os.path.join(new_dir, "Zips")
            for key in ["songs", "albums", "playlists", "youtubedl", "zips"]:
                os.makedirs(config["download_dirs"][key], exist_ok=True)
            
            from app.downloader import album_cache
            album_cache.update_dir(config["download_dirs"]["albums"])
            
        # Save all to settings.json
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        settings_path = os.path.join(root_dir, "settings.json")
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump({
                    "output_dir": config["download_dirs"]["base"],
                    "layout_mode": layout_mode,
                    "auto_redirect_queue": auto_redirect_queue,
                    "item_size": item_size,
                    "download_lrc": download_lrc,
                    "soulseek_enabled": soulseek_enabled,
                    "soulseek_username": soulseek_username,
                    "soulseek_password": soulseek_password,
                    "sldl_command": sldl_command
                }, f, indent=2)
        except Exception as e:
            print(f"WARNING: Could not save settings.json: {e}")

        return jsonify({"status": "ok"})

    return app
