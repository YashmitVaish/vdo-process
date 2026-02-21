import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

INPUT_VIDEO = os.path.join(PROJECT_ROOT, "samples", "test1.mp4")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

INPUT_VIDEO = os.path.join(PROJECT_ROOT, "samples", "test1.mp4")
TEMP1 = os.path.join(PROJECT_ROOT, "outputs", "temp1.mp4")
TEMP2 = os.path.join(PROJECT_ROOT, "outputs", "temp2.mp4")
FINAL = os.path.join(PROJECT_ROOT, "outputs", "final.mp4")

os.makedirs(os.path.join(PROJECT_ROOT, "outputs"), exist_ok=True)

print("Extracting metadata...")
metadata = get_metadata(INPUT_VIDEO)

print("Analyzing...")
analysis = analyze(metadata)

current = INPUT_VIDEO

if analysis["resolution"]:
    print("Fixing resolution...")
    normalize_resolution(current, TEMP1)
    current = TEMP1

if analysis["fps"]:
    print("Fixing FPS...")
    normalize_fps(current, TEMP2)
    current = TEMP2

if analysis["audio"]:
    print("Fixing audio...")
    normalize_audio(current, FINAL)
    current = FINAL

print("Processing complete.")
print("Final file:", current)