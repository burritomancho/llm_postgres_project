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
    cur.execute(
        "INSERT INTO products (title, source) VALUES (%s, %s) RETURNING id;",
        (product_title, "user_input"),
    )
    product_id = cur.fetchone()[0]

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(product_text)

    embeddings_model = get_embedding_function(api_key)
    for chunk in chunks:
        embedding = embeddings_model.embed_query(chunk)
        cur.execute(
            """
            INSERT INTO product_chunks (product_id, content, embedding)
            VALUES (%s, %s, %s)
            """,
            (product_id, chunk, embedding),
        )
    conn.commit()
    cur.close()
    conn.close()
    return product_id

def search_similar_chunks(question, api_key=None, top_k=5):
    conn = get_db_connection()
    cur = conn.cursor()
    embeddings_model = get_embedding_function(api_key)
    q_embed = embeddings_model.embed_query(question)
    cur.execute(
        f"""
        SELECT content FROM product_chunks
        ORDER BY embedding <-> %s
        LIMIT {top_k};
        """,
        (q_embed,),
    )
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return results
