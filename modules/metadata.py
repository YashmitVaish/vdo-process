import json
import subprocess

def get_metadata(video_path):
    command = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        video_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    return json.loads(result.stdout)