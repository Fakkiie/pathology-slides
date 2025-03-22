#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Download the SAM model checkpoint
CHECKPOINT_FILE="sam_vit_h_4b8939.pth"
CHECKPOINT_URL="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"

if [ ! -f "$CHECKPOINT_FILE" ]; then
    echo "Downloading SAM checkpoint..."
    wget -q "$CHECKPOINT_URL" -O "$CHECKPOINT_FILE"
    echo "Download complete."
else
    echo "Checkpoint already exists."
fi
