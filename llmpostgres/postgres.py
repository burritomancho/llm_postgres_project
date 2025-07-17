from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import psycopg2
import psycopg2.extras
import os

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Did you link the database in Render?")
    conn = psycopg2.connect(database_url)
    psycopg2.extras.register_vector(conn)
    return conn

def init_db_schema():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_chunks (
            id SERIAL PRIMARY KEY,
            product_id INT REFERENCES products(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            embedding VECTOR(1536),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_chunks_embedding
        ON product_chunks
        USING ivfflat (embedding vector_l2_ops)
        WITH (lists = 100);
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_embedding_function(api_key=None):
    return OpenAIEmbeddings(model="text-embedding-ada-002", api_key=api_key)

def store_product_in_db(product_title, product_text, api_key=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.e
