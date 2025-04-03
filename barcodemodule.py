import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pyzbar.pyzbar import decode as pyzbar_decode
from qreader import QReader
from pylibdmtx.pylibdmtx import decode as zxing_decode  # Using ZXing equivalent

# ✅ Initialize QR Code Detectors (For QR codes only)
qreader = QReader()
cv_qr_detector = cv2.QRCodeDetector()

def detect_qr_codes(image):
    """Detects QR codes using Pyzbar, OpenCV, and QReader."""
    qr_detections = []

    # ✅ Method 1: Pyzbar
    pyzbar_results = pyzbar_decode(image)
    for obj in pyzbar_results:
        if obj.type == "QRCODE":
            qr_detections.append({
                "bbox": [(p.x, p.y) for p in obj.polygon]
            })

    # ✅ Method 2: OpenCV QRCodeDetector
    retval, points, _ = cv_qr_detector.detectAndDecode(image)
    if retval and points is not None:
        points = points[0].astype(int)
        qr_detections.append({
            "bbox": [tuple(point) for point in points]
        })

    # ✅ Method 3: QReader
    qreader_results = qreader.detect(image)
    for result in qreader_results:
        if len(result['bbox_xyxy']) == 4:
            x1, y1, x2, y2 = map(int, result['bbox_xyxy'])
            qr_detections.append({
                "bbox": [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            })

    return qr_detections  # ✅ Green boxes for QR codes

def detect_barcodes(image):
    """Detects barcodes using ZXing (pylibdmtx)."""
    barcode_detections = []
    decoded_barcodes = zxing_decode(image)

    for barcode in decoded_barcodes:
        x, y, w, h = barcode.rect.left, barcode.rect.top, barcode.rect.width, barcode.rect.height
        barcode_detections.append({
            "bbox": (x, y, x + w, y + h),
            "data": barcode.data.decode("utf-8") if barcode.data else None
        })
    
    return barcode_detections  # ✅ Yellow boxes for barcodes

def process_image(image_path):
    """Processes an image, detecting only QR codes from our function and barcodes from ZXing."""
    print(f"[INFO] Processing: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Could not load image: {image_path}")
        return None, None

    # ✅ Detect QR Codes (Only our 3 methods)
    qr_results = detect_qr_codes(image)

    # ✅ Detect Barcodes (Using ZXing)
    barcode_results = detect_barcodes(image)

    # ✅ Draw bounding boxes for barcodes (Yellow)
    for barcode in barcode_results:
        x1, y1, x2, y2 = barcode["bbox"]
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)  # Yellow for Barcodes

        label = f'Barcode: {barcode["data"]}' if barcode["data"] else "Barcode"
        cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    # ✅ Draw bounding boxes for QR codes (Green)
    for qr in qr_results:
        pts = np.array(qr["bbox"], dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, (0, 255, 0), 2)  # Green for QR Codes

    return barcode_results, image

def process_images(directory):
    """Processes all images in a directory and returns barcode detections."""
    results = {}
    for filename in os.listdir(directory):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(directory, filename)
            barcodes, processed_image = process_image(image_path)

            # ✅ Store results
            results[filename] = {"barcodes": barcodes}

            # ✅ Display processed image using Matplotlib
            if processed_image is not None:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.imshow(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
                ax.set_title(f"Detected Barcodes - {filename}")
                ax.axis("off")
                plt.show()
    
    return results

if __name__ == "__main__":
    IMAGE_DIRECTORY = "~/Downloads/barcode-dataset/"
    detections = process_images(os.path.expanduser(IMAGE_DIRECTORY))

    
    for img_name, result in detections.items():
        print(f"\nImage: {img_name}")
        print("Barcodes:")
        for barcode in result["barcodes"]:
            print(f"   - Bbox: {barcode['bbox']}, Data: {barcode['data']}")