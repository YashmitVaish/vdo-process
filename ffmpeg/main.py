import os
from .utils.ffmpeg import (
    process_video,
    merge_videos_with_crossfade,
    match_color
)

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
    OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    video1 = os.path.join(SAMPLES_DIR, "Test3.mp4")
    video2 = os.path.join(SAMPLES_DIR, "Test4.mp4")

    normalized1 = os.path.join(OUTPUTS_DIR, "norm1.mp4")
    normalized2 = os.path.join(OUTPUTS_DIR, "norm2.mp4")

    color_matched = os.path.join(OUTPUTS_DIR, "color_matched.mp4")
    final_output = os.path.join(OUTPUTS_DIR, "merged_output.mp4")

    # -------------------------------------------------
    # Step 1: Normalize Both Videos
    # -------------------------------------------------

    print("Normalizing first video...")
    process_video(video1, normalized1)

    print("Normalizing second video...")
    process_video(video2, normalized2)

    # -------------------------------------------------
    # Step 2: Match Color of Video1 to Video2
    # -------------------------------------------------

    print("Applying color matching...")
    match_color(normalized1, normalized2, color_matched)

    # -------------------------------------------------
    # Step 3: Merge with Smooth Audio Crossfade
    # -------------------------------------------------

    print("Merging with smooth audio crossfade...")
    merge_videos_with_crossfade(color_matched, normalized2, final_output, fade_duration=2)

    print("Done.")
    print("Final file:", final_output)


if __name__ == "__main__":
    main()