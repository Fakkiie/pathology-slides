import os
import sys
from datetime import datetime

# Add label extract module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "labelextract")))
from model import load_model
from mask_generator import generate_mask
from utils import find_label_area_from_generated_mask

# Define paths
IMAGES_FOLDER = "images/"
OUTPUT_FOLDER = "outputimages/"
LOG_FOLDER = "log/"
LOG_FILE = os.path.join(LOG_FOLDER, "label_log.txt")
OVERWRITE_FILE = os.path.join(LOG_FOLDER, "label_overwrite_counts.txt")
CHECKPOINT_PATH = os.path.join("modules", "labelextract", "sam_vit_h_4b8939.pth")

# Ensure folders exist
os.makedirs(IMAGES_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Clear log file
open(LOG_FILE, "w").close()

# Load overwrite counts from file
overwrite_count = {}
if os.path.exists(OVERWRITE_FILE) and os.stat(OVERWRITE_FILE).st_size > 0:
    print("Loading existing overwrite counts...")
    with open(OVERWRITE_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(" - Overwritten ")
            if len(parts) == 2:
                file_key = parts[0]
                try:
                    count = int(parts[1].split(" times")[0])
                    overwrite_count[file_key] = count
                except ValueError:
                    print(f"Failed to parse overwrite count from: {line.strip()}")

# Load segmentation model
print("Loading SAM model...")
sam, device = load_model(CHECKPOINT_PATH)
print("Model loaded.")

def copy_and_process_images():
    """Processes and copies images for label removal using SAM segmentation model."""
    found_files = False
    new_logs = []

    print(f"\n Scanning '{IMAGES_FOLDER}' for images...\n")
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

                print(f"Processing: {file_key}")
                try:
                    # Step 1: Generate mask
                    print("Generating mask...")
                    output_mask, image_rgb = generate_mask(sam, source_path)

                    # Step 2: Get shape
                    image_shape = (image_rgb.shape[0], image_rgb.shape[1])

                    # Step 3: Find + erase label
                    print("Removing label area and saving result...")
                    area = find_label_area_from_generated_mask(output_mask, image_shape, image_rgb, destination_path)

                    if area is not None:
                        print(f"Saved to {destination_path}")
                    else:
                        print(f"No label found. Image saved as-is.")

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"{timestamp} - {file_key} - Overwritten {overwrite_count[file_key]} times"
                    new_logs.append(log_entry)

                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    if found_files:
        print("\n Writing logs...")
        with open(LOG_FILE, "w") as f:
            for entry in new_logs:
                f.write(entry + "\n")

        with open(OVERWRITE_FILE, "w") as f:
            for file_key, count in overwrite_count.items():
                f.write(f"{file_key} - Overwritten {count} times\n")

        print("Logs written successfully.")
    else:
        print("No image files found to process.")

# Run the pipeline
if __name__ == "__main__":
    copy_and_process_images()
