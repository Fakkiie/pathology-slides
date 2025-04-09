import os
import sys
import argparse
from datetime import datetime
import shutil
import glob
import cv2
import pydicom
from pydicom.uid import ExplicitVRLittleEndian
import numpy as np

# Set up module paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "conversion")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "barcode")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "ocr")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "modules", "labelextract")))

# Imports
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

def convert_dicom_bottom_layer_to_jpeg(input_dicom_path, output_jpeg_path=None):
    """Convert DICOM to JPEG and return both pixel array and original DICOM data"""
    try:
        ds = pydicom.dcmread(input_dicom_path, force=True)
        
        # Handle missing metadata
        if not hasattr(ds, 'file_meta'):
            ds.file_meta = pydicom.dataset.FileMetaDataset()
            ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        
        pixel_array = ds.pixel_array
        if pixel_array.ndim == 3:  # For multi-frame DICOMs
            pixel_array = pixel_array[-1]  # Get bottom layer

        # Normalize to 8-bit
        if pixel_array.dtype != np.uint8:
            pixel_array = cv2.normalize(pixel_array, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        if output_jpeg_path:
            cv2.imwrite(output_jpeg_path, pixel_array)
            
        return pixel_array, ds
        
    except Exception as e:
        print(f"DICOM to JPEG conversion error: {e}")
        raise

def convert_jpeg_to_dicom(processed_image, output_dicom_path, original_ds):
    """Convert processed image array back to DICOM format"""
    try:
        # Create new dataset from original
        new_ds = original_ds.copy()
        
        # Update with processed pixel data
        new_ds.PixelData = processed_image.tobytes()
        new_ds.Rows, new_ds.Columns = processed_image.shape
        
        # Ensure proper DICOM metadata
        new_ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        new_ds.SamplesPerPixel = 1
        new_ds.PhotometricInterpretation = "MONOCHROME2"
        new_ds.BitsAllocated = 8
        new_ds.BitsStored = 8
        new_ds.HighBit = 7
        new_ds.PixelRepresentation = 0

        # Save the modified DICOM
        new_ds.save_as(output_dicom_path)
        print(f"Saved modified DICOM to {output_dicom_path}")
        
    except Exception as e:
        print(f"JPEG to DICOM conversion error: {e}")
        raise

def clean_jpeg_files(folder):
    """Remove all temporary JPEG files from the output folder"""
    jpeg_files = glob.glob(os.path.join(folder, '**/*.jp*g'), recursive=True)
    removed_count = 0
    for jpeg_file in jpeg_files:
        try:
            if any(x in os.path.basename(jpeg_file) for x in ['_temp', '_intermediate', 'edited_']):
                os.remove(jpeg_file)
                removed_count += 1
        except Exception as e:
            print(f"Error removing {jpeg_file}: {e}")
    return removed_count

def process_file(image_path, rel_path, output_dir):
    """Process an image file through enabled modules"""
    file_name = os.path.basename(image_path)
    edited_name = f"edited_{file_name}"
    out_path = os.path.join(output_dir, rel_path, edited_name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    shutil.copy(image_path, out_path)

    try:
        if "barcode" in ENABLED_MODULES:
            print("Barcode removal...")
            out_path = run_barcode(out_path, os.path.dirname(out_path))
        
        if "label" in ENABLED_MODULES and sam:
            print("Label removal...")
            mask, image_rgb = generate_mask(sam, out_path)
            shape = (image_rgb.shape[0], image_rgb.shape[1])
            find_label_area_from_generated_mask(mask, shape, image_rgb, out_path)
        
        if "ocr" in ENABLED_MODULES:
            print("OCR...")
            run_ocr_on_image(out_path, os.path.dirname(out_path))
            
        return out_path
    except Exception as e:
        print(f"Error processing {out_path}: {e}")
        return None

def run_pipeline():
    logs = []
    image_count = 0
    temp_files = set()

    print(f"\nScanning '{INPUT_FOLDER}' for DICOM, SVS, and image files...\n")

    for root, _, files in os.walk(INPUT_FOLDER):
        rel_path = os.path.relpath(root, INPUT_FOLDER)
        output_subdir = os.path.join(OUTPUT_FOLDER, rel_path)
        os.makedirs(output_subdir, exist_ok=True)

        for file in files:
            if file.lower() == '.ds_store':
                continue
                
            full_path = os.path.join(root, file)
            file_lower = file.lower()
            file_base = os.path.splitext(file)[0]

            try:
                if file_lower.endswith(".dcm"):
                    # DICOM processing pipeline
                    temp_jpeg = os.path.join(output_subdir, f"{file_base}_temp.jpg")
                    processed_jpeg = os.path.join(output_subdir, f"processed_{file_base}.jpg")
                    final_output = os.path.join(output_subdir, file)
                    
                    # Convert DICOM to JPEG
                    pixel_array, original_ds = convert_dicom_bottom_layer_to_jpeg(full_path, temp_jpeg)
                    temp_files.add(temp_jpeg)
                    
                    # Process the JPEG
                    processed_path = process_file(temp_jpeg, rel_path, output_subdir)
                    if processed_path and os.path.exists(processed_path):
                        temp_files.add(processed_path)
                        # Read the processed image
                        modified_img = cv2.imread(processed_path, cv2.IMREAD_GRAYSCALE)
                        
                        # Convert back to DICOM using the MODIFIED image
                        convert_jpeg_to_dicom(modified_img, final_output, original_ds)
                        image_count += 1
                    
                elif file_lower.endswith(".svs"):
                    # SVS processing pipeline
                    temp_jpeg = os.path.join(output_subdir, f"{file_base}_temp.jpg")
                    processed_jpeg = os.path.join(output_subdir, f"processed_{file_base}.jpg")
                    final_output = os.path.join(output_subdir, file)
                    
                    convert_svs_bottom_layer_to_jpeg(full_path, temp_jpeg)
                    temp_files.add(temp_jpeg)
                    
                    processed_path = process_file(temp_jpeg, rel_path, output_subdir)
                    if processed_path and os.path.exists(processed_path):
                        temp_files.add(processed_path)
                        jpeg_to_svs(processed_path, final_output)
                        image_count += 1
                    
                elif file_lower.endswith((".jpg", ".jpeg", ".png")):
                    # Regular image processing
                    processed_path = process_file(full_path, rel_path, output_subdir)
                    if processed_path:
                        final_output = os.path.join(output_subdir, file)
                        shutil.move(processed_path, final_output)
                        image_count += 1
                        
            except Exception as e:
                print(f"Failed to process {file}: {e}")

    # Cleanup temporary files
    print("\nCleaning up temporary files...")
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            print(f"Warning: Could not remove {temp_file}: {e}")

    # Final JPEG cleanup pass
    removed_count = clean_jpeg_files(OUTPUT_FOLDER)
    print(f"Removed {removed_count} temporary JPEG files")

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