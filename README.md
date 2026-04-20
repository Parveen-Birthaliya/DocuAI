# DocuAI - Multi-Format RAG System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**DocuAI** is a comprehensive, production-ready **Retrieval-Augmented Generation (RAG)** system that processes multi-format documents and enables semantic search with LLM-powered Q&A.

## 🎯 Features

✅ **Complete RAG Pipeline** - 7 sequential processing stages  
✅ **8 Document Formats** - PDF, HTML, JSON, CSV, TXT, Markdown, Python code + binary  
✅ **100% Local Processing** - No cloud APIs, all CPU-runnable models  
✅ **Production-Grade** - ~9,000 lines of clean, documented code  
✅ **Multiple Interfaces** - CLI, REST API, Streamlit UI  
✅ **Flexible LLM Backend** - Support for mock, OpenAI, HuggingFace, Ollama  
✅ **Deploy Anywhere** - GitHub, Hugging Face Spaces, Docker, Local  

## 🏗️ Architecture

### 7-Stage Processing Pipeline

```
Raw Documents
    ↓
[BLOG 1] Corpus Audit & Quality Baselining
    ├─ Format detection (8 formats)
    ├─ Quality scoring (GPT-2 perplexity)
    └─ Routing table generation
    ↓
[BLOG 2] Format-Aware Parsing
    ├─ PDF text/OCR extraction
    ├─ HTML structure preservation
    ├─ CSV/JSON/TXT parsing
    └─ Intelligent routing
    ↓
[BLOG 3] Text Cleaning & Noise Elimination
    ├─ Tier 1: Heuristic filters
    ├─ Tier 2: Statistical quality gating
    └─ Tier 3: Boilerplate removal
    ↓
[BLOG 4] Structured Knowledge Extraction
    ├─ Table extraction
    ├─ Metadata extraction
    ├─ Code block identification
    └─ Document structure analysis
    ↓
[BLOG 5] Deduplication & Consolidation
    ├─ Multi-metric similarity (5 metrics)
    ├─ Duplicate detection & grouping
    └─ Knowledge merging
    ↓
[BLOG 6] Embedding & Retrieval
    ├─ Intelligent chunking
    ├─ Semantic embeddings (384-dim)
    ├─ FAISS vector indexing
    └─ Similarity search
    ↓
[BLOG 7] RAG - User Interfaces
    ├─ CLI interactive mode
    ├─ REST API (Flask)
    ├─ Web UI (Streamlit)
    └─ Batch processing
    ↓
Q&A Results with Attribution
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/docuai/docuai.git
cd docuai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (optional, for Blog 3)
python -m spacy download en_core_web_sm
```

### Run Full Pipeline

```bash
# Process all documents through all 6 stages (Blog 1-6)
python run_pipeline.py all

# Or process individual stages
python run_pipeline.py blog1    # Audit & quality scoring
python run_pipeline.py blog2    # Parsing
python run_pipeline.py blog3    # Cleaning
python run_pipeline.py blog4    # Extraction
python run_pipeline.py blog5    # Deduplication
python run_pipeline.py blog6    # Embedding & retrieval
```

### Interact with RAG System (Blog 7)

```bash
# CLI Mode - Interactive Q&A
python run_pipeline.py blog7 --mode cli

# REST API - Start Flask server
python run_pipeline.py blog7 --mode api --port 5000
# Then: curl -X POST http://localhost:5000/api/answer -H "Content-Type: application/json" -d '{"question": "What is X?"}'

# Web UI - Streamlit app
python run_pipeline.py blog7 --mode streamlit
# Opens browser at http://localhost:8501
```

### Programming API

```python
from src.blog6_embedding import load_retriever
from src.blog7_rag import Blog7Orchestrator

# Load retriever
retriever = load_retriever()

# Create orchestrator
orchestrator = Blog7Orchestrator(retriever, llm_model="mock")

# Answer questions
answer = orchestrator.answer("What is the main topic?", top_k=5)
print(answer.answer)
print(f"Confidence: {answer.confidence:.0%}")
print(f"Sources: {answer.sources}")
```

## 📁 Project Structure

```
docuai/
├── src/
│   ├── blog1_audit/           # Stage 1: Corpus audit
│   ├── blog2_parsing/         # Stage 2: Format parsing
│   ├── blog3_cleaning/        # Stage 3: Text cleaning
│   ├── blog4_extraction/      # Stage 4: Knowledge extraction
│   ├── blog5_dedup/           # Stage 5: Deduplication
│   ├── blog6_embedding/       # Stage 6: Embedding & retrieval
│   ├── blog7_rag/             # Stage 7: RAG interfaces
│   ├── utils/                 # Shared utilities
│   ├── chunking/              # Chunking strategies
│   ├── embedding/             # Embedding models
│   ├── models/                # Data models
│   └── config.py              # Configuration
├── data/
│   ├── raw/                   # Input documents
│   └── processed/             # Processed outputs
├── docs/                      # Documentation
│   ├── implementation/        # Technical docs
│   └── guides/                # User guides
├── tests/                     # Test suite
├── archive/                   # Blog research & stage docs
├── pipeline.py                # Main orchestrator
├── run_pipeline.py            # CLI entry point
├── requirements.txt           # Python dependencies
├── config.yaml                # Configuration file
└── pyproject.toml             # Package metadata
```

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
paths:
  data_dir: data
  processed_path: data/processed

