import os
import shutil
from datetime import datetime
import sys

# Add barcode module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "barcode")))
from barcode import process_image  # Import function to process images

# Define paths
IMAGES_FOLDER = "images/"
OUTPUT_FOLDER = "outputimages/"
LOG_FOLDER = "log/"
LOG_FILE = os.path.join(LOG_FOLDER, "log.txt")
OVERWRITE_FILE = os.path.join(LOG_FOLDER, "overwrite_counts.txt")

# Ensure folders exist
os.makedirs(IMAGES_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Clear log file
open(LOG_FILE, "w").close()
print("Cleared previous log.txt")

# Load overwrite counts from file
overwrite_count = {}
if os.path.exists(OVERWRITE_FILE) and os.stat(OVERWRITE_FILE).st_size > 0:
    print(f"Loading overwrite counts from {OVERWRITE_FILE}...")
    with open(OVERWRITE_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(" - Overwritten ")
            if len(parts) == 2:
                file_key = parts[0]
                try:
                    count = int(parts[1].split(" times")[0])
                    overwrite_count[file_key] = count
                    print(f"   ➕ {file_key}: {count}x")
                except ValueError:
                    print(f"   ⚠️ Skipped bad line: {line.strip()}")

def copy_and_process_images():
    """Processes and copies images, logs overwrite counts and file changes."""
    found_files = False
    new_logs = []

    print(f"\nScanning '{IMAGES_FOLDER}' for images...\n")
    for root, _, files in os.walk(IMAGES_FOLDER):
        subfolder_name = os.path.relpath(root, IMAGES_FOLDER)
        if subfolder_name == ".":
            subfolder_name = ""
        output_subdir = os.path.join(OUTPUT_FOLDER, subfolder_name)
        os.makedirs(output_subdir, exist_ok=True)

        for filename in files:
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                found_files = True
                source_path = os.path.join(root, filename)
                new_filename = f"edited_{filename}"
                destination_path = os.path.join(output_subdir, new_filename)
                file_key = f"{subfolder_name}/{new_filename}"
                overwrite_count[file_key] = overwrite_count.get(file_key, 0) + 1

                print(f"Processing: {file_key} | Count: {overwrite_count[file_key]}")
                try:
                    processed_image_path = process_image(source_path, output_subdir)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"{timestamp} - {file_key} - Overwritten {overwrite_count[file_key]} times"
                    new_logs.append(log_entry)
                    print(f"Saved to: {processed_image_path}")
                except Exception as e:
                    print(f"Failed to process: {file_key} | Reason: {e}")

    if found_files:
        print("\n Writing logs...")
        with open(LOG_FILE, "w") as f:
            for entry in new_logs:
                f.write(entry + "\n")
                print(f"{entry}")

        with open(OVERWRITE_FILE, "w") as f:
            for file_key, count in overwrite_count.items():
                line = f"{file_key} - Overwritten {count} times"
                f.write(line + "\n")

        print(f"\n Done! Logs saved to '{LOG_FILE}' and overwrite counts to '{OVERWRITE_FILE}'")
    else:
        print("No images found to process.")

# Run the pipeline
copy_and_process_images()
