import os
from tcia_utils import nbia

COLLECTION_NAME = "TCGA-BRCA"

# 1) Query all series in the collection
all_series = nbia.getSeries(collection=COLLECTION_NAME)
print(f"Found {len(all_series)} series in '{COLLECTION_NAME}'.")

# 2) Slice out the first 50
some_series = all_series[:50]

# 3) Build a plain Python list of SeriesInstanceUID strings
some_series_list = [s["SeriesInstanceUID"] for s in some_series]

# 4) Create the download folder
download_folder = os.path.join("data", "dicom")
os.makedirs(download_folder, exist_ok=True)

# 5) Download them all in one shot
print("\nDownloading 50 series to", download_folder)
nbia.downloadSeries(
    series_data=some_series_list,   # Our list of UIDs
    input_type="list",              # Tells downloadSeries we're passing a list
    path=download_folder            # Destination folder
)

print("\nDone! Check 'data/dicom' for downloaded .dcm files.")
