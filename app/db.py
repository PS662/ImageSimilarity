import psycopg2
import numpy as np
import json
from dotenv import load_dotenv
import os

load_dotenv()

def connect_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

#FIXME: Add bulk insert
def save_vector(vector, model_id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO embeddings (vector, model_id) VALUES (%s, %s)", 
            (json.dumps(vector.tolist()), model_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error saving vector: {e}")
    finally:
        conn.close()
        

def search_embeddings(query_vector, model_id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT vector FROM embeddings WHERE model_id = %s", (model_id,))
        vectors = cur.fetchall()

        if not vectors:
            return {"error": "No embeddings found for the given model_id."}

        vectors = [np.array(json.loads(v[0])) for v in vectors]
        similarities = [np.dot(v, query_vector) for v in vectors]
        best_match_idx = np.argmax(similarities)

        result = {
            "best_match": int(best_match_idx),  
            "similarity": float(similarities[best_match_idx]) 
        }
        print(f"Search result: {result}")  # Debug
        return result
    except Exception as e:
        print(f"Error searching embeddings: {e}")
        return {"error": str(e)}
    finally:
        conn.close()
