import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from apps.ai_engine.models import DocumentEmbedding

def process_document_embeddings(document):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OpenAI API Key not configured")

    embeddings_model = OpenAIEmbeddings(openai_api_key=api_key)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    current_version = document.current_version
    if not current_version or not current_version.ocr_text:
        return

    chunks = text_splitter.split_text(current_version.ocr_text)
    
    # Clear existing
    DocumentEmbedding.objects.filter(document=document).delete()
    
    # Generate and save
    embeddings = embeddings_model.embed_documents(chunks)
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        DocumentEmbedding.objects.create(
            document=document,
            chunk_index=i,
            chunk_text=chunk,
            embedding=embedding
        )
