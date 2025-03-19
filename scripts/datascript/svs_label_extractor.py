import os
import openslide

def process_svs_for_label_and_macro(svs_path, label_dir, macro_dir):
    """
    Opens an SVS file and checks for 'label' and 'macro' in associated_images.
    If found, saves them in label_dir or macro_dir respectively.
    """
    print(f"\nProcessing: {svs_path}")
    try:
        slide = openslide.OpenSlide(svs_path)
    except openslide.OpenSlideError as e:
        print(f"  [ERROR] Cannot open slide: {e}")
        return

    associated = slide.associated_images.keys()
    print(f"  Associated images found: {list(associated)}")

    base_name = os.path.splitext(os.path.basename(svs_path))[0]

    # Check for label
    if "label" in associated:
        label_img = slide.associated_images["label"]
        # Convert to grayscale if prefered
        label_img_gray = label_img.convert("L")

        os.makedirs(label_dir, exist_ok=True)
        label_filepath = os.path.join(label_dir, f"{base_name}_label.jpeg")
        label_img_gray.save(label_filepath)
        print(f"  Saved label image to: {label_filepath}")
    else:
        print("  No label image found.")

    # Check for macro
    if "macro" in associated:
        macro_img = slide.associated_images["macro"]
        # Convert to grayscale if prefered
        macro_img_gray = macro_img.convert("L")

        os.makedirs(macro_dir, exist_ok=True)
        macro_filepath = os.path.join(macro_dir, f"{base_name}_macro.jpeg")
        macro_img_gray.save(macro_filepath)
        print(f"  Saved macro image to: {macro_filepath}")
    else:
        print("  No macro image found.")

    slide.close()

def process_all_svs_in_folder(input_svs_dir, label_dir, macro_dir):
    """
    Scans input_svs_dir for .svs files, processes each to extract label and macro images
    if they exist, and saves them into label_dir and macro_dir.
    """
    if not os.path.isdir(input_svs_dir):
        print(f"Error: {input_svs_dir} is not a directory.")
        return

    svs_files = [f for f in os.listdir(input_svs_dir) if f.lower().endswith(".svs")]
    if not svs_files:
        print(f"No .svs files found in {input_svs_dir}")
        return

    print(f"Found {len(svs_files)} .svs file(s) in {input_svs_dir}")
    for filename in svs_files:
        full_svs_path = os.path.join(input_svs_dir, filename)
        process_svs_for_label_and_macro(full_svs_path, label_dir, macro_dir)

if __name__ == "__main__":
    # Directory that holds my .svs files:
    svs_folder = os.path.join("data", "svs")

    # Output directories for label & macro images:
    label_output_dir = os.path.join("data", "svs_labels")
    macro_output_dir = os.path.join("data", "svs_macro")

    process_all_svs_in_folder(svs_folder, label_output_dir, macro_output_dir)
