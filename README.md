# AI-Powered Document Management System 🧠📁

![Angular](https://img.shields.io/badge/Angular-19-dd0031?style=for-the-badge&logo=angular)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20DB-blue?style=for-the-badge)

An enterprise-grade, full-stack Document Management System (DMS) supercharged with Artificial Intelligence. This platform allows organizations to securely store, version, and instantly retrieve documents using precise keyword matching and **Semantic Vector Search**. 

Built with a Decoupled API-First Architecture, the system automatically processes uploaded documents through OCR and utilizes LLMs to generate instant summaries, extract key business entities, and support interactive multi-turn conversational Q&A over the entire document corpus.

---

## ✨ AI Contributions & Pipelines

This project showcases a production-ready integration of Generative AI and Information Retrieval (IR) patterns, highlighted by the following pipelines:

### 1. Retrieval-Augmented Generation (RAG) — AI Assistant
* **Conversational Q&A**: Uses LangChain and OpenAI `gpt-4o-mini` to answer natural language questions about uploaded files.
* **Context Retrieval Engine**: Custom chunk-retrieval pipeline matching FAISS embeddings (with a fallback database keyword search when embeddings are compiling) to feed relevant document contexts directly to the LLM.
* **Citations & References**: Returns the exact source document details along with the specific text chunks utilized to generate the AI response.
* **Multi-Turn Chat History**: Preserves conversation history locally on the frontend, allowing for seamless follow-up questions.

### 2. Semantic Vector Search
* **Text Chunking**: Dynamically splits extracted text into overlapping segments using LangChain's `RecursiveCharacterTextSplitter` (chunk size: 1000, overlap: 200).
* **OpenAI Embeddings**: Converts chunks into 1536-dimensional vector representations using `text-embedding-3-small`.
* **FAISS Indexing**: Indexes vector embeddings on the local file system using **FAISS** (Facebook AI Similarity Search) FlatIP indexes (Inner Product) for lightning-fast cosine similarity lookups.
* **Hybrid Merging Engine**: Executes a PostgreSQL full-text search and a FAISS semantic search concurrently, merging results via a custom python ranking system to balance exact-word matches and conceptual meaning.

### 3. Automated Summarization & Entity Extraction
* **Structured JSON Extraction**: Commands OpenAI to return structured summaries, key topics, and named entities (Dates, Organizations, Concepts) with relevance scores using JSON Schema validation.
* **Metadata Generation**: Automatically stores word counts, page counts, and mime-types, updating the document's AI status asynchronously.

### 4. Optical Character Recognition (OCR)
* **Image Text Processing**: Detects scanned documents and images (PNG, JPG, JPEG), routing them through **PyTesseract** to extract text for downstream vectorization and summary tasks.

---

## 🏗️ System Architecture

The application is structured into decoupled tiers communicating via REST APIs. Long-running OCR and AI generation processes are handled in the background to ensure the client-side remains fast.

```mermaid
graph TD
    %% Frontend Layer
    subgraph Frontend [Client - Angular 19]
        UI[Stunning UI/UX - Dark Theme]
        Auth[JWT Authentication & Guards]
        Dash[Dashboard, Search, & Document Detail]
        AIChat[AI Assistant Chat View]
    end

    %% API Layer
    subgraph Backend [API Server - Django REST]
        API_GW[REST API Endpoints]
        Doc_App[Documents App: CRUD & Versions]
        Search_App[Search App: Hybrid Search Engine]
        Auth_App[Accounts App: RBAC & Profiles]
        
        API_GW --> Doc_App
        API_GW --> Search_App
        API_GW --> Auth_App
    end

    %% Background Processing Layer
    subgraph Async [Background Workers]
        Celery[Celery Task Workers]
        Redis[(Redis Broker & Cache)]
    end

    %% Data Layer
    subgraph Data [Data Persistence]
        DB[(PostgreSQL / SQLite)]
        FAISS[(FAISS Vector Index on Disk)]
        Storage[Local File System Media Storage]
    end

    %% External APIs
    subgraph External [AI Providers]
        OpenAI[OpenAI API]
    end

    %% Connections
    UI <-->|HTTP/REST APIs| API_GW
    Doc_App -.->|Trigger Task| Redis
    Redis -.-> Celery
    
    Celery -->|Vectorize Chunks| FAISS
    Celery -->|Summarize & Extract Entities| OpenAI
    
    Search_App <-->|SQL/Keyword Query| DB
    Search_App <-->|Similarity Lookup| FAISS
    Search_App <-->|Generate Embedding| OpenAI
    
    Doc_App <--> DB
    Doc_App <--> Storage
    Auth_App <--> DB
```

---

## 🛠️ Technology Stack

### Frontend (Client)
* **Framework:** Angular 19 (Standalone Components)
* **State Management:** RxJS, Signals
* **UI/UX:** Angular Material 19, Custom Vanilla CSS (Glassmorphism, CSS Variables, Accent Gradients, Micro-animations)
* **Routing:** Angular Router with Route Guards (AuthGuard/RoleGuard)
* **Markdown:** `ngx-markdown` to render formatted AI responses and code blocks.

### Backend (API Engine)
* **Framework:** Django & Django REST Framework (DRF)
* **Database:** PostgreSQL / SQLite (Development fallback)
* **Vector Store:** FAISS (Facebook AI Similarity Search)
* **Task Queue:** Celery & Redis (Asynchronous task offloading)
* **Authentication:** SimpleJWT (JSON Web Tokens)
* **Python 3.14 Compatibility:** Implemented lazy imports in views and tasks to avoid startup-time langchain deprecation clashes.

---

## 🚀 Local Development Setup

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- Redis Server (for background tasks)
- Tesseract OCR (installed on system path)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Or `venv/bin/activate` on Mac/Linux
pip install -r requirements.txt

# Environment Setup
cp .env.example .env
# --> Edit .env to add your OPENAI_API_KEY

# Database Migrations
python manage.py makemigrations
python manage.py migrate

# Create Superuser (Admin)
python manage.py createsuperuser

# Start Django Server
python manage.py runserver
```

### 2. Frontend Setup
```bash
cd frontend
npm install

# Start Angular Dev Server
npm start
```
The application will be available at **`http://localhost:4200`**.

---

## 👨‍💻 Author
**Nasim Uddin**  
*Full Stack & AI Engineer*

Demonstrating the power of combining traditional enterprise architecture with cutting-edge artificial intelligence to solve complex data retrieval problems.
