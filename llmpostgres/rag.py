from langchain_openai import ChatOpenAI
# from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from postgres import store_product_in_db, search_similar_chunks
from prompt import Prompt

# def format_documents(docs):
#     return"\n\n".join(doc.page_content for doc in docs)

def answer_question(relevant_chunks, query, api_key):
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

    context = "\n\n".join(relevant_chunks)

    prompt_template = ChatPromptTemplate.from_template(Prompt)

    prompt = prompt_template.format(context=context, question=query)

    return llm.invoke(prompt).content

def query_document(product_title, product_text, query, api_key):
    store_product_in_db(product_title, product_text, api_key=api_key)

    relevant_chunks = search_similar_chunks(query, api_key=api_key, top_k=5)

    final_answer = answer_question(relevant_chunks, query, api_key)

    return final_answer
