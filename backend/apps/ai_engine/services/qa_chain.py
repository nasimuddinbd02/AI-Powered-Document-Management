import os
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from apps.ai_engine.models import DocumentEmbedding
import numpy as np

def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_a = np.linalg.norm(v1)
    norm_b = np.linalg.norm(v2)
    return dot_product / (norm_a * norm_b)

def retrieve_context(query, doc_ids, top_k=5):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OpenAI API Key not configured")
        
    embeddings_model = OpenAIEmbeddings(openai_api_key=api_key)
    query_embedding = embeddings_model.embed_query(query)
    
    # Fetch all embeddings for allowed docs
    chunks = DocumentEmbedding.objects.filter(document_id__in=doc_ids)
    
    results = []
    for chunk in chunks:
        # Simple local cosine similarity since we store JSON lists for dev
        sim = cosine_similarity(query_embedding, chunk.embedding)
        results.append({
            'chunk': chunk.chunk_text,
            'document_id': chunk.document_id,
            'score': sim
        })
        
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]
    return results

def answer_question(question, doc_ids):
    context_results = retrieve_context(question, doc_ids)
    context_text = "\n\n".join([r['chunk'] for r in context_results])
    
    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0, model_name="gpt-4", openai_api_key=api_key)
    
    prompt = f"""Use the following context to answer the question. If you don't know the answer, say you don't know.
    
    Context:
    {context_text}
    
    Question: {question}
    Answer:"""
    
    answer = llm.predict(prompt)
    return answer, context_results

def chat_with_documents(question, doc_ids, chat_history):
    # For a full RAG we would merge chat_history
    return answer_question(question, doc_ids)
