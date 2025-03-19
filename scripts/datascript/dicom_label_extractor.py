import os
import pydicom
import numpy as np
from PIL import Image

def extract_dicom_label(dicom_path, output_folder):
    print(f"\nInspecting DICOM file: {dicom_path}")
    try:
        ds = pydicom.dcmread(dicom_path)
    except Exception as e:
        print(f"  [ERROR] Could not read {dicom_path}: {e}")
        return

    # Check using ds.dir()
    if "SlideLabelImageSequence" not in ds.dir():
        print("  No 'SlideLabelImageSequence' found. Skipping.")
        return

    # If present, ds.SlideLabelImageSequence should be safe to access
    label_seq = ds.SlideLabelImageSequence[0]
    try:
        label_array = label_seq.pixel_array
    except Exception as e:
        print(f"  [ERROR] Could not access label pixel data: {e}")
        return

    # Convert to 8-bit if needed
    if label_array.dtype != np.uint8:
        max_val = np.max(label_array)
        if max_val > 0:
            label_array = (label_array / max_val * 255).astype(np.uint8)
        else:
            label_array = label_array.astype(np.uint8)

    label_img = Image.fromarray(label_array).convert("L")
    base_name = os.path.splitext(os.path.basename(dicom_path))[0]
    out_path = os.path.join(output_folder, f"{base_name}_label.jpeg")

    os.makedirs(output_folder, exist_ok=True)
    label_img.save(out_path)
    print(f"  Label image extracted and saved as {out_path}")


def extract_labels_in_folder(dicom_folder="data/dicom", label_output="data/dicom_labels"):
    """
    Loops over all .dcm files in dicom_folder and attempts to extract the label image
    (SlideLabelImageSequence) for each, saving it to label_output.
    """
    if not os.path.isdir(dicom_folder):
        print(f"Error: {dicom_folder} is not a valid directory.")
        return

    dcm_files = [f for f in os.listdir(dicom_folder) if f.lower().endswith(".dcm")]
    if not dcm_files:
        print(f"No .dcm files found in {dicom_folder}.")
        return

    print(f"Found {len(dcm_files)} DICOM file(s) in {dicom_folder}. Scanning for labels...")
    for fname in dcm_files:
        dicom_path = os.path.join(dicom_folder, fname)
        extract_dicom_label(dicom_path, label_output)


if __name__ == "__main__":
    # Adjust these paths as needed
    dicom_input_dir = os.path.join("data", "dicom")
    label_output_dir = os.path.join("data", "dicom_labels")

    extract_labels_in_folder(dicom_folder=dicom_input_dir, label_output=label_output_dir)
