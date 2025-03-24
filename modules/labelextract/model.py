import torch
from segment_anything import sam_model_registry

def load_model(checkpoint_path="sam_vit_h_4b8939.pth", model_type="vit_h", device=None):
    if device is None:
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    sam = sam_model_registry[model_type](checkpoint=checkpoint_path).to(device)
    return sam, device