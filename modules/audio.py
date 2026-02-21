from config import TARGET_LUFS
from utils.runner import run_command

def normalize_audio(input_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-af", f"loudnorm=I={TARGET_LUFS}:LRA=11:TP=-1.5",
        "-c:v", "copy",
        output_path
    ]

    return run_command(command)