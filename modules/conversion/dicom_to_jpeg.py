import pydicom
import cv2
import numpy as np
from datetime import datetime
from pydicom.dataset import FileDataset
from PIL import Image

def convert_dicom_bottom_layer_to_jpeg(input_dicom, output_jpeg):
    ds = pydicom.dcmread(input_dicom)
    img = ds.pixel_array
    if img.ndim >= 3:
        bottom_img = img[-1]
    else:
        bottom_img = img

    if bottom_img.dtype != np.uint8:
        bottom_img = bottom_img.astype(np.float32)
        bottom_img -= np.min(bottom_img)
        if np.max(bottom_img) > 0:
            bottom_img /= np.max(bottom_img)
        bottom_img = (bottom_img * 255).astype(np.uint8)

    cv2.imwrite(output_jpeg, bottom_img)
    print(f"Saved JPEG to {output_jpeg}")

def convert_jpeg_to_dicom(jpeg_path, output_dicom_path):
    img = Image.open(jpeg_path).convert('L')
    pixel_array = np.array(img)

    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.ImplementationClassUID = pydicom.uid.PYDICOM_IMPLEMENTATION_UID

    ds = FileDataset(output_dicom_path, {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.Modality = 'OT'
    ds.ContentDate = datetime.now().strftime('%Y%m%d')
    ds.ContentTime = datetime.now().strftime('%H%M%S')
    ds.PatientName = 'Converted'
    ds.PatientID = '000000'

    ds.Rows, ds.Columns = pixel_array.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsStored = 8
    ds.BitsAllocated = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = pixel_array.tobytes()

    ds.save_as(output_dicom_path)
    print(f"Re-saved as DICOM: {output_dicom_path}")
