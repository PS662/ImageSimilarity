from celery import Celery
import os
from .db import save_vector, search_embeddings
from .model_loader import load_model, extract_features
import numpy as np

DEFAULT_MODEL_ID = os.getenv("MODEL_ID", "resnet50_1")

celery = Celery('tasks', 
                broker=os.getenv("REDIS_URL"),
                backend=os.getenv("REDIS_URL"))

#FIXME: Add more models, add base class
@celery.task
def vectorize_image(image_path, model_id=None):
    if model_id is None:
        model_id = DEFAULT_MODEL_ID
    model = load_model(model_id)
    vector = extract_features(model, image_path)
    return vector

@celery.task
def add_vector(folder_path, model_id=None):
    if model_id is None:
        model_id = DEFAULT_MODEL_ID
    model = load_model(model_id)
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        vector = extract_features(model, file_path)
        print (f"Saving vecotr len: {(len(vector))}")
        save_vector(vector, model_id)
    return "Catalogue updated successfully"

@celery.task
def search_vector(image_path, model_id=None):
    if model_id is None:
        model_id = DEFAULT_MODEL_ID
    print(f"Search image: {image_path} with model: {model_id}")
    
    model = load_model(model_id)
    query_vector = extract_features(model, image_path)
    result = search_embeddings(query_vector, model_id)

    # Ensure result is serializable
    if isinstance(result, dict):
        for key, value in result.items():
            if isinstance(value, set):
                result[key] = list(value)  # Convert set to list
    print(f"Final result: {result}")  # Debug statement
    return result
