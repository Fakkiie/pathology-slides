import os
import sys
import argparse
from datetime import datetime
import shutil

# Set up module paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "conversion")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "barcode")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "ocr")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "labelextract")))

# Imports
from dicom_to_jpeg import convert_dicom_bottom_layer_to_jpeg, convert_jpeg_to_dicom
from svs_to_jpeg import convert_svs_bottom_layer_to_jpeg, jpeg_to_svs
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

original_ext_map = {}
original_name_map = {}

def process_file(image_path, rel_path, output_dir, original_ext=None):
    file_name = os.path.basename(image_path)
    edited_name = f"edited_{file_name}"
    out_path = os.path.join(output_dir, rel_path, edited_name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    shutil.copy(image_path, out_path)

    file_key = f"{rel_path}/{edited_name}"
    overwrite_count[file_key] = overwrite_count.get(file_key, 0) + 1

    try:
        if "barcode" in ENABLED_MODULES:
            print("Barcode removal...")
            out_path = run_barcode(out_path, os.path.dirname(out_path))

        if "label" in ENABLED_MODULES:
            print("Label removal...")
            mask, image_rgb = generate_mask(sam, out_path)
            shape = (image_rgb.shape[0], image_rgb.shape[1])
            find_label_area_from_generated_mask(mask, shape, image_rgb, out_path)

        if "ocr" in ENABLED_MODULES:
            print("OCR...")
            run_ocr_on_image(out_path, os.path.dirname(out_path))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return out_path, f"{timestamp} - {file_key} - Overwritten {overwrite_count[file_key]} times"

    except Exception as e:
        print(f"Error processing {file_key}: {e}")
        return None, None

def run_pipeline():
    logs = []
    image_count = 0
    temp_files = []  # Track all temporary files for cleanup
    print(f"\nScanning '{INPUT_FOLDER}' for DICOM, SVS, and image files...\n")

    for root, _, files in os.walk(INPUT_FOLDER):
        rel_path = os.path.relpath(root, INPUT_FOLDER)
        output_subdir = os.path.join(OUTPUT_FOLDER, rel_path)
        os.makedirs(output_subdir, exist_ok=True)

        for file in files:
            full_path = os.path.join(root, file)
            file_lower = file.lower()
            file_base, file_ext = os.path.splitext(file)

            try:
                if file_lower.endswith(".dcm") or file_lower.endswith(".svs"):
                    # Create unique intermediate filenames
                    temp_jpeg = os.path.join(output_subdir, f"{file_base}_intermediate.jpg")
                    processed_jpeg = os.path.join(output_subdir, f"edited_{file_base}_intermediate.jpg")
                    final_output = os.path.join(output_subdir, file)
                    
                    # Track these files for potential cleanup
                    temp_files.extend([temp_jpeg, processed_jpeg])

                    # Conversion to JPEG
                    if file_lower.endswith(".dcm"):
                        print(f"Converting DICOM: {file}")
                        convert_dicom_bottom_layer_to_jpeg(full_path, temp_jpeg)
                    else:  # SVS
                        print(f"Converting SVS: {file}")
                        convert_svs_bottom_layer_to_jpeg(full_path, temp_jpeg)

                    # Process the JPEG
                    _, log_entry = process_file(temp_jpeg, rel_path, output_subdir)
                    if log_entry:
                        logs.append(log_entry)
                        image_count += 1

                    # Verify processed JPEG exists before conversion back
                    if not os.path.exists(processed_jpeg):
                        raise FileNotFoundError(f"Processed JPEG not found: {processed_jpeg}")

                    # Conversion back to original format
                    if file_lower.endswith(".dcm"):
                        convert_jpeg_to_dicom(processed_jpeg, final_output)
                    else:  # SVS
                        jpeg_to_svs(processed_jpeg, final_output)

                    # Verify final output exists before cleanup
                    if not os.path.exists(final_output):
                        raise FileNotFoundError(f"Final output not created: {final_output}")

                    # Only remove intermediates if final output was successfully created
                    for temp_file in [temp_jpeg, processed_jpeg]:
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                                temp_files.remove(temp_file)
                        except Exception as e:
                            print(f"Warning: Could not remove temporary file {temp_file}: {e}")

                elif file_lower.endswith((".jpg", ".jpeg", ".png")):
                    print(f"Processing raw image: {file}")
                    processed_path = os.path.join(output_subdir, f"edited_{file}")
                    _, log_entry = process_file(full_path, rel_path, output_subdir)
                    if log_entry:
                        logs.append(log_entry)
                        image_count += 1

            except Exception as e:
                print(f"Failed to handle {file}: {e}")
                # Log the error but continue with next file
                continue

    # Final cleanup of any remaining temp files
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            print(f"Warning: Could not remove temporary file {temp_file}: {e}")

    # Save logs
    with open(LOG_FILE, "w") as f:
        for entry in logs:
            f.write(entry + "\n")
    with open(OVERWRITE_FILE, "w") as f:
        for key, count in overwrite_count.items():
            f.write(f"{key} - Overwritten {count} times\n")

    print(f"\nPipeline complete! Processed {image_count} files. Logs saved to 'log/'.")
    
if __name__ == "__main__":
    run_pipeline()
