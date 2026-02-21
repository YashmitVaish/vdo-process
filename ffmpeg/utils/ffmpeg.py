import subprocess
import json
from config import TARGET_FPS,TARGET_HEIGHT,TARGET_LUFS,TARGET_SAMPLE_RATE,TARGET_WIDTH

# -------------------------
# Core Command Runner
# -------------------------

def run_command(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("FFmpeg Error:")
        print(result.stderr)
    else:
        print("Command executed successfully")

    return result


# -------------------------
# Metadata Extraction
# -------------------------

def get_metadata(video_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        video_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if not result.stdout:
        return None

    return json.loads(result.stdout)


# -------------------------
# Resolution Normalization
# -------------------------

def normalize_resolution(input_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf",
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "copy",
        output_path
    ]

    return run_command(command)


# -------------------------
# Audio Normalization
# -------------------------

def normalize_audio(input_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-af", f"loudnorm=I={TARGET_LUFS}:LRA=11:TP=-1.5",
        "-ar", str(TARGET_SAMPLE_RATE),
        "-c:v", "copy",
        output_path
    ]

    return run_command(command)


# -------------------------
# Frame Rate Normalization
# -------------------------

def normalize_fps(input_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf", f"fps={TARGET_FPS}",
        "-c:a", "copy",
        output_path
    ]

    return run_command(command)


# -------------------------
# Sync Offset
# -------------------------

def apply_sync_offset(input_path, output_path, offset):
    command = [
        "ffmpeg",
        "-y",
        "-itsoffset", str(offset),
        "-i", input_path,
        "-c", "copy",
        output_path
    ]

    return run_command(command) 

def analyze(metadata):
    video_stream = None
    audio_stream = None

    for stream in metadata.get("streams", []):
        if stream["codec_type"] == "video":
            video_stream = stream
        elif stream["codec_type"] == "audio":
            audio_stream = stream

    analysis = {
        "resolution": False,
        "audio": False,
        "fps": False
    }

    if video_stream:
        width = int(video_stream["width"])
        height = int(video_stream["height"])

        if width != TARGET_WIDTH or height != TARGET_HEIGHT:
            analysis["resolution"] = True

        if video_stream.get("r_frame_rate") != f"{TARGET_FPS}/1":
            analysis["fps"] = True

    if audio_stream:
        analysis["audio"] = True

    return analysis