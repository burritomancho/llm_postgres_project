from rag import query_document
from document_utils import get_text_from_input
from dotenv import load_dotenv
from postgres import init_db_schema

import os
import streamlit as st

load_dotenv()
key = os.environ['OPENAI_API_KEY']

init_db_schema()


st.title("PDF Q&A App (LangChain + OpenAI)")

product_input = st.text_input("Enter a **webpage URL** OR a description of the product")

query = st.text_input("What would you like to know about this product?")

if product_input and query:
    with st.spinner("Processing product info..."):
        text = get_text_from_input(product_input)

        answer = query_document(
            product_title=product_input,
            product_text=text,
            query=query,
            api_key = key
        )

        st.write(answer)
