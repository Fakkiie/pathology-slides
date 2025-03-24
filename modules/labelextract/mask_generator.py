import cv2
import numpy as np
from segment_anything import SamAutomaticMaskGenerator

def generate_mask(model, image_path):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mask_generator = SamAutomaticMaskGenerator(model)
    return mask_generator.generate(image_rgb), image_rgb