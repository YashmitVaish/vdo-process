from config import TARGET_WIDTH, TARGET_HEIGHT, TARGET_LUFS

def analyze(metadata):
    video_stream = None
    audio_stream = None

    for stream in metadata["streams"]:
        if stream["codec_type"] == "video":
            video_stream = stream
        elif stream["codec_type"] == "audio":
            audio_stream = stream

    analysis = {
        "needs_resolution_fix": False,
        "needs_audio_fix": False
    }

    if video_stream:
        width = int(video_stream["width"])
        height = int(video_stream["height"])

        if width != TARGET_WIDTH or height != TARGET_HEIGHT:
            analysis["needs_resolution_fix"] = True

    # Loudness detection would require external analysis
    # For hackathon MVP, assume audio needs normalization
    if audio_stream:
        analysis["needs_audio_fix"] = True

    return analysis