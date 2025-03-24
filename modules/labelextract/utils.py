import matplotlib.pyplot as plt
import numpy as np
import os
import cv2

def show_output(result_dict, image_rgb, axes=None):
    if axes is None:
        _, axes = plt.subplots(1, 2, figsize=(10, 10))
    axes[0].imshow(image_rgb)

    sorted_result = sorted(result_dict, key=lambda x: x['area'], reverse=True)
    for val in sorted_result:
        mask = val['segmentation']
        img = np.ones((mask.shape[0], mask.shape[1], 3))
        color_mask = np.random.random((1, 3)).tolist()[0]
        for i in range(3):
            img[:, :, i] = color_mask[i]
        axes[1].imshow(np.dstack((img, mask * 0.5)))

    plt.show()


def find_label_area_from_generated_mask(output_mask, image_shape, image_rgb, save_path="result/processed_image.png"):
    """
    Finds the bounding box closest to the image edge and calculates its area,
    ensuring it is at most 1/3 of the total image area, also width of Image is 1/3 of total width.

    Parameters:
        output_mask (list of dict): Generated mask output from mask_generator.generate(image_rgb).
        image_shape (tuple): Shape of the original image (height, width).

    Returns:
        int: Area of the detected label region (if valid), otherwise None.
        Blackens the detected label region on the original image.
    """
    height, width = image_shape[:2]
    total_image_area = height * width
    max_allowed_width = width / 3  # 1/3 of total image width
    max_allowed_area = total_image_area / 3

    best_box = None
    best_distance = float('inf')

    for mask_data in output_mask:
        bbox = mask_data["bbox"]  # Bounding box format: (x, y, w, h)
        x, y, w, h = bbox
        area = w * h
        distance = min(x, y, width - (x + w), height - (y + h))

        if distance < best_distance and w <= max_allowed_width and area <= max_allowed_area:
            best_distance = distance
            best_box = bbox

    if best_box:
        x, y, w, h = best_box
        area = w * h
        image_with_box = image_rgb.copy()
        image_with_box[y:y + h, x:x + w] = (0, 0, 0)  # Set label area to black

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cv2.imwrite(save_path, cv2.cvtColor(image_with_box, cv2.COLOR_RGB2BGR))

        return area
    else:
        return None
