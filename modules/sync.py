from utils.runner import run_command

def apply_sync_offset(input_path, output_path, offset_seconds):
    command = [
        "ffmpeg",
        "-y",
        "-itsoffset", str(offset_seconds),
        "-i", input_path,
        "-c", "copy",
        output_path
    ]

    return run_command(command)