# Documentation

DocuAI comprehensive documentation organized by category.

## Quick Start

- [Quickstart Guide](guides/QUICKSTART.md) - Get up and running in 5 minutes

## Implementation Details

- [Architecture Overview](implementation/PROJECT_ARCHITECTURE.md) - System design and component overview
- [Implementation Summary](implementation/IMPLEMENTATION_SUMMARY.md) - Full technical implementation details
- [Delivery Summary](implementation/DELIVERY_SUMMARY.md) - Project completion and statistics

## Blog References

For detailed information about each blog stage, see the [archive/blog_docs](../archive/blog_docs/) folder:

- `STAGE_1_COMPLETE.md` - Corpus Audit & Quality Baselining
- `STAGE_2_COMPLETE.md` - Format-Aware Parsing
- `STAGE_3_COMPLETE.md` - Text Cleaning & Noise Elimination
- `STAGE_4_COMPLETE.md` - Structured Knowledge Extraction
- `STAGE_5_COMPLETE.md` - Deduplication & Consolidation
- `STAGE_6_COMPLETE.md` - Embedding & Retrieval
- `STAGE_7_COMPLETE.md` - RAG System - UI & Deployment

Plus original blog research documents:
- `blog1_corpus_audit_quality_baselining.md`
- `blog2_format_aware_parsing.md`
- `blog3_text_cleaning_noise_elimination.md`
- `blog4_structured_knowledge_extraction.md`
- `blog5_deduplication_validation_feedback.md`

## API Reference

### Core Modules

#### Blog 1: Corpus Audit
```python
from src.blog1_audit import CorpusAuditor
auditor = CorpusAuditor()
summary = auditor.audit_corpus()
```

#### Blog 2: Format Parsing
```python
from src.blog2_parsing import FormatAwareParser
parser = FormatAwareParser()
results = parser.parse_corpus()
```

#### Blog 3: Text Cleaning
```python
from src.blog3_cleaning import TextCleaner
cleaner = TextCleaner()
cleaned = cleaner.clean_corpus()
```

#### Blog 4: Knowledge Extraction
```python
from src.blog4_extraction import run_extraction
results = run_extraction()
```

#### Blog 5: Deduplication
```python
from src.blog5_dedup import run_blog5
results = run_blog5(config)
```

#### Blog 6: Embedding & Retrieval
```python
from src.blog6_embedding import run_blog6, load_retriever
results = run_blog6(config)
retriever = load_retriever(config)
results = retriever.retrieve("query", top_k=5)
```

#### Blog 7: RAG Interfaces
```python
from src.blog7_rag import run_blog7_rag, Blog7Orchestrator

# CLI Mode
run_blog7_rag(retriever, mode="cli")

# API Mode
run_blog7_rag(retriever, mode="api", port=5000)

# Streamlit Mode
run_blog7_rag(retriever, mode="streamlit")

# Or use orchestrator directly
orchestrator = Blog7Orchestrator(retriever, llm_model="mock")
orchestrator.run_cli_interactive()
```

## Configuration

See [config.yaml](../config.yaml) for all configuration options.

Common settings:
- `data_dir` - Data directory path
- `processed_path` - Processed data output path
- `embedding_model` - Which embedding model to use
- `chunk_size` - Document chunk size (default: 512)
- `chunk_overlap` - Chunk overlap (default: 50)

## Deployment

- **Hugging Face Spaces** - Upload to HF Spaces for web UI
- **Docker** - Containerize for cloud deployment
- **Local** - Run on your machine

See [Quickstart Guide](guides/QUICKSTART.md) for detailed deployment instructions.

## Contributing

Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Support

- Check existing issues on GitHub
- Review documentation in this folder
- Open a new issue for bugs or feature requests

## License

MIT License - See [LICENSE](../LICENSE) for details.
