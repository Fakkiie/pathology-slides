import os
import sys
import argparse
from datetime import datetime

# Set up module paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "conversion")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "barcode")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "ocr")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "labelextract")))

# Imports
from dicom_to_jpeg import convert_dicom_bottom_layer_to_jpeg
from svs_to_jpeg import convert_svs_bottom_layer_to_jpeg
from barcode import process_image as run_barcode
from ocr import run_ocr_on_image
from model import load_model
from mask_generator import generate_mask
from utils import find_label_area_from_generated_mask

# CLI args
parser = argparse.ArgumentParser(description="Pathology Slide Processor")
parser.add_argument("--input", required=True, help="Folder with .dcm/.svs/.jpg input images")
parser.add_argument("--output", required=True, help="Folder to save processed results")
parser.add_argument("--modules", required=True, help="Comma-separated modules: ocr,barcode,label")
args = parser.parse_args()

INPUT_FOLDER = args.input
OUTPUT_FOLDER = args.output
ENABLED_MODULES = [m.strip().lower() for m in args.modules.split(",")]

# Logging
LOG_FOLDER = "log/"
os.makedirs(LOG_FOLDER, exist_ok=True)
LOG_FILE = os.path.join(LOG_FOLDER, "log.txt")
OVERWRITE_FILE = os.path.join(LOG_FOLDER, "overwrite_counts.txt")
open(LOG_FILE, "w").close()

overwrite_count = {}
if os.path.exists(OVERWRITE_FILE) and os.stat(OVERWRITE_FILE).st_size > 0:
    with open(OVERWRITE_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(" - Overwritten ")
            if len(parts) == 2:
                key = parts[0]
                try:
                    count = int(parts[1].split(" times")[0])
                    overwrite_count[key] = count
                except:
                    continue

# Load SAM model if needed
sam, device = None, None
if "label" in ENABLED_MODULES:
    print("Loading SAM model for label removal...")
    checkpoint = os.path.join("modules", "labelextract", "sam_vit_h_4b8939.pth")
    sam, device = load_model(checkpoint)

def process_file(image_path, rel_path, output_dir):
    file_name = os.path.basename(image_path)
    out_path = os.path.join(output_dir, rel_path, f"edited_{os.path.splitext(file_name)[0]}.jpg")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    file_key = f"{rel_path}/edited_{file_name}"
    overwrite_count[file_key] = overwrite_count.get(file_key, 0) + 1

    try:
        if "barcode" in ENABLED_MODULES:
            print("Barcode removal...")
            out_path = run_barcode(image_path, os.path.dirname(out_path))

        if "label" in ENABLED_MODULES:
            print("Label removal...")
            mask, image_rgb = generate_mask(sam, out_path)
            shape = (image_rgb.shape[0], image_rgb.shape[1])
            find_label_area_from_generated_mask(mask, shape, image_rgb, out_path)

        if "ocr" in ENABLED_MODULES:
            print("OCR...")
            run_ocr_on_image(out_path, os.path.dirname(out_path))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} - {file_key} - Overwritten {overwrite_count[file_key]} times"

    except Exception as e:
        print(f"Error processing {file_key}: {e}")
        return None

def run_pipeline():
    logs = []
    image_count = 0

    print(f"\nScanning '{INPUT_FOLDER}' for DICOM, SVS, and image files...\n")
    for root, _, files in os.walk(INPUT_FOLDER):
        rel_path = os.path.relpath(root, INPUT_FOLDER)
        for file in files:
            full_path = os.path.join(root, file)
            ext = file.lower()

            try:
                if ext.endswith(".dcm") or ext.endswith(".svs"):
                    # Convert and process
                    print(f"Converting: {file}")
                    os.makedirs(os.path.join(OUTPUT_FOLDER, rel_path), exist_ok=True)
                    out_jpeg = os.path.join(OUTPUT_FOLDER, rel_path, os.path.splitext(file)[0] + ".jpg")

                    if ext.endswith(".dcm"):
                        convert_dicom_bottom_layer_to_jpeg(full_path, out_jpeg)
                    elif ext.endswith(".svs"):
                        convert_svs_bottom_layer_to_jpeg(full_path, out_jpeg)

                    log_entry = process_file(out_jpeg, rel_path, OUTPUT_FOLDER)
                    if log_entry:
                        logs.append(log_entry)
                        image_count += 1

                elif ext.endswith((".jpg", ".jpeg", ".png")):
                    print(f"Raw image: {file}")
                    log_entry = process_file(full_path, rel_path, OUTPUT_FOLDER)
                    if log_entry:
                        logs.append(log_entry)
                        image_count += 1
            except Exception as e:
                print(f"Failed to handle {file}: {e}")

    with open(LOG_FILE, "w") as f:
        for entry in logs:
            f.write(entry + "\n")
    with open(OVERWRITE_FILE, "w") as f:
        for key, count in overwrite_count.items():
            f.write(f"{key} - Overwritten {count} times\n")

    print(f"\nPipeline complete! Processed {image_count} files. Logs saved to 'log/'.")

if __name__ == "__main__":
    run_pipeline()
