import os
import chromadb
from chromadb.config import Settings

# Persistent local storage for the vector DB (Zero-setup approach)
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Initialize ChromaDB Client
# This uses SQLite under the hood to store vectors and metadata
client = chromadb.PersistentClient(path=STORAGE_DIR, settings=Settings(anonymized_telemetry=False))

def get_or_create_collection(job_id: str):
    """
    Retrieves or creates a collection specific to a job (document/video).
    The job_id serves as the unique identifier for the document's vector space.
    """
    # Chroma collection names must be valid identifiers. 
    # We replace any invalid characters just in case, but job_id is usually UUID.
    safe_name = f"doc_{job_id.replace('-', '_')}"
    return client.get_or_create_collection(name=safe_name)

def store_document_chunks(job_id: str, text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Chunks a long text and stores it in the local vector DB for this job_id.
    """
    collection = get_or_create_collection(job_id)
    
    # Simple chunking logic (character based)
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        
    # Prepare IDs and Documents for Chroma
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"chunk_index": i} for i in range(len(chunks))]
    
    # Chroma handles embedding automatically using all-MiniLM-L6-v2 by default
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Stored {len(chunks)} chunks in local Vector DB for job {job_id}")

def retrieve_context(job_id: str, query: str, top_k: int = 5) -> str:
    """
    Retrieves the most relevant chunks from the local vector DB based on the query.
    """
    collection = get_or_create_collection(job_id)
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    if not results['documents'] or not results['documents'][0]:
        return ""
        
    # Combine retrieved chunks into a single context string
    retrieved_chunks = results['documents'][0]
    context = "\n\n...[Snippet]...\n\n".join(retrieved_chunks)
    return context
