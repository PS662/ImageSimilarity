
# Image Similarity Search Application

This Google Lens like prototype has a image similarity search backend using FastAPI, Celery, Redis, and pgvector. For feature extraction, I’ve integrated pretrained models like OpenCLIP, ResNet, and VGG.

For similarity search, I opted to use pgvector over Locality Sensitive Hashing. While LSH is faster for lightweight, approximate searches, it lacks the accuracy and scalability needed for complex use cases. Additionally, pgvector’s HNSW index offers superior query performance and accuracy compared to LSH, making it ideal for latency-sensitive applications. Pgvector has several other advantages  [https://www.metisdata.io/blog/exploring-the-power-of-pgvector-as-an-open-source-vector-database](https://www.metisdata.io/blog/exploring-the-power-of-pgvector-as-an-open-source-vector-database). Pgvector supports advanced vector operations like cosine similarity and ordering by relevance, which makes it easy to implement search pipelines without requiring separate tools for external index structure. Plus, pgvector scales well with modern database optimizations and avoids the additional infrastructure overhead that LSH typically demands.

Another benchmarking that I need to do is to compare quantised model with the base models, to optimize latency without sacrificing much in terms of accuracy.

The mini-test dataset: [https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small)

Walkthrough: [https://www.loom.com/share/9f3236f22aec4606b059af9f1b91752a?sid=d29b0a1a-41d1-49fe-bd07-f3bf508b4c08](https://www.loom.com/share/9f3236f22aec4606b059af9f1b91752a?sid=d29b0a1a-41d1-49fe-bd07-f3bf508b4c08)

---

## Prerequisites

1. **Python**: Ensure Python 3.10 or later is installed.
2. **PostgreSQL**: Install PostgreSQL with the `pgvector` extension.
3. **Redis**: Install Redis for Celery task queue management.


---

## Installation - Docker

```
make docker-app-image
make run-compose

# If you are running for the first time
source set_bash_env.sh
make init-db 

# When you are done
make stop-compose
```

---

## Example Usage

Go to: `http://localhost:8000`

### 1. **Uploading a Catalog of Images**

- Click the **"Update Catalogue"** button on the homepage.
- Select a folder containing images.
- Choose the model ID from the dropdown (if applicable).
- The images will be processed and stored in the database.

### 2. **Searching with an Image**

- Click the **"Search With Image"** button on the homepage.
- Select an image file to upload.
- The application will display a grid of the most similar images from the catalog.

---

## Evaluation

Quick hack to create a dummy ground truth. Ideally, we would have tags and we could use text embeddings to check similarity. Here I am selecting random image uri for every odd index and for even assigning true.
This can easily be replace with an original ground truth.

I have calculated MRR, NDCG, Precision, Recall and F1-Score.

To evaluate run:

```
python evaluation/evaluation_metrics.py --help # to see full list of supported options

python evaluation/evaluation_metrics.py --test-folder-data ./temp_catalogue/openclip_1/ --model-id openclip_1 --metrics MRR Precision Recall F1-Score NDCG --cache-dir evaluation/results/

```

## API Endpoints

`POST /upload_catalogue`  

`POST /search_with_image`  

`GET /poll_task_status/{req_id}`  


- For additional models, update the `config/model_config.json` file. 

## Installation - Develop

1. Clone the repository:
   ```bash
   git clone https://github.com/PS662/ImageSimilarity
   cd ImageSimilarity
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv image_similarity_env
   source image_similarity_env/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install pgvector

    ```
    sudo apt install postgresql-server-dev-14
    cd /tmp
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    make install # may need sudo
    ```

5. Set up environment variables, look into .env.example

---

### Initialization

1. **Set up the database**:
   Initialize the PostgreSQL database and `pgvector` extension:
   ```bash
   make init-db
   ```

2. **Start the Celery worker**:
   ```bash
   make run-worker
   ```

3. **Run the application**:
   ```bash
   make run-app
   ```

The application will be available at `http://localhost:8000`.

---