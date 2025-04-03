import pydicom
import cv2
import numpy as np

def convert_dicom_bottom_layer_to_jpeg(input_dicom, output_jpeg):
    # Read the DICOM file
    ds = pydicom.dcmread(input_dicom)
    
    # Extract the pixel data from the dataset.
    # If multi-frame, ds.pixel_array is an array with shape (frames, rows, cols)
    # For single-frame images, it is 2D.
    img = ds.pixel_array
    if img.ndim >= 3:
        # Use the last frame (bottom layer)
        bottom_img = img[-1]
    else:
        bottom_img = img

    # Normalize the image if it's not already 8-bit
    if bottom_img.dtype != np.uint8:
        bottom_img = bottom_img.astype(np.float32)
        bottom_img -= np.min(bottom_img)
        if np.max(bottom_img) > 0:
            bottom_img /= np.max(bottom_img)
        bottom_img = (bottom_img * 255).astype(np.uint8)
    
    # Save the resulting image as a JPEG
    cv2.imwrite(output_jpeg, bottom_img)
    print(f"Saved JPEG to {output_jpeg}")

if __name__ == "__main__":
    # Set your input and output file paths:
    input_dicom = r""       # Replace with your DICOM file path
    output_jpeg = r"" # Replace with desired JPEG output path
    
    convert_dicom_bottom_layer_to_jpeg(input_dicom, output_jpeg)
