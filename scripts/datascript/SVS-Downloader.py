import requests
import json
import os

BASE_URL = "https://api.gdc.cancer.gov"
DOWNLOAD_FOLDER = "data/svs"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# 1) Define filters for open-access SVS files
filters = {
    "op": "and",
    "content": [
        {
            "op": "in",
            "content": {
                "field": "data_format",
                "value": ["SVS"]
            }
        },
        {
            "op": "in",
            "content": {
                "field": "access",
                "value": ["open"]
            }
        }
        # Uncomment this to filter by project (e.g., only TCGA-OV slides)
        # {
        #     "op": "in",
        #     "content": {
        #         "field": "project.project_id",
        #         "value": ["TCGA-OV"]
        #     }
        # }
    ]
}

# 2) Request parameters
params = {
    "filters": json.dumps(filters),
    "fields": "file_id,file_name,project.project_id,data_format,access",
    "format": "JSON",
    "size": 50  # Adjust this if you need more or fewer
}

# 3) Send the request to GDC API
response = requests.get(f"{BASE_URL}/files", params=params)
data = response.json()

# 4) Extract file details
hits = data.get("data", {}).get("hits", [])
print(f"Found {len(hits)} open-access SVS files.")

# 5) Loop through each file and download it
for i, item in enumerate(hits, start=1):
    file_id = item["file_id"]
    file_name = item["file_name"]
    project_dict = item.get("project", {})  # Avoid KeyError
    project_id = project_dict.get("project_id", "Unknown")

    print(f"[{i}/{len(hits)}] Downloading {file_name} from project {project_id}...")

    # Construct download URL
    download_url = f"{BASE_URL}/data/{file_id}"
    out_path = os.path.join(DOWNLOAD_FOLDER, file_name)

    # Download the file
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

print("\n✅ All SVS files downloaded successfully! Check 'data/svs/'.")
