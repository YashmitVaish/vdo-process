import os
from modules.metadata import get_metadata
from modules.analyzer import analyze
from modules.resolution import normalize_resolution
from modules.audio import normalize_audio

INPUT_VIDEO = "samples/test1.mp4"
TEMP_VIDEO = "outputs/temp.mp4"
FINAL_VIDEO = "outputs/final.mp4"

os.makedirs("outputs", exist_ok=True)

print("Extracting metadata...")
metadata = get_metadata(INPUT_VIDEO)

print("Metadata raw output:")
print(metadata)

print("Analyzing video...")
analysis = analyze(metadata)

current_file = INPUT_VIDEO

if analysis["needs_resolution_fix"]:
    print("Applying resolution normalization...")
    normalize_resolution(current_file, TEMP_VIDEO)
    current_file = TEMP_VIDEO

if analysis["needs_audio_fix"]:
    print("Applying audio normalization...")
    normalize_audio(current_file, FINAL_VIDEO)
    current_file = FINAL_VIDEO

print("Processing complete.")
print("Final output:", current_file)