import subprocess
import threading
import json
import time
from uuid import uuid4
from datetime import datetime, timezone
from backend.utils.mongo import streams_col

from backend.utils.redis_client import redis_client
# ---------------------------------------------------------------------------
# Config — import from your config.py
# ---------------------------------------------------------------------------
from ffmpeg.config import (
    TARGET_WIDTH,
    TARGET_HEIGHT,
    TARGET_FPS,
    TARGET_LUFS,
    TARGET_SAMPLE_RATE,
)

MEDIAMTX_RTMP_BASE = "rtmp://localhost:1935/live"
ACTIVE_STREAMS: dict[str, dict] = {}
import os
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

def _redis_key(stream_id: str) -> str:
    return f"stream:{stream_id}"


def _set_redis(stream_id: str, fields: dict):
    redis_client.hset(_redis_key(stream_id), mapping=fields)


def _get_metadata_live(rtsp_url: str) -> dict | None:
    is_rtsp = rtsp_url.startswith("rtsp://")

    command = ["ffprobe", "-v", "quiet"]

    if is_rtsp:
        command.extend(["-rtsp_transport", "tcp"])

    command.extend([
        "-analyzeduration", "10000000",
        "-probesize", "10000000",
        "-print_format", "json",
        "-show_streams",
        rtsp_url,
    ])

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if not result.stdout or result.stdout.strip() == "":
            # ffprobe returned nothing — source is unreachable
            return None
        data = json.loads(result.stdout)
        # Accept partial results — even if video params are missing,
        # we still know there's a video stream from codec_type
        if not data.get("streams"):
            return None
        return data
    except subprocess.TimeoutExpired:
        print(f"[stream_manager] ffprobe timed out for {rtsp_url}")
        return None
    except Exception as e:
        print(f"[stream_manager] ffprobe failed: {e}")
        return None
    
def _build_ffmpeg_command(input_url: str, rtmp_url: str, has_audio: bool) -> list[str]:
    video_filters = [
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:flags=lanczos:force_original_aspect_ratio=decrease",
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        f"fps={TARGET_FPS}",
        "format=yuv420p",
    ]

    audio_filters = [
        "afftdn",
        f"loudnorm=I={TARGET_LUFS}:LRA=11:TP=-1.5",
        "alimiter",
    ] if has_audio else []

    is_rtsp = input_url.startswith("rtsp://")

    # Input section — no filter flags here
    cmd = ["ffmpeg", "-y"]

    if is_rtsp:
        cmd.extend(["-rtsp_transport", "tcp"])

    cmd.extend([
        "-fflags", "nobuffer+genpts",
        "-flags", "low_delay",
        "-analyzeduration", "10000000",
        "-probesize", "10000000",
        "-i", input_url,   # -i MUST come before any output flags
    ])

    # Output section — filters go here, after -i
    cmd.extend(["-vf", ",".join(video_filters)])

    if audio_filters:
        cmd.extend(["-af", ",".join(audio_filters)])

    cmd.extend([
        "-c:v", "libx264",
        "-profile:v", "high",          # changed from "main" — webcam outputs High 4:2:2
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-crf", "23",
        "-c:a", "aac",
        "-ar", str(TARGET_SAMPLE_RATE),
        "-f", "flv",
        rtmp_url,
    ])

    return cmd

