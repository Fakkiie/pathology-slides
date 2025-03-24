#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Download model checkpoint
curl -o modules/labelextract/sam_vit_h_4b8939.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth

