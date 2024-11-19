from sqlalchemy import (
    create_engine, Column, Integer, String, Table, MetaData
)
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.ext.declarative import declared_attr
from pgvector.sqlalchemy import Vector
from sqlalchemy import cast, func, inspect
from dotenv import load_dotenv
import numpy as np
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
metadata = MetaData()

class ModelMeta(Base):
    __tablename__ = "model_meta"
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String, unique=True, nullable=False)
    model_type = Column(String, nullable=False)
    embedding_table = Column(String, nullable=False)

class EmbeddingTable(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)
    vector = Column(Vector, nullable=False)
    model_id = Column(String, nullable=False)

_emb_table_classes = {}

def fetch_embedding_table(model_type, model_dim):
    table_name = f"{model_type}_embeddings"
    inspector = inspect(engine)

    if not inspector.has_table(table_name):
        print(f"Creating table {table_name}...")
        table = Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("vector", Vector(dim=model_dim), nullable=False),
            Column("model_id", String, nullable=False),
            Column("image_uri", String, nullable=False), 
            extend_existing=True,  # Allow redefining options if it already exists
        )
        metadata.create_all(bind=engine)
    else:
        print(f"Table {table_name} already exists.")
        
    # FIXME: Dirty hack to get ORM working
    # Check if the ORM class is already defined
    if table_name not in _emb_table_classes:
        # Dynamically create the ORM class with all necessary columns
        table_class = type(
            table_name,
            (EmbeddingTable,),
            {
                "__tablename__": table_name.lower(),
                "id": Column(Integer, primary_key=True, autoincrement=True),
                "vector": Column(Vector(dim=model_dim), nullable=False),
                "model_id": Column(String, nullable=False),
                "image_uri": Column(String, nullable=False),  
            },
        )
        _emb_table_classes[table_name] = table_class

    return _emb_table_classes[table_name]


def save_vector(vector, model_id, model_type, model_dim, image_uri=None):
    table_class = fetch_embedding_table(model_type, model_dim)  # Already returns a class

    with Session(engine) as session:
        vector_dict = {"vector": vector.tolist(), "model_id": model_id, "image_uri": image_uri}
        session.add(table_class(**vector_dict))
        session.commit()


def save_vectors_bulk(vectors, model_id, model_type, model_dim, image_uris=None):
    table_class = fetch_embedding_table(model_type, model_dim)  # Already returns a class

    with Session(engine) as session:
        vector_dicts = [
            {"vector": v.tolist(), "model_id": model_id, "image_uri": uri}
            for v, uri in zip(vectors, image_uris or [])
        ]
        session.bulk_insert_mappings(table_class, vector_dicts)
        session.commit()
        


# FIXME: A lot can be improved
def search_embeddings(query_vector, model_id, model_type, model_dim, top_k=10):

    query_vector = query_vector.tolist() # Slow
    query_vector_cast = cast(query_vector, Vector(model_dim)) #FIXME: Hack

    table_class = fetch_embedding_table(model_type, model_dim)

    with Session(engine) as session:
        results = (
            session.query(
                table_class.image_uri,  
                func.cosine_distance(table_class.vector, query_vector_cast).label("distance") 
            )
            .filter(table_class.model_id == model_id)  # Filter by model_id
            .order_by("distance")  
            .limit(top_k)  # Limit results
            .all()
        )

    if not results:
        return {"error": f"No embeddings found for model_id {model_id}."}

    # Convert results into a list of dictionaries
    # This is again slow, look for different methods
    ordered_results = [
        {"image_uri": result.image_uri, "distance": result.distance} for result in results
    ]

    print(f"Search results from {table_class.__tablename__}: {ordered_results}")
    return ordered_results
