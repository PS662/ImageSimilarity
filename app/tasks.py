from celery import Celery
import os
from .db import save_vector, save_vectors_bulk, search_embeddings
from .model_loader import ModelLoader, DEFAULT_MODEL_CONFIG
import numpy as np

DEFAULT_MODEL_ID = DEFAULT_MODEL_CONFIG["model_id"]

celery = Celery('tasks', 
                broker=os.getenv("REDIS_URL"),
                backend=os.getenv("REDIS_URL"))

@celery.task
def vectorize_image(image_path, model_id=None):
    if model_id is None:
        model_id = DEFAULT_MODEL_ID

    model = ModelLoader.load_model(model_id)
    vector = model.extract_features(image_path)
    return vector


@celery.task
def add_vector(folder_path, model_id=None):
    if model_id is None:
        model_id = DEFAULT_MODEL_ID

    model = ModelLoader.load_model(model_id)
    model_type = model_id.split("_")[0]
    print(f"Using model id: {model_id}")
    vectors = []
    image_uris = []
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        vector = model.extract_features(file_path)
        print(f"Saving vector len: {len(vector)}")
        vectors.append(vector)
        image_uris.append(file_path)

    save_vectors_bulk(vectors, model_id, model_type, model.output_dim, image_uris=image_uris)
    return "Catalogue updated successfully"


@celery.task
def search_vector(image_path, model_id=None):
    if model_id is None:
        model_id = DEFAULT_MODEL_ID

    #FIXME: Encapsulate
    model = ModelLoader.load_model(model_id)
    model_type = model_id.split("_")[0]
    print(f"Search image: {image_path} with model: {model_id} model_dim: {model.output_dim}")

    query_vector = model.extract_features(image_path)
    results = search_embeddings(query_vector, model_id, model_type, model.output_dim)

    print(f"Final results: {results}")
    return results

