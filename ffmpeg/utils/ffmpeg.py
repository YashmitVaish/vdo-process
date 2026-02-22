import subprocess
import json
import numpy as np
from scipy.signal import correlate
import wave

from ..config import (
    TARGET_FPS,
    TARGET_HEIGHT,
    TARGET_LUFS,
    TARGET_SAMPLE_RATE,
    TARGET_WIDTH
)

# -------------------------------------------------
# Core Command Runner
# -------------------------------------------------

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


# -------------------------------------------------
# Metadata Extraction
# -------------------------------------------------

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


# -------------------------------------------------
# Signal Statistics (Broadcast Matching)
# -------------------------------------------------

import re

def get_signal_stats(video_path):

    command = [
    "ffmpeg",
    "-t", "5",
    "-i", video_path,
    "-vf", "signalstats,metadata=print",
    "-f", "null",
    "-"
]

    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stderr

    y_avg = []
    y_low = []
    y_high = []

    for line in output.split("\n"):

        if "lavfi.signalstats.YAVG" in line:
            y_avg.append(float(line.split("=")[-1]))

        if "lavfi.signalstats.YLOW" in line:
            y_low.append(float(line.split("=")[-1]))

        if "lavfi.signalstats.YHIGH" in line:
            y_high.append(float(line.split("=")[-1]))

    return {
        "YAVG": sum(y_avg)/len(y_avg) if y_avg else 0,
        "YLOW": sum(y_low)/len(y_low) if y_low else 0,
        "YHIGH": sum(y_high)/len(y_high) if y_high else 0,
    }

def compute_matching_params(statsA, statsB):

    brightness_shift = (statsB["YAVG"] - statsA["YAVG"]) / 255.0

    # Contrast scaling based on dynamic range
    rangeA = statsA["YHIGH"] - statsA["YLOW"]
    rangeB = statsB["YHIGH"] - statsB["YLOW"]

    contrast_scale = (rangeB / rangeA) if rangeA != 0 else 1.0

    # Keep correction safe
    contrast_scale = max(0.8, min(1.2, contrast_scale))

    return {
        "brightness": brightness_shift * 0.7,
        "contrast": contrast_scale
    }

def apply_broadcast_match(videoA, videoB, output_path):

    print("Analyzing source video...")
    statsA = get_signal_stats(videoA)

    print("Analyzing reference video...")
    statsB = get_signal_stats(videoB)

    print("Stats A:", statsA)
    print("Stats B:", statsB)

    params = compute_matching_params(statsA, statsB)

    print("Computed Matching Params:", params)

    filter_string = (
        f"[0:v]"
        f"eq=brightness={params['brightness']}:contrast={params['contrast']}"
        f"[v]"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", videoA,
        "-filter_complex", filter_string,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "23",
        "-movflags", "+faststart",
        "-c:a", "copy",
        output_path
    ]

    return run_command(command)


# -------------------------------------------------
# Main Normalization Engine (NO COLOR GRADING HERE)
# -------------------------------------------------

def process_video(input_path, output_path):

    metadata = get_metadata(input_path)
    if not metadata:
        print("Invalid metadata")
        return

    video_stream = None
    audio_stream = None

    for stream in metadata.get("streams", []):
        if stream["codec_type"] == "video":
            video_stream = stream
        elif stream["codec_type"] == "audio":
            audio_stream = stream

    video_filters = []
    audio_filters = []

    # Resolution
    if video_stream:
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        if width != TARGET_WIDTH or height != TARGET_HEIGHT:
            video_filters.append(
                f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2"
            )

        # FPS
        fps_string = video_stream.get("r_frame_rate", "0/0")
        try:
            num, den = fps_string.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0
        except:
            fps = 0

        if round(fps) != TARGET_FPS:
            video_filters.append(f"fps={TARGET_FPS}")

        video_filters.append("format=yuv420p")

    # Audio
    if audio_stream:
        audio_filters.append("afftdn")
        audio_filters.append(f"loudnorm=I={TARGET_LUFS}:LRA=11:TP=-1.5")
        audio_filters.append("alimiter")
        

    command = [
        "ffmpeg",
        "-y",
        "-i", input_path
    ]

    if video_filters:
        command.extend(["-vf", ",".join(video_filters)])

    if audio_filters:
        command.extend(["-af", ",".join(audio_filters)])

    command.extend([
        "-ar", str(TARGET_SAMPLE_RATE),
        "-c:v", "libx264",
        "-profile:v", "main",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "23",
        "-movflags", "+faststart",
        "-c:a", "aac",
        output_path
    ])

    return run_command(command)


# -------------------------------------------------
# Crossfade Merge
# -------------------------------------------------

def merge_videos_with_crossfade(video1, video2, output_path, fade_duration=2, offset=0):
    command = [
        "ffmpeg",
        "-y",
        "-i", video1,
        "-i", video2,
        "-filter_complex",
        (
            f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}:offset={offset}[vout];"
            f"[0:a][1:a]acrossfade=d={fade_duration}:c1=exp:c2=exp[aout]"
        ),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]

    return run_command(command)