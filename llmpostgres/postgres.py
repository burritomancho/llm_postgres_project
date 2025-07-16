# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_openai import OpenAIEmbeddings
import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("POSTGRES_DB", "pdfdata"),
        user=os.environ.get("POSTGRES_USER", "pdf_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "pdf_pw"),
        host=os.environ.get("POSTGRES_HOST", "db"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
    )


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
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        cur.execute(
            """
            INSERT INTO product_chunks (product_id, content, embedding)
            VALUES (%s, %s, %s)
            """,
            (product_id, chunk, embedding_str),
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
    q_embed_str = "[" + ",".join(str(x) for x in q_embed) + "]"

    cur.execute(
        f"""
        SELECT content FROM product_chunks
        ORDER BY embedding <-> %s
        LIMIT {top_k};
        """,
        (q_embed_str,),
    )

    results = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return results