def _monitor_process(stream_id: str):
    """
    Runs in a thread. Watches the FFmpeg process and updates Redis/Mongo
    when the stream ends (camera disconnect, network drop, explicit stop).
    Also handles reconnection if the stream drops unexpectedly.
    """
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 5  # seconds between reconnect attempts

    entry = ACTIVE_STREAMS.get(stream_id)
    if not entry:
        return

    attempts = 0

    while True:
        proc = entry["process"]
        return_code = proc.wait()  # blocks until FFmpeg exits

        # Check if we were asked to stop
        current_status = redis_client.hget(_redis_key(stream_id), "status")
        if isinstance(current_status, bytes):
            current_status = current_status.decode()

        if current_status == "stopped" or stream_id not in ACTIVE_STREAMS:
            print(f"[stream_manager] Stream {stream_id} stopped cleanly.")
            break

        # Unexpected exit — attempt reconnect
        attempts += 1
        if attempts > MAX_RECONNECT_ATTEMPTS:
            print(f"[stream_manager] Stream {stream_id} exceeded reconnect attempts. Giving up.")
            _set_redis(stream_id, {"status": "failed", "error": "Max reconnect attempts exceeded"})
            streams_col.update_one(
                {"_id": stream_id},
                {"$set": {"status": "failed", "updated_at": datetime.now(timezone.utc)}}
            )
            ACTIVE_STREAMS.pop(stream_id, None)
            break

        print(f"[stream_manager] Stream {stream_id} exited (code {return_code}). "
              f"Reconnecting in {RECONNECT_DELAY}s (attempt {attempts}/{MAX_RECONNECT_ATTEMPTS})...")

        _set_redis(stream_id, {"status": "reconnecting", "reconnect_attempt": attempts})
        time.sleep(RECONNECT_DELAY)

        # Restart FFmpeg
        rtsp_url = entry["rtsp_url"]
        rtmp_url = entry["rtmp_url"]
        has_audio = entry.get("has_audio", True)
        cmd = _build_ffmpeg_command(rtsp_url, rtmp_url, has_audio)

        try:
            log_file = open(f"logs/{stream_id}.log", "w")

            new_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=log_file,  # capture stderr for debugging
            )
            entry["process"] = new_proc
            _set_redis(stream_id, {"status": "live", "reconnect_attempt": attempts})
            print(f"[stream_manager] Stream {stream_id} reconnected.")
        except Exception as e:
            print(f"[stream_manager] Failed to restart FFmpeg for {stream_id}: {e}")
            _set_redis(stream_id, {"status": "failed", "error": str(e)})
            ACTIVE_STREAMS.pop(stream_id, None)
            break


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_stream(rtsp_url: str, stream_id: str | None = None) -> dict:
    """
    Start a live RTSP → normalize → RTMP stream.

    Returns a dict with stream_id, rtmp_url, status.
    Raises RuntimeError if the RTSP source can't be probed.
    """
    stream_id = stream_id or str(uuid4())
    rtmp_url = f"{MEDIAMTX_RTMP_BASE}/{stream_id}"

    # Probe the source
    print(f"[stream_manager] Probing {rtsp_url}...")
    metadata = _get_metadata_live(rtsp_url)
    if not metadata:
        raise RuntimeError(f"Could not probe RTSP source: {rtsp_url}")

    has_video = any(s["codec_type"] == "video" for s in metadata.get("streams", []))
    has_audio = any(s["codec_type"] == "audio" for s in metadata.get("streams", []))

    if not has_video:
        raise RuntimeError("RTSP source has no video stream.")

    # Build and launch FFmpeg
    cmd = _build_ffmpeg_command(rtsp_url, rtmp_url, has_audio)
    print(f"[stream_manager] Starting FFmpeg for stream {stream_id}")

    log_file = open(f"logs/{stream_id}.log", "w")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=log_file,   # write to file instead of PIPE
    )

    now = datetime.now(timezone.utc)

    entry = {
        "process": proc,
        "rtsp_url": rtsp_url,
        "rtmp_url": rtmp_url,
        "has_audio": has_audio,
    }
    ACTIVE_STREAMS[stream_id] = entry

    # Persist to Redis
    _set_redis(stream_id, {
        "stream_id": stream_id,
        "status": "live",
        "rtsp_url": rtsp_url,
        "rtmp_url": rtmp_url,
        "has_audio": int(has_audio),
        "started_at": now.isoformat(),
        "reconnect_attempt": 0,
    })

    # Persist to Mongo
    streams_col.insert_one({
        "_id": stream_id,
        "stream_id": stream_id,
        "rtsp_url": rtsp_url,
        "rtmp_url": rtmp_url,
        "status": "live",
        "has_audio": has_audio,
        "created_at": now,
        "updated_at": now,
    })

    # Start monitor thread
    thread = threading.Thread(target=_monitor_process, args=(stream_id,), daemon=True)
    entry["thread"] = thread
    thread.start()

    return {
        "stream_id": stream_id,
        "rtmp_url": rtmp_url,
        "hls_preview": f"http://localhost:8888/{stream_id}/index.m3u8",
        "status": "live",
    }


def stop_stream(stream_id: str) -> dict:
    """
    Gracefully stop a running stream.
    """
    entry = ACTIVE_STREAMS.get(stream_id)
    if not entry:
        raise RuntimeError(f"Stream {stream_id} not found in active streams.")

    # Mark as stopped in Redis BEFORE killing process
    # so the monitor thread doesn't try to reconnect
    _set_redis(stream_id, {"status": "stopped"})

    proc = entry["process"]
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

    ACTIVE_STREAMS.pop(stream_id, None)

    streams_col.update_one(
        {"_id": stream_id},
        {"$set": {"status": "stopped", "updated_at": datetime.now(timezone.utc)}}
    )

    return {"stream_id": stream_id, "status": "stopped"}


def get_stream_status(stream_id: str) -> dict | None:
    """
    Get current stream status from Redis.
    """
    data = redis_client.hgetall(_redis_key(stream_id))
    if not data:
        return None
    return {
        k.decode() if isinstance(k, bytes) else k:
        v.decode() if isinstance(v, bytes) else v
        for k, v in data.items()
    }


def list_active_streams() -> list[str]:
    return list(ACTIVE_STREAMS.keys())