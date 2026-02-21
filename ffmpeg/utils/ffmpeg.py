import subprocess
import json
import numpy as np
from scipy.signal import correlate
import wave
import contextlib

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
# Extract Audio for Sync Detection
# -------------------------------------------------

def extract_audio_wav(input_path, output_wav):
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-ac", "1",
        "-ar", "44100",
        "-acodec", "pcm_s16le",
        output_wav
    ]
    run_command(command)


# -------------------------------------------------
# Audio Cross-Correlation Sync
# -------------------------------------------------

def compute_audio_offset(file1, file2):
    extract_audio_wav(file1, "temp1.wav")
    extract_audio_wav(file2, "temp2.wav")

    with wave.open("temp1.wav", "rb") as w1:
        data1 = np.frombuffer(w1.readframes(w1.getnframes()), dtype=np.int16)

    with wave.open("temp2.wav", "rb") as w2:
        data2 = np.frombuffer(w2.readframes(w2.getnframes()), dtype=np.int16)

    correlation = correlate(data1, data2, mode='full')
    lag = correlation.argmax() - (len(data2) - 1)

    sample_rate = 44100
    offset_seconds = lag / sample_rate

    print(f"Detected sync offset: {offset_seconds:.3f} sec")

    return offset_seconds


# -------------------------------------------------
# Apply Sync Offset
# -------------------------------------------------

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


# -------------------------------------------------
# Main Adaptive Harmonization Engine
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

    # -------------------------
    # Resolution + Aspect Ratio
    # -------------------------
    if video_stream:
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        if width != TARGET_WIDTH or height != TARGET_HEIGHT:
            video_filters.append(
                f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2"
            )

        # FPS Sync
        fps_string = video_stream.get("r_frame_rate", "0/0")
        try:
            num, den = fps_string.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0
        except:
            fps = 0

        if round(fps) != TARGET_FPS:
            video_filters.append(f"fps={TARGET_FPS}")

        # Pixel format
        video_filters.append("format=yuv420p")

        # Brightness Harmonization
        video_filters.append("eq=brightness=0.02:contrast=1.05")

    # -------------------------
    # Audio Harmonization
    # -------------------------
    if audio_stream:
        video_duration = float(video_stream.get("duration", 0))
        audio_duration = float(audio_stream.get("duration", 0))

        if abs(video_duration - audio_duration) > 0.2:
            print("⚠ Potential A/V sync mismatch detected")

        audio_filters.append(
            f"loudnorm=I={TARGET_LUFS}:LRA=11:TP=-1.5"
        )

        audio_filters.append("alimiter")
        audio_filters.append("afftdn")

    # -------------------------
    # Build Final FFmpeg Command
    # -------------------------

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
        "-preset", "medium",
        "-crf", "23",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:v", "4M",
        output_path
    ])

    return run_command(command)
def merge_videos_with_crossfade(video1, video2, output_path, fade_duration=2):
    """
    Smoothly merges two videos with audio crossfade transition.
    fade_duration = seconds of audio crossfade
    """

    # Step 1: Get duration of first video
    metadata1 = get_metadata(video1)
    if not metadata1:
        print("Error reading metadata of first video")
        return

    video_stream1 = None
    for stream in metadata1.get("streams", []):
        if stream["codec_type"] == "video":
            video_stream1 = stream
            break

    duration1 = float(video_stream1.get("duration", 0))

    # Crossfade should start fade_duration seconds before video1 ends
    offset = duration1 - fade_duration

    command = [
        "ffmpeg",
        "-y",
        "-i", video1,
        "-i", video2,
        "-filter_complex",
        (
            f"[0:a][1:a]acrossfade=d={fade_duration}:c1=exp:c2=exp[aout];"
            f"[0:v][1:v]concat=n=2:v=1:a=0[vout]"
        ),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        "-movflags", "+faststart",
        output_path
    ]

    return run_command(command)

# -------------------------------------------------
# Color Matching Between Two Videos
# -------------------------------------------------

def match_color(videoA, videoB, output_path):

    command = [
        "ffmpeg",
        "-y",
        "-i", videoA,
        "-filter_complex",
        (
            "[0:v]"
            "zscale=transfer=bt709:matrix=bt709:primaries=bt709,"
            "histeq=strength=0.25:intensity=0.4,"
            "colorlevels=rimin=0.05:gimin=0.05:bimin=0.05:"
            "rimax=0.95:gimax=0.95:bimax=0.95,"
            "colorbalance=rs=0.01:gs=0.00:bs=-0.01"
            "[v]"
        ),
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        "-movflags", "+faststart",
        "-c:a", "copy",
        output_path
    ]

    return run_command(command)