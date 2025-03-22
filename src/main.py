import os
from model import load_model
from mask_generator import generate_mask
from utils import show_output, find_label_area_from_generated_mask

# Constants
# IMAGE_PATH = "data/download (1).png"
CHECKPOINT_PATH = "sam_vit_h_4b8939.pth"
DATASET_FOLDER = "data/"
RESULT_FOLDER = "result/"
# Ensure model checkpoint exists
if not os.path.exists(CHECKPOINT_PATH):
    raise FileNotFoundError(f"Checkpoint file {CHECKPOINT_PATH} not found!")

# Load Model
sam, device = load_model(CHECKPOINT_PATH)



# Loop through all images in the dataset folder
for filename in os.listdir(DATASET_FOLDER):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        image_path = os.path.join(DATASET_FOLDER, filename)

        print(f"Processing: {image_path}")
        
        # Generate Mask
        output_mask, image_rgb = generate_mask(sam, image_path)
        
        # Get image dimensions
        image_shape = (image_rgb.shape[0], image_rgb.shape[1])

        # Process and save result
        save_path = os.path.join(RESULT_FOLDER, f"processed_{filename}")
        find_label_area_from_generated_mask(output_mask, image_shape, image_rgb, save_path)
