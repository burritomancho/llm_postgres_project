from langchain_openai import OpenAIEmbeddings

def get_embedding_function(api_key):
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002", openai_api_key=api_key
    )
    return embeddings
