"""Configuration loader for SnowskyEchoFileDownloader."""
import os
import sys
from configparser import ConfigParser


def load_config(config_path: str) -> ConfigParser:
    """Load and validate the config file."""
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    config = ConfigParser()
    config.read(config_path)

    # Ensure required sections exist
    required = ["download_dirs", "http", "deezer", "youtubedl"]
    for section in required:
        if section not in config:
            print(f"Missing config section: [{section}]")
            sys.exit(1)

    # Allow env var overrides for Deezer cookies
    env_map = {
        "DEEZER_COOKIE_ARL": "cookie_arl",
        "DEEZER_COOKIE_FIXED_JWT": "cookie_fixed_jwt",
        "DEEZER_COOKIE_REFRESH_TOKEN_D": "cookie_refresh_token_D",
        "DEEZER_COOKIE_REFRESH_TOKEN": "cookie_refresh_token",
    }
    for env_var, config_key in env_map.items():
        if env_var in os.environ:
            config["deezer"][config_key] = os.environ[env_var]

    # Load settings.json if exists to override base download dir
    import json
    settings_path = os.path.join(os.path.dirname(config_path), "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                new_dir = settings.get("output_dir", "").strip()
                if new_dir:
                    config["download_dirs"]["base"] = new_dir
                    config["download_dirs"]["songs"] = os.path.join(new_dir, "Songs")
                    config["download_dirs"]["albums"] = os.path.join(new_dir, "Albums")
                    config["download_dirs"]["playlists"] = os.path.join(new_dir, "Playlists")
                    config["download_dirs"]["youtubedl"] = os.path.join(new_dir, "Youtube-dl")
                    config["download_dirs"]["zips"] = os.path.join(new_dir, "Zips")
        except Exception as e:
            print(f"WARNING: Could not load settings.json: {e}")

    # Create download directories
    for key in ["songs", "albums", "playlists", "youtubedl", "zips"]:
        if key in config["download_dirs"]:
            try:
                os.makedirs(config["download_dirs"][key], exist_ok=True)
            except Exception as e:
                print(f"WARNING: Could not create directory {config['download_dirs'][key]}: {e}")

    return config
