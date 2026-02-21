import os
from .utils.ffmpeg import (
    process_video,
    apply_broadcast_match,
    merge_videos_with_crossfade
)

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
    OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    # Input videos
    video1 = os.path.join(SAMPLES_DIR, "test1.mp4")
    video2 = os.path.join(SAMPLES_DIR, "test2.mp4")

    # Intermediate files
    normalized1 = os.path.join(OUTPUTS_DIR, "norm1.mp4")
    normalized2 = os.path.join(OUTPUTS_DIR, "norm2.mp4")
    matched_video = os.path.join(OUTPUTS_DIR, "matched.mp4")

    # Final output
    final_output = os.path.join(OUTPUTS_DIR, "merged_output.mp4")

    # -------------------------------------------------
    # Step 1: Normalize Both Videos
    # -------------------------------------------------

    print("Normalizing first video...")
    process_video(video1, normalized1)

    print("Normalizing second video...")
    process_video(video2, normalized2)

    # -------------------------------------------------
    # Step 2: Apply Broadcast Matching
    # -------------------------------------------------

    print("Applying broadcast matching (Video1 → Video2)...")
    apply_broadcast_match(normalized1, normalized2, matched_video)

    # -------------------------------------------------
    # Step 3: Merge With Audio Crossfade
    # -------------------------------------------------

    print("Merging with smooth audio crossfade...")
    merge_videos_with_crossfade(matched_video, normalized2, final_output, fade_duration=2)

    print("\nDone.")
    print("Final file:", final_output)


if __name__ == "__main__":
    main()