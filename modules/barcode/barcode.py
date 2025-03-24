import os
import cv2
import numpy as np
from pyzbar.pyzbar import decode as pyzbar_decode
from qreader import QReader
from pylibdmtx.pylibdmtx import decode as zxing_decode
from ultralytics import YOLO

# Load YOLO model
model = YOLO('../weights/best.pt')

# Define class names for YOLO
classNames = ["Item", "QR_code", "Bar_code"]

# Initialize QR Code Detectors
qreader = QReader()
cv_qr_detector = cv2.QRCodeDetector()

def compute_tight_bbox(x1, y1, x2, y2, image_shape):
    h, w, _ = image_shape
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return x1, y1, x2, y2

def detect_qr_codes(image):
    qr_detections = []

    # QReader
    qreader_results = qreader.detect(image)
    for result in qreader_results:
        if len(result['bbox_xyxy']) == 4:
            x1, y1, x2, y2 = map(int, result['bbox_xyxy'])
            x1, y1, x2, y2 = compute_tight_bbox(x1, y1, x2, y2, image.shape)
            qr_detections.append({"bbox": (x1, y1, x2, y2), "method": "QReader"})

    # Pyzbar
    pyzbar_results = pyzbar_decode(image)
    for obj in pyzbar_results:
        if obj.type == "QRCODE":
            (x, y, w, h) = obj.rect
            x1, y1, x2, y2 = compute_tight_bbox(x, y, x + w, y + h, image.shape)
            qr_detections.append({"bbox": (x1, y1, x2, y2), "method": "Pyzbar"})

    # OpenCV QRCodeDetector
    retval, points, _ = cv_qr_detector.detectAndDecode(image)
    if retval and points is not None:
        points = points[0].astype(int)
        x1, y1 = np.min(points, axis=0)
        x2, y2 = np.max(points, axis=0)
        x1, y1, x2, y2 = compute_tight_bbox(x1, y1, x2, y2, image.shape)
        qr_detections.append({"bbox": (x1, y1, x2, y2), "method": "OpenCV QRCodeDetector"})

    return qr_detections

def detect_barcodes_yolo(image):
    results = model(image, show=False, conf=0.80, iou=0.90, line_width=1, verbose=False)
    best_barcode = None

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            clsId = int(box.cls[0])

            if clsId >= len(classNames) or classNames[clsId] != "Bar_code":
                continue

            conf = float(box.conf[0])
            x1, y1, x2, y2 = compute_tight_bbox(x1, y1, x2, y2, image.shape)

            if best_barcode is None or conf > best_barcode["confidence"]:
                best_barcode = {"bbox": (x1, y1, x2, y2), "confidence": conf, "method": "YOLO"}

    return [best_barcode] if best_barcode else []

def detect_barcodes_pyzbar(image):
    best_barcode = None

    for barcode in pyzbar_decode(image):
        myData = barcode.data.decode('utf-8')
        (left, top, width, height) = barcode.rect
        x1, y1, x2, y2 = compute_tight_bbox(left, top, left + width, top + height, image.shape)

        if best_barcode is None or width * height > best_barcode["area"]:
            best_barcode = {"bbox": (x1, y1, x2, y2), "data": myData, "area": width * height, "method": "Pyzbar"}

    return [best_barcode] if best_barcode else []

def detect_barcodes(image):
    yolo_barcodes = detect_barcodes_yolo(image)
    if yolo_barcodes:
        return yolo_barcodes

    pyzbar_barcodes = detect_barcodes_pyzbar(image)
    if pyzbar_barcodes:
        return pyzbar_barcodes

    return []

def erase_detected_regions(image, detections):
    for detection in detections:
        x1, y1, x2, y2 = detection["bbox"]
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 0), thickness=-1)
    return image

def process_image(image_path, output_folder):
    image = cv2.imread(image_path)
    if image is None:
        return None

    qr_results = detect_qr_codes(image)
    barcode_results = detect_barcodes(image)
    image_without_codes = erase_detected_regions(image, qr_results + barcode_results)

    output_path = os.path.join(output_folder, f"processed_{os.path.basename(image_path)}")
    cv2.imwrite(output_path, image_without_codes)
    return output_path

def process_images():
    images_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "images"))
    output_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputimages"))
    os.makedirs(output_directory, exist_ok=True)

    results = {}

    if not os.path.exists(images_directory):
        return results

    for filename in os.listdir(images_directory):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(images_directory, filename)
            processed_image_path = process_image(image_path, output_directory)
            results[filename] = {"output_path": processed_image_path}

    return results

if __name__ == "__main__":
    process_images()
