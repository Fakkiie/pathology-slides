import pydicom
import cv2
import numpy as np
from pydicom.uid import ExplicitVRLittleEndian

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