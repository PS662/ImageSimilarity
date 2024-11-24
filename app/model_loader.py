import os
import json
import numpy as np
import torch
import torch.nn as nn
from torchvision.models import resnet50, vgg16, ResNet50_Weights, VGG16_Weights
from PIL import Image
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from abc import ABC, abstractmethod
import open_clip
from fashion_clip.fashion_clip import FashionCLIP
from .db import fetch_embedding_table

_loaded_models = {}

# Default configuration for fallback
DEFAULT_MODEL_CONFIG = {
    "model_type": "resnet50",
    "model_dim": 2048,
    "model_id": "resnet50_1",
    "model_path": None,
}

CONFIG_PATH = os.path.join("config", "model_config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        MODEL_CONFIGS = {config["model_id"]: config for config in json.load(f)}
else:
    MODEL_CONFIGS = {DEFAULT_MODEL_CONFIG["model_id"]: DEFAULT_MODEL_CONFIG}


class BaseModel(ABC):
    @abstractmethod
    def preprocess(self):
        pass

    @abstractmethod
    def extract_features(self, image_path):
        pass


class ResNet50Model(BaseModel):
    def __init__(self):
        self.model = resnet50(weights=ResNet50_Weights.DEFAULT)
        self.model = nn.Sequential(*list(self.model.children())[:-1])
        self.model.eval()

    def preprocess(self):
        return Compose([
            Resize((224, 224)),
            ToTensor(),
            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def extract_features(self, image_path):
        img = Image.open(image_path).convert("RGB")
        input_tensor = self.preprocess()(img).unsqueeze(0)
        with torch.no_grad():
            features = self.model(input_tensor)
        return features.squeeze().numpy()


class VGG16Model(BaseModel):
    def __init__(self):
        self.model = vgg16(weights=VGG16_Weights.DEFAULT)
        # FIXME: VGG16 does not yield 4096 in the last layer, you would get 7 x 7 x 512
        # We are interested in 4096 len feature vector hence this hack.
        # 7x7x512 = 25088
        self.model = nn.Sequential(
            *list(self.model.children())[:-1],
            nn.Flatten(), 
            nn.Linear(25088, 4096), 
            nn.ReLU() 
        )
        self.model.eval()

    def preprocess(self):
        return Compose([
            Resize((224, 224)),
            ToTensor(),
            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def extract_features(self, image_path):
        img = Image.open(image_path).convert("RGB")
        input_tensor = self.preprocess()(img).unsqueeze(0)
        with torch.no_grad():
            features = self.model(input_tensor)
        flattened_features = features.squeeze().numpy()
        print(f"Flattened features shape: {flattened_features.shape}")
        return flattened_features



class OpenCLIPModel(BaseModel):
    def __init__(self, model_path, model_subtype=None):
        if model_subtype == "fashion_clip":
            self.model = FashionCLIP('fashion-clip')
            self.model_subtype = "fashion_clip"
        else:
            self.model, _, self.preprocess_func = open_clip.create_model_and_transforms(model_path, 
                                                                                        pretrained="laion2b_s34b_b79k")
            self.model_subtype = "open_clip"
            self.model.eval()

    def preprocess(self):
        return self.preprocess_func

    def extract_features(self, image_path):
        # FIXME: Add batch
        img = Image.open(image_path).convert("RGB")
        if self.model_subtype == "fashion_clip":
            features = self.model.encode_images([img], batch_size=1)
            return features.squeeze()
        else:
            input_tensor = self.preprocess()(img).unsqueeze(0)
            with torch.no_grad():
                features = self.model.encode_image(input_tensor)
            return features.squeeze().numpy()


class ModelLoader:
    @staticmethod
    def load_model(model_id=None):
        global _loaded_models

        if model_id is None:
            model_id = DEFAULT_MODEL_CONFIG["model_id"]

        if model_id in _loaded_models:
            return _loaded_models[model_id]

        model_info = MODEL_CONFIGS.get(model_id, DEFAULT_MODEL_CONFIG)
        model_type = model_info["model_type"]
        model_dim = model_info["model_dim"]
        model_subtype = None
        if "model_subtype" in model_info.keys():
            model_subtype= model_info["model_subtype"]

        fetch_embedding_table(model_type, model_dim)

        if model_type == "resnet50":
            model = ResNet50Model()
        elif model_type == "vgg16":
            model = VGG16Model()
        elif model_type == "openclip":
            model_path = None
            if "model_path" in model_info.keys():
                model_path = model_info["model_path"]
            model = OpenCLIPModel(model_path=model_path, model_subtype=model_subtype)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        model.output_dim = model_dim
        model.type = model_type
        _loaded_models[model_id] = model
        return model
