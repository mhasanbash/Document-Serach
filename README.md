# Document-Serach
# RAG System with Django, Chroma & LangChain

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-5.2-green.svg)](https://djangoproject.com)
[![Docker](https://img.shields.io/badge/docker-compose-blue)](https://docker.com)

An intelligent **Retrieval-Augmented Generation (RAG)** question‑answering system that lets you upload Word (`.docx`) files, understands their content, and answers your questions based on the documents. Built with **Django REST Framework**, **Chroma vector database**, and **LangChain** + **OpenRouter/OpenAI** language models.

---

## ✨ Key Features

- Upload `.docx` files with automatic metadata extraction  
- Convert text to vectors (embeddings) and store them in Chroma (vector database)  
- Semantic search across all documents or within a specific document  
- Generate intelligent answers using an LLM (GPT‑oss‑120b or any other)  
- Full CRUD operations on documents with automatic Chroma synchronization  
- Store question & answer history  
- Ready‑to‑run with Docker & Docker Compose  

---

## 🛠️ Technologies

- **Backend**: Django 5.2, Django REST Framework  
- **Main database**: PostgreSQL 17  
- **Vector database**: Chroma (persistent directory)  
- **LLM & Embeddings**: LangChain + OpenRouter (switchable to OpenAI)  
- **File processing**: LangChain KreuzbergLoader (supports 88+ formats)  
- **Containerization**: Docker, Docker Compose  

---

## 📋 Prerequisites

- Docker and Docker Compose installed  
- An API key from [OpenRouter](https://openrouter.ai/keys) or OpenAI (for embedding and chat models)

---

## 🚀 Quick Start

### 1️⃣ Clone the repository
```bash
git clone https://your-repo-url.git
cd your-project
```

## Project Structure (Simplified)
.
├── backend/
│   ├── config/                # Django settings & URLs
│   ├── LLM/                   # Main RAG app
│   │   ├── models.py          # Documents, QueryAndAnswer models
│   │   ├── views.py           # Upload, delete, query API views
│   │   ├── chroma_service.py  # Chroma + LangChain integration
│   │   └── ...
│   └── manage.py
├── media/                     # Uploaded files (auto‑created)
├── chroma_data/               # Chroma vector database files (auto‑created)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
