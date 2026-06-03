"""yt-dlp integration for downloading audio from YouTube and other sites."""
import re
from shlex import quote
from subprocess import Popen, PIPE


def youtubedl_download(url: str, destination_dir: str, ytdlp_cmd: str = "yt-dlp", proxy: str = None) -> str:
    """
    Download audio from a URL via yt-dlp.

    Returns the absolute path of the downloaded MP3 file.
    Raises YoutubeDLError on failure.
    """
    proxy_flag = f' --proxy {proxy}' if proxy else ""
    cmd = (
        f'{ytdlp_cmd}{proxy_flag}'
        f' -x --audio-format mp3 --audio-quality 0'
        f' --embed-metadata --no-embed-chapters'
        f" -o \"{destination_dir}/%(title)s.%(ext)s\""
        f' {quote(url)}'
    )

    print(f"Executing: {cmd}")
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    p.wait()
    stdout, stderr = p.communicate()
    stdout_str = stdout.decode()
    stderr_str = stderr.decode()

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
