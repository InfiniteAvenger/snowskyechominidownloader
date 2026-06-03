#!/usr/bin/env python3
"""SnowskyEchoFileDownloader - Launch the web app."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import load_config
from app.web import create_app

def main():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    config = load_config(config_path)

    app = create_app(config)

    host = config.get("http", "host", fallback="127.0.0.1")
    port = config.getint("http", "port", fallback=5000)

    print(f"\n  SnowskyEchoFileDownloader")
    print(f"  Running at http://{host}:{port}")
    print(f"  Output directory: {config['download_dirs']['base']}\n")

    from waitress import serve
    serve(app, host=host, port=port)

if __name__ == "__main__":
    main()
