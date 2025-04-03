import openslide
import cv2
import numpy as np
import pyvips

def convert_svs_bottom_layer_to_jpeg(input_svs, output_jpeg):
    slide = openslide.OpenSlide(input_svs)
    bottom_level = slide.level_count - 1
    width, height = slide.level_dimensions[bottom_level]
    print(f"Bottom layer (level {bottom_level}) dimensions: {width} x {height}")

    region = slide.read_region((0, 0), bottom_level, (width, height))
    arr_rgba = np.array(region)
    img_rgb = cv2.cvtColor(arr_rgba, cv2.COLOR_RGBA2RGB)
    slide.close()

    cv2.imwrite(output_jpeg, img_rgb)
    print(f"Saved bottom layer JPEG to {output_jpeg}")

def jpeg_to_svs(jpeg_path, output_path):
    image = pyvips.Image.new_from_file(jpeg_path, access="sequential")
    image.tiffsave(
        output_path,
        tile=True,
        tile_width=256,
        tile_height=256,
        pyramid=True,
        bigtiff=True,
        compression="jpeg",
        Q=90,
        subifd=True
    )
    print(f"Re-saved as SVS: {output_path}")
