from langchain_core import embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List, Dict, Any
import os

from .config import Config


def setup_vs(api_key=None, collection_name: str = "docs"):
 # Evaluate the API key at CALL time, not DEFINITION time
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            # Create Config instance to get the key
            config = Config()
            api_key = config.GEMINI_API_KEY
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required but not found")

    config = Config()



    embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key= api_key,
            model= Config.EMBEDDING_MODEL,
            transport="rest"
            )

    return Chroma(
                collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_db"
        )

def add_documents(store, elements: List[Dict[str, Any]]):

    docs = []

    for element in elements:
        if element["content_type"] == "image":
            page_content = f"Image: {element.get('image_desc', 'No image description')}"
        elif element.get("content_type") == "table":
            page_content = element["content"]
            # add html conent if available
            if element.get("html_content"):
                page_content += f"\nTable HTML: {element['html_content']}"
        else:
            page_content = element["content"]

        # create document with metadata

        docs=[] 
        doc = Document(
                page_content=page_content,
                # metadata={
                    # merge operator to put all key values into outer dict.
                    # **(element.get("metadata",{}))
                    # }
                # )
                metadata = {
                "type": element.get("type", "unknown"),
                "content_type": element.get("content_type", "text"),
                "source": element.get("source", "unknown"),
                "id": element.get("id", "unknown"),
                # Add image data if available
                "image_data": element.get("image_data", ""),
                "image_desc": element.get("image_desc", ""),
                "html_content": element.get("html_content", "")
            }
        )
        docs.append(doc)
    
    # Add all documents to the store
    if docs:
        store.add_documents(docs)
        print(f"Added {len(docs)} documents to vector store")


def query(store, query_text: str, k: int = 4):
    return store.similarity_search(query_text, k=k)
