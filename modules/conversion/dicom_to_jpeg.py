import pydicom
import cv2
import numpy as np
from pydicom.uid import ExplicitVRLittleEndian
from pydicom.dataset import FileDataset
import os
from datetime import datetime

def convert_dicom_bottom_layer_to_jpeg(input_dicom_path, output_jpeg_path=None):
    """
    Converts DICOM to RGB JPEG and returns the RGB pixel array + original DICOM object.
    """
    try:
        ds = pydicom.dcmread(input_dicom_path, force=True)

        # Ensure required DICOM metadata exists
        if not hasattr(ds, 'file_meta'):
            ds.file_meta = pydicom.dataset.FileMetaDataset()
        if not hasattr(ds.file_meta, 'TransferSyntaxUID'):
            ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        pixel_array = ds.pixel_array

        # Get the last frame if multi-frame
        if pixel_array.ndim == 3:
            pixel_array = pixel_array[-1]

        # Normalize grayscale to 8-bit
        if pixel_array.dtype != np.uint8:
            pixel_array = cv2.normalize(pixel_array, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Convert to RGB for processing compatibility
        rgb_array = cv2.cvtColor(pixel_array, cv2.COLOR_GRAY2RGB)

        if output_jpeg_path:
            cv2.imwrite(output_jpeg_path, rgb_array)
            print(f"[✓] Saved temporary RGB JPEG: {output_jpeg_path}")

        return rgb_array, ds

    except Exception as e:
        print(f"[ERROR] Failed to convert DICOM to JPEG: {e}")
        raise

def convert_jpeg_to_dicom(processed_image_rgb, output_dicom_path, original_ds):
    """
    Converts an RGB or grayscale image array back to MONOCHROME2 DICOM format.
    """
    try:
        # Convert to grayscale if it's RGB
        if len(processed_image_rgb.shape) == 3:
            processed_image = cv2.cvtColor(processed_image_rgb, cv2.COLOR_RGB2GRAY)
        else:
            processed_image = processed_image_rgb

        new_ds = original_ds.copy()
        new_ds.PixelData = processed_image.tobytes()
        new_ds.Rows, new_ds.Columns = processed_image.shape

        new_ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        new_ds.SamplesPerPixel = 1
        new_ds.PhotometricInterpretation = "MONOCHROME2"
        new_ds.BitsAllocated = 8
        new_ds.BitsStored = 8
        new_ds.HighBit = 7
        new_ds.PixelRepresentation = 0

        new_ds.save_as(output_dicom_path)
        print(f"[✓] Saved modified DICOM to: {output_dicom_path}")

    except Exception as e:
        print(f"[ERROR] Failed to convert JPEG to DICOM: {e}")
        raise


