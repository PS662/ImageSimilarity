
### TODO: Add usage instructions

# Image Similarity Search Application

This Google Lens like prototype has a image similarity search backend using FastAPI, Celery, Redis, and pgvector. For feature extraction, I’ve integrated pretrained models like OpenCLIP, ResNet, and VGG.

For similarity search, I opted to use pgvector over Locality Sensitive Hashing. While LSH is faster for lightweight, approximate searches, it lacks the accuracy and scalability needed for complex use cases. Additionally, pgvector’s HNSW index offers superior query performance and accuracy compared to LSH, making it ideal for latency-sensitive applications. Pgvector has several other advantages  [https://www.metisdata.io/blog/exploring-the-power-of-pgvector-as-an-open-source-vector-database](https://www.metisdata.io/blog/exploring-the-power-of-pgvector-as-an-open-source-vector-database). Pgvector supports advanced vector operations like cosine similarity and ordering by relevance, which makes it easy to implement search pipelines without requiring separate tools for external index structure. Plus, pgvector scales well with modern database optimizations and avoids the additional infrastructure overhead that LSH typically demands.

I have not done this yet but I plan to add Siamese networks and Autoencoder and will benchmark along with the current models. I laso need to add ranking metrics and precision, recall, and Mean Average Precision. 

Another benchmarking that I need to do is to compare quantised model with the base models, to optimize latency without sacrificing much in terms of accuracy.


---

## Prerequisites

1. **Python**: Ensure Python 3.10 or later is installed.
2. **PostgreSQL**: Install PostgreSQL with the `pgvector` extension.
3. **Redis**: Install Redis for Celery task queue management.


---

## Installation

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

## Initialization

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

## Example Usage

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

## API Endpoints

### 1. Upload a Catalog
**Endpoint**: `POST /upload_catalogue`  
**Parameters**:
- `files`: A list of images to upload.
- `model_id`: Model to use for embedding.

### 2. Search With Image
**Endpoint**: `POST /search_with_image`  
**Parameters**:
- `file`: An image file for searching.

### 3. Poll Task Status
**Endpoint**: `GET /poll_task_status/{req_id}`  
**Parameters**:
- `req_id`: Task ID to check the status.

- For additional models, update the `config/model_config.json` file. 
