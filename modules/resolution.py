from config import TARGET_WIDTH, TARGET_HEIGHT
from utils.runner import run_command

def normalize_resolution(input_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf",
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "copy",
        output_path
    ]

    return run_command(command)