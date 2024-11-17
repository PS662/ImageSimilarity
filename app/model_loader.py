import os
from torchvision.models import resnet50, ResNet50_Weights
import torch.nn as nn
import torch

_loaded_models = {}

DEFAULT_MODEL_ID = os.getenv("MODEL_ID", "resnet50_1")

MODEL_CONFIG = {
    "resnet50_1": {
        "type": "resnet50",
        "dim": 2048,
    }
}

def load_model(model_id=None):
    global _loaded_models
    if model_id is None:
        model_id = DEFAULT_MODEL_ID

    if model_id in _loaded_models:
        return _loaded_models[model_id]

    if model_id not in MODEL_CONFIG:
        raise ValueError(f"Model ID '{model_id}' not found in config.")

    model_info = MODEL_CONFIG[model_id]
    model_type = model_info["type"]

    if model_type == "resnet50":
        model = resnet50(weights=ResNet50_Weights.DEFAULT)
        # Remove the classification head
        model = nn.Sequential(*list(model.children())[:-1])
        model.eval()  # Set model to evaluation mode
        _loaded_models[model_id] = model
        return model

    raise ValueError(f"Unsupported model type: {model_type}")

# FIXME: Add batch API
def extract_features(model, image_path):
    from PIL import Image
    from torchvision.transforms import Compose, Resize, ToTensor, Normalize

    preprocess = Compose([
        Resize((224, 224)),
        ToTensor(),
        Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    img = Image.open(image_path).convert("RGB")
    input_tensor = preprocess(img).unsqueeze(0)

    with torch.no_grad():
        features = model(input_tensor)
    
    return features.squeeze().numpy()
