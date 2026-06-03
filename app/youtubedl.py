"""yt-dlp integration for downloading audio from YouTube and other sites."""
import os
import re
import shutil
from subprocess import Popen, PIPE


def resolve_ytdlp_cmd(ytdlp_cmd: str) -> str:
    """Resolve the yt-dlp command path, falling back to the virtual environment if needed."""
    if ytdlp_cmd != "yt-dlp":
        return ytdlp_cmd
    if shutil.which("yt-dlp"):
        return "yt-dlp"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    win_path = os.path.join(base_dir, "venv", "Scripts", "yt-dlp.exe")
    if os.path.exists(win_path):
        return win_path
    unix_path = os.path.join(base_dir, "venv", "bin", "yt-dlp")
    if os.path.exists(unix_path):
        return unix_path
    return "yt-dlp"


def youtubedl_download(url: str, destination_dir: str, ytdlp_cmd: str = "yt-dlp", proxy: str = None) -> str:
    """
    Download audio from a URL via yt-dlp.

    Returns the absolute path of the downloaded MP3 file.
    Raises YoutubeDLError on failure.
    """
    resolved_cmd = resolve_ytdlp_cmd(ytdlp_cmd)
    cmd = [resolved_cmd]
    if proxy:
        cmd.extend(["--proxy", proxy])
    cmd.extend([
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--embed-metadata",
        "--no-embed-chapters",
        "-o", f"{destination_dir}/%(title)s.%(ext)s",
        url
    ])

    print(f"Executing: {' '.join(cmd)}")
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    p.wait()
    stdout, stderr = p.communicate()
    stdout_str = stdout.decode("utf-8", errors="ignore")
    stderr_str = stderr.decode("utf-8", errors="ignore")

    if p.returncode != 0:
        raise YoutubeDLError(f"yt-dlp failed:\n{stderr_str}")

    # Extract output filename
    match = re.search(r'Destination:\s(.*mp3)', stdout_str)
    if not match:
        # Try alternative pattern for already-converted files
        match = re.search(r'\[ExtractAudio\].*Destination:\s*(.*)', stdout_str)
    if not match:
        raise YoutubeDLError(f"Could not determine output file.\nstdout: {stdout_str}")

    return match.group(1).strip()


class YoutubeDLError(Exception):
    pass