blog1:
  sample_size: 100

blog6:
  embedding_model: all-MiniLM-L6-v2
  chunk_size: 512
  chunk_overlap: 50

blog7:
  mode: cli
  llm_model: mock
  api_port: 5000
```

## 📊 Performance

| Stage | Speed | Memory |
|-------|-------|--------|
| Blog 1 (Audit) | 5-10s/100 docs | ~200MB |
| Blog 2 (Parsing) | 30-60s/100 docs | ~300MB |
| Blog 3 (Cleaning) | 10-20s/100 docs | ~200MB |
| Blog 4 (Extraction) | 20-30s/100 docs | ~250MB |
| Blog 5 (Dedup) | 15-30s/100 docs | ~500MB |
| Blog 6 (Embedding) | 5-10s/100 docs | ~800MB |
| **Blog 7 (RAG)** | **100-500ms/query** | **1-1.2GB** |

## 🌐 Deployment

### Hugging Face Spaces

```bash
# 1. Create new Space (Python 3.10+)
# 2. Upload requirements.txt
# 3. Create app.py:
#    from pipeline import RAGPipeline
#    p = RAGPipeline()
#    p.run_stage_7_rag(mode="streamlit")
# 4. Deploy!
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
CMD ["streamlit", "run", "app.py"]
```

### Local Development

```bash
python run_pipeline.py all  # Process documents
python run_pipeline.py blog7 --mode streamlit  # Start UI
```

## 📚 Documentation

- **[Quickstart Guide](docs/guides/QUICKSTART.md)** - Get started in 5 minutes
- **[Architecture](docs/implementation/PROJECT_ARCHITECTURE.md)** - System design details
- **[Implementation](docs/implementation/IMPLEMENTATION_SUMMARY.md)** - Full technical overview
- **[Documentation Index](docs/README.md)** - Complete documentation
- **[Archive](archive/blog_docs/)** - Research blogs & stage documentation

## 🔄 Data Flow

```
Question
    ↓
Orchestrator Route
    ↓
RAGAnswerer.answer(question)
    ├→ Retriever.search(question, top_k)
    │   ├→ Embed query with all-MiniLM-L6-v2
    │   └→ FAISS search returns top_k chunks
    │
    ├→ LLMBackend.generate(query, context)
    │   ├→ Mock: Extract key phrases
    │   ├→ OpenAI: Call GPT-3.5/4
    │   ├→ HuggingFace: Use local model
    │   └→ Ollama: Use local Ollama
    │
    └→ RAGAnswer(query, answer, sources, confidence)
            ↓
        Response to User
```

## 🛠️ Technology Stack

### Core
- **sentence-transformers** - 384-dim embeddings
- **FAISS** - Vector similarity search
- **spaCy** - NLP & tokenization
- **transformers** - LLM models

### Interfaces
- **Flask** - REST API
- **Streamlit** - Web UI
- **Click** - CLI framework

### Optional LLMs
- **OpenAI** - GPT-3.5, GPT-4
- **HuggingFace** - Any HF model
- **Ollama** - Local LLM running

## ✅ Completion Status

- ✅ Blog 1: Corpus Audit & Quality Baselining
- ✅ Blog 2: Format-Aware Parsing
- ✅ Blog 3: Text Cleaning & Noise Elimination
- ✅ Blog 4: Structured Knowledge Extraction
- ✅ Blog 5: Deduplication & Consolidation
- ✅ Blog 6: Embedding & Retrieval
- ✅ Blog 7: RAG System - User Interface & Deployment

**Status**: 🎉 **Complete & Production Ready**

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas for contribution:
- [ ] Additional LLM integrations
- [ ] Performance optimization
- [ ] New document format support
- [ ] Advanced retrieval strategies

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙋 Support

- 📖 Check [documentation](docs/)
- 🐛 Report issues on [GitHub](https://github.com/docuai/docuai/issues)
- 💬 Start a [discussion](https://github.com/docuai/docuai/discussions)

## 📈 Statistics

| Metric | Count |
|--------|-------|
| **Total Modules** | 50+ |
| **Lines of Code** | ~9,200 |
| **Python Packages** | 30+ |
| **Supported Formats** | 8 |
| **Processing Stages** | 7 |
| **Interface Modes** | 4 |

## 🎓 References

This project implements concepts from:
- Retrieval-Augmented Generation (RAG) papers
- Document parsing best practices
- Text quality metrics
- Deduplication algorithms
- Vector search optimization

---

**Made with ❤️ by the DocuAI Team**

**Latest Update**: April 2024 | **Version**: 1.0.0
