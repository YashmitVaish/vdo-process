from utils.config import *

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