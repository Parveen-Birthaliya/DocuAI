# Quick Start Guide for DocuAI

## What You Have (STAGE 1)

✅ **Complete project skeleton** with:
- All 7-level directory structure
- Core data models (Document, Chunk, RetrievalResult)
- Utilities (logging, file handling, JSON persistence)
- Configuration system (config.yaml)
- Pipeline orchestrator skeleton
- CLI entry point

## Next: Installation

### 1. Create Virtual Environment

```bash
cd ~/Project/RAG/DocuAI
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Download spaCy models (for sentence tokenization)
python -m spacy download en_core_web_sm

# (Optional) Get FastText language detection model
python -c "import fasttext; fasttext.load_model('lid.176.bin')" 2>/dev/null || echo "Model will download on first use"
```

### 3. Verify Installation

```bash
# Test imports
python -c "from src.utils import logger; logger.info('Setup successful!')"

# Check config loads
python -c "from src.config import get_config; print(get_config())"

# Try CLI
python run_pipeline.py --help
```

## Sample Corpus Setup

### Download Or Create Minimal Test Documents

For testing, create 5 documents of each type in `data/raw_corpus/`:

```bash
# Create directories
mkdir -p data/raw_corpus/{pdfs,htmls,jsons,csvs,txts,mds,codes}

# Add some minimal test files:
# - data/raw_corpus/pdfs/test_1.pdf
# - data/raw_corpus/htmls/test_1.html
# - data/raw_corpus/jsons/test_1.json
# - etc.
```

**See `docs/CORPUS_PREP.md` for detailed corpus preparation** (created in next stage).

## Architecture at a Glance

```
Raw Documents (35)
    ↓
Blog 1: Audit (format detection, quality scoring)
    ↓
Blog 2: Parsing (format-specific extraction)
    ↓
Blog 3: Cleaning (3-tier filtering, boilerplate removal)
    ↓
Blog 4: Extraction (tables, figures, metadata)
    ↓
Blog 5: Dedup (SHA-256 + MinHash LSH)
    ↓
Chunking (semantic boundaries)
    ↓
Embedding (sentence-transformers → FAISS)
    ↓
Retrieval (semantic search)
    ↓
LLM (Ollama or HF Inference)
    ↓
Gradio UI
```

## Files To Know

### Core Files
- `config.yaml` - All pipeline settings
- `pipeline.py` - Main orchestrator
- `run_pipeline.py` - CLI entry point

### Data Models
- `src/models/document.py` - DocumentQualityScore
- `src/models/chunk.py` - Chunk, IndexedChunk
- `src/models/retrieval_result.py` - RetrievalResult

### Utilities
- `src/utils/logger.py` - Logging configuration
- `src/utils/json_store.py` - JSON persistence
- `src/utils/time_tracker.py` - Pipeline timing
- `src/config.py` - Configuration loader

### Modules
- `src/audit/` - Stage 1: Corpus Audit
- `src/parsing/` - Stage 2: Format Parsing
- `src/cleaning/` - Stage 3: Text Cleaning
- `src/extraction/` - Stage 4: Knowledge Extraction
- `src/dedup/` - Stage 5: Deduplication
- `src/embedding/` - Stage 6: Embeddings & Retrieval
- `src/rag/` - Stage 7: RAG Interfaces
- `src/utils/` - Shared utilities
- `src/models/` - Data models

## Next Steps

### STAGE 2 (Stage 1 Implementation)
Implemented:
- `src/audit/format_detector.py`
- `src/audit/quality_scorer.py` (no kenlm!)
- `src/audit/auditor.py` (orchestrator)

**Timeline:** ~1-2 week sprint

### To Get Started on STAGE 2
Run the CLI to confirm it's wired up:
```bash
python run_pipeline.py --stage blog1
```

You'll see: `"Blog 1 auditor not yet implemented (STAGE 2)"` - this is expected!

---

**Status:** Foundation complete ✅  
**Next:** Blog 1 (Corpus Audit) implementation  
**Questions?** Refer to PROJECT_ARCHITECTURE.md
