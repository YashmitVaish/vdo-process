import os
from utils.ffmpeg import process_video, merge_videos_with_crossfade

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
    OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    video1 = os.path.join(SAMPLES_DIR, "test1.mp4") 
    video2 = os.path.join(SAMPLES_DIR, "test2.mp4")
    
    normalized1 = os.path.join(OUTPUTS_DIR, "norm1.mp4")
    normalized2 = os.path.join(OUTPUTS_DIR, "norm2.mp4")

    final_output = os.path.join(OUTPUTS_DIR, "merged_output.mp4")

    print("Normalizing first video...")
    process_video(video1, normalized1)

    print("Normalizing second video...")
    process_video(video2, normalized2)

    print("Merging with smooth audio crossfade...")
    merge_videos_with_crossfade(normalized1, normalized2, final_output, fade_duration=2)

    print("Done.")
    print("Final file:", final_output)

if __name__ == "__main__":
    main()