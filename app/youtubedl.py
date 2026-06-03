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


def download_from_youtube_search(query: str, output_file: str, audio_format: str, config) -> bool:
    """Download audio from a YouTube search query directly to output_file."""
    ytdlp_cmd = config.get("youtubedl", "command", fallback="yt-dlp")
    resolved_cmd = resolve_ytdlp_cmd(ytdlp_cmd)
    proxy = config.get("proxy", "server", fallback="").strip() or None
    
    cmd = [resolved_cmd]
    if proxy:
        cmd.extend(["--proxy", proxy])
    cmd.extend([
        "-x",
        "--audio-format", audio_format,
        "--audio-quality", "0",
        "--no-embed-chapters",
        "--no-playlist",
        "-o", output_file,
        f"ytsearch1:{query}"
    ])
    
    print(f"Executing YouTube fallback: {' '.join(cmd)}")
    try:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        p.wait()
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            return True
        else:
            print(f"yt-dlp search download failed: {stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        print(f"Error executing yt-dlp fallback: {e}")
        return False


def download_from_soulseek_search(query: str, temp_dir: str, audio_format: str, username: str, password: str, sldl_cmd: str) -> bool:
    """Download audio from Soulseek using sldl CLI executable."""
    import shutil
    from subprocess import Popen, PIPE
    
    # Resolve command
    if sldl_cmd == "sldl" and shutil.which("sldl.exe"):
        resolved_cmd = "sldl.exe"
    elif sldl_cmd == "sldl" and shutil.which("sldl"):
        resolved_cmd = "sldl"
    else:
        resolved_cmd = sldl_cmd
        
    cmd = [
        resolved_cmd,
        query,
        "--user", username,
        "--pass", password,
        "--pref-format", audio_format
    ]
    
    print(f"Executing Soulseek fallback: {' '.join(cmd)} inside Cwd: {temp_dir}")
    try:
        p = Popen(cmd, cwd=temp_dir, stdout=PIPE, stderr=PIPE)
        p.wait()
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            return True
        else:
            print(f"sldl failed: {stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        print(f"Error executing sldl: {e}")
        return False
