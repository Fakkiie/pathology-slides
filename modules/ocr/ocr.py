import os
import numpy as np
import cv2
from PIL import Image
from paddleocr import PaddleOCR
from pillow_heif import register_heif_opener

# Register HEIC support
register_heif_opener()

# Initialize OCR engine
ocr = PaddleOCR(use_angle_cls=True, lang='en',
                det_db_thresh=0.3, det_db_box_thresh=0.5,
                det_db_unclip_ratio=2.0,
                show_log=False)

def run_ocr_on_image(image_path, save_dir):
    try:
        # Step 1: Convert HEIC to JPG if needed
        ext = os.path.splitext(image_path)[1].lower()
        if ext == '.heic':
            print(f"Converting HEIC image: {image_path}")
            img = Image.open(image_path).convert("RGB")
            image_path = os.path.join(save_dir, os.path.basename(image_path).replace('.heic', '.jpg'))
            img.save(image_path, "JPEG")
            print(f"Image converted to: {image_path}")

        # Step 2: Preprocessing (contrast + sharpening)
        img = cv2.imread(image_path)
        contrast = cv2.convertScaleAbs(img, alpha=0.5, beta=0.1)
        kernel_sharpening = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(contrast, -1, kernel_sharpening)

        sharpened_path = os.path.join(save_dir, "temp_sharpened.jpg")
        cv2.imwrite(sharpened_path, sharpened)

        # Step 3: OCR
        result = ocr.ocr(sharpened_path, cls=True)
        os.remove(sharpened_path)

        if not result or not result[0]:
            print(f"No text detected in {image_path}")
            return None

        # Step 4: Black out detected text regions
        original_image = cv2.imread(image_path)

        for line in result[0]:
            box = line[0]  # list of 4 points (x, y)
            pts = np.array(box, dtype=np.int32)
            cv2.fillPoly(original_image, [pts], (0, 0, 0))  # Fill polygon with black

        # Step 5: Save blacked-out image
        result_path = image_path 
        cv2.imwrite(result_path, original_image)

        print(f"Text redacted and saved to: {result_path}")
        return result_path

    except Exception as e:
        print(f"OCR failed for {image_path}: {e}")
        return None
