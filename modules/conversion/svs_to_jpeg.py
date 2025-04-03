import openslide
import cv2
import numpy as np

def convert_svs_bottom_layer_to_jpeg(input_svs, output_jpeg):
    # Open the SVS file using OpenSlide
    slide = openslide.OpenSlide(input_svs)
    
    # Determine the bottom layer (lowest resolution)
    bottom_level = slide.level_count - 1
    width, height = slide.level_dimensions[bottom_level]
    print(f"Bottom layer (level {bottom_level}) dimensions: {width} x {height}")
    
    # Read the entire bottom layer as a region starting from (0,0)
    region = slide.read_region((0, 0), bottom_level, (width, height))
    
    # Convert the PIL image (RGBA) to a NumPy array and then to RGB
    arr_rgba = np.array(region)
    img_rgb = cv2.cvtColor(arr_rgba, cv2.COLOR_RGBA2RGB)
    
    slide.close()
    
    # Save the resulting bottom layer as a JPEG
    cv2.imwrite(output_jpeg, img_rgb)
    print(f"Saved bottom layer JPEG to {output_jpeg}")

if __name__ == "__main__":
    # Set your input SVS file path and output JPEG file path:
    input_svs = r""
    output_jpeg = r""
    
    convert_svs_bottom_layer_to_jpeg(input_svs, output_jpeg)
