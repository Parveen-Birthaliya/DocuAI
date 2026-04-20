# DocuAI: Multiple-Format RAG System
## Final Year Project - Complete Architecture

**Project Goal:** Build an end-to-end RAG system that processes heterogeneous documents through all 5 blog stages, deployable on laptop & Hugging Face Spaces.

**Corpus Size:** 5 documents × 7 formats = 35 total documents (Minimum Viable Dataset)

---

## Part 0: Technology Stack & Free Tools

| Layer | Tool | Free? | Why This Choice |
|-------|------|-------|-----------------|
| **Language** | Python 3.11+ | ✅ | Universal, best ML ecosystem |
| **Document Parsing** | PyMuPDF (fitz), pdfplumber, beautifulsoup4 | ✅ | Free, no external APIs |
| **OCR** | Tesseract + pytesseract | ✅ | Free, open source (Surya optional for high-value docs) |
| **Embedding** | sentence-transformers (all-MiniLM-L6-v2) | ✅ | Fast, CPU-runnable, 384d |
| **LLM Chat** | Ollama (local) + Hugging Face Inference API | ✅ | Free tier available |
| **Vector DB** | FAISS (CPU) | ✅ | Facebook, no external service |
| **Structured Data** | SQLite (local) + Pandas | ✅ | Laptop-friendly, no network |
| **Task Queue** | APScheduler (local) | ✅ | Lightweight background jobs |
| **Layout Analysis** | Docling (IBM, free) | ✅ | DocLayNet-trained, free |
| **Table Extraction** | pdfplumber + camelot-py | ✅ | Free, open source |
| **Dedup** | datasketch (MinHash) | ✅ | Pure Python, no C++ deps |
| **Data Storage** | JSON files + Pandas + SQLite | ✅ | Laptop-native, versioned |
| **Serving** | Gradio app | ✅ | Easy Hugging Face deployment |

**❌ AVOID:**
- kenlm (too complex to build, use transformer perplexity instead)
- Apache Airflow (too heavy, use APScheduler)
- PySpark (too heavy, use Pandas for 35 docs)
- Cloud APIs (BigQuery, AWS, GCP costs money)
- Large proprietary LLMs (no free quota)

---

## Part 1: Project Structure & Modules

```
DocuAI/
├── README.md
├── requirements.txt
├── config.yaml                          # Pipeline configuration
├── setup.py
│
├── data/
│   ├── raw_corpus/                      # 5 docs per format (35 total)
│   │   ├── pdfs/                        # 5 PDF files (text + scanned mix)
│   │   ├── htmls/                       # 5 HTML pages
│   │   ├── jsons/                       # 5 JSON files
│   │   ├── txts/                        # 5 TXT files
│   │   ├── markdowns/                   # 5 Markdown files
│   │   ├── csvs/                        # 5 CSV files (as SQL-like)
│   │   └── codes/                       # 5 Python script files
│   │
│   ├── processed/
│   │   ├── audit_logs/                  # Blog 1: Audit results
│   │   ├── parsed/                      # Blog 2: Parsed output
│   │   ├── cleaned/                     # Blog 3: Cleaned text
│   │   ├── extracted/                   # Blog 4: Structured data
│   │   ├── deduplicated/                # Blog 5: Final corpus
│   │   └── embeddings.faiss             # Vector store
│   │
│   └── metadata/
│       ├── quality_scores.json          # Blog 1 quality signals
│       ├── routing_table.json           # Blog 1 routing tags
│       ├── dedup_clusters.json          # Blog 5 dedup info
│       └── retrieval_baseline.json      # Blog 5 baseline metrics
│
├── src/
│   ├── __init__.py
│   │
│   ├── blog1_audit/                     # STAGE 1: Corpus Audit
│   │   ├── __init__.py
│   │   ├── auditor.py                   # Main audit engine
│   │   ├── pdf_auditor.py               # PDF-specific audit
│   │   ├── html_auditor.py              # HTML-specific audit
│   │   ├── format_detector.py           # Format detection
│   │   └── quality_scorer.py            # Quality scoring (no kenlm!)
│   │
│   ├── blog2_parsing/                   # STAGE 2: Format-Aware Parsing
│   │   ├── __init__.py
│   │   ├── parser.py                    # Router to format-specific parsers
│   │   ├── pdf_parser.py                # PDF text extraction (reading order)
│   │   ├── pdf_ocr_parser.py            # PDF OCR (Tesseract-based)
│   │   ├── html_parser.py               # HTML DOM extraction
│   │   ├── json_parser.py               # JSON flattening
│   │   ├── code_parser.py               # AST-based code extraction
│   │   └── markdown_parser.py           # Markdown heading extraction
│   │
│   ├── blog3_cleaning/                  # STAGE 3: Text Cleaning
│   │   ├── __init__.py
│   │   ├── cleaner.py                   # Three-tier filtering coordinator
│   │   ├── tier1_heuristics.py          # Heuristic filters (FineWeb)
│   │   ├── tier2_quality.py             # ML-based quality scoring
│   │   ├── tier3_llm.py                 # LLM gate (optional, lite)
│   │   ├── boilerplate_detector.py      # Trafilatura + n-gram analysis
│   │   └── encoding_normalizer.py       # UTF-8 NFC normalization
│   │
│   ├── blog4_extraction/                # STAGE 4: Structured Knowledge
│   │   ├── __init__.py
│   │   ├── extractor.py                 # Main coordinator
│   │   ├── table_extractor.py           # Table extraction (pdfplumber)
│   │   ├── figure_extractor.py          # Figure caption extraction
│   │   └── metadata_enricher.py         # Metadata enrichment
│   │
│   ├── blog5_dedup/                     # STAGE 5: Dedup & Validation
│   │   ├── __init__.py
│   │   ├── deduplicator.py              # Main dedup coordinator
│   │   ├── exact_dedup.py               # SHA-256 exact dedup
│   │   ├── near_dedup.py                # MinHash LSH near-dedup
│   │   ├── validator.py                 # Validation gates
│   │   └── quality_baseline.py          # Baseline metrics
│   │
│   ├── embedding/                       # EMBEDDING & RETRIEVAL
│   │   ├── __init__.py
│   │   ├── embedder.py                  # Embedding engine (sentence-transformers)
│   │   ├── faiss_store.py               # FAISS vector store management
│   │   └── retriever.py                 # Retrieval engine
│   │
│   ├── chunking/                        # CHUNKING (before embedding)
│   │   ├── __init__.py
│   │   ├── chunk_strategy.py            # Generic chunking
│   │   ├── semantic_chunker.py          # Semantic boundary detection
│   │   └── chunk_metadata.py            # Chunk provenance tracking
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                    # Centralized logging
│   │   ├── file_handler.py              # File I/O utilities
│   │   ├── json_store.py                # JSON persistence layer
│   │   ├── time_tracker.py              # Pipeline timing metrics
│   │   └── constants.py                 # Global constants
│   │
│   └── models/
│       ├── __init__.py
│       ├── document.py                  # DocumentQualityScore dataclass
│       ├── chunk.py                     # Chunk dataclass
│       └── retrieval_result.py          # Retrieval result schema
│
├── notebooks/
│   ├── 01_explore_corpus.ipynb          # Exploratory analysis
│   ├── 02_audit_results.ipynb           # Blog 1 visualization
│   ├── 03_parsing_samples.ipynb         # Blog 2 output samples
│   ├── 04_cleaning_analysis.ipynb       # Blog 3 filter impact
│   ├── 05_extraction_examples.ipynb     # Blog 4 tables/figures
│   ├── 06_dedup_clusters.ipynb          # Blog 5 dedup analysis
│   └── 07_retrieval_demo.ipynb          # End-to-end RAG demo
│
├── tests/
│   ├── __init__.py
│   ├── test_blog1_audit.py
│   ├── test_blog2_parsing.py
│   ├── test_blog3_cleaning.py
│   ├── test_blog4_extraction.py
│   ├── test_blog5_dedup.py
│   └── test_retrieval.py
│
├── app.py                               # Gradio interface for demo
├── pipeline.py                          # Main pipeline orchestration
├── run_pipeline.py                      # CLI entry point
│
├── deployment/
│   ├── requirements_docker.txt          # Hugging Face Space requirements
│   ├── Dockerfile                       # (Optional) Docker for Space
│   ├── Space_README.md                  # Hugging Face Space instructions
│   └── hf_space_app.py                  # Modified Gradio for HF Deploy
│
└── docs/
    ├── ARCHITECTURE.md                  (YOU ARE HERE)
    ├── SETUP.md                         # Installation & setup
    ├── PIPELINE_GUIDE.md                # How to run each stage
    ├── CORPUS_PREP.md                   # How to prepare sample docs
    └── DEPLOYMENT.md                    # Laptop → HF Space guide
```

---

## Part 2: Component Architecture

### **System Overview Diagram**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  RAW CORPUS (5 PDFs, 5 HTMLs, 5 JSONs, 5 CSVs, 5 TXTs, 5 MDs, 5 PYs)   │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────────┐
          │  BLOG 1: CORPUS AUDIT & QA SCORING │
          │  ✓ Format detection                │
          │  ✓ Quality scoring (no kenlm)      │
          │  ✓ Routing tags                    │
          └────────────────────────────────────┘
                    audit_logs/*.json
                    routing_table.json
                           │
                           ▼
         ┌──────────────────────────────────────┐
         │ BLOG 2: FORMAT-AWARE PARSING         │
         │ ✓ PDF (text + OCR)                  │
         │ ✓ HTML (trafilatura)                │
         │ ✓ JSON/CSV (schema flattening)      │
         │ ✓ Code (basic AST)                  │
         │ ✓ Markdown (structure preservation) │
         └──────────────────────────────────────┘
                  parsed/*.json
                           │
                           ▼
          ┌─────────────────────────────────────┐
          │ BLOG 3: TEXT CLEANING (3-Tier)      │
          │ ✓ Tier 1: Heuristic filters        │
          │ ✓ Tier 2: ML quality scoring       │
          │ ✓ Tier 3: LLM gate (optional)      │
          │ ✓ Boilerplate detection            │
          └─────────────────────────────────────┘
                   cleaned/*.json
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │ BLOG 4: STRUCTURED KNOWLEDGE         │
        │ ✓ Table extraction                  │
        │ ✓ Figure caption linking            │
        │ ✓ Metadata enrichment               │
        └──────────────────────────────────────┘
               extracted/*.json
                           │
                           ▼
       ┌───────────────────────────────────────┐
       │ BLOG 5: DEDUP & VALIDATION            │
       │ ✓ Exact dedup (SHA-256)              │
       │ ✓ Near-dedup (MinHash LSH)           │
       │ ✓ Validation gates                   │
       │ ✓ Baseline metrics                   │
       └───────────────────────────────────────┘
          deduplicated/*.json
          retrieval_baseline.json
                           │
                           ▼
       ┌───────────────────────────────────────┐
       │ CHUNKING & EMBEDDING                  │
       │ ✓ Semantic chunking                  │
       │ ✓ sentence-transformers              │
       │ ✓ FAISS vector store                 │
       └───────────────────────────────────────┘
           embeddings.faiss + metadata.json
                           │
                           ▼
       ┌───────────────────────────────────────┐
       │ RETRIEVAL & LLM GENERATION            │
       │ ✓ Semantic search (FAISS)            │
       │ ✓ Local LLM (Ollama) or HF API       │
       │ ✓ Gradio UI                         │
       └───────────────────────────────────────┘
           RAG Chat Interface
```

---

## Part 3: Module Dependencies & Data Flow

### **Detailed Data Model**

```
DocumentQualityScore (Blog 1)
├─ doc_id: str
├─ source_path: str
├─ format_type: str (pdf_text | pdf_scanned | html | json | csv | code | markdown)
├─ language: str
├─ perplexity: float (transformer-based, not kenlm!)
├─ char_count, word_count: int
├─ quality_score: float (0-1.0)
├─ requires_special_handling: bool
├─ routing_tag: str  ← CRITICAL: Routes to Blog 2
└─ [Other Blog 1 signals]

↓ (Blog 2 processes using routing_tag)

ParsedDocument
├─ doc_id: str
├─ format_type: str
├─ text: str
├─ layout_metadata: dict (for PDFs: columns, tables, etc.)
├─ heading_path: list (for structured docs)
├─ parse_quality: float
└─ [Blog 2 provenance]

↓ (Blog 3 filters)

CleanedDocument
├─ doc_id: str
├─ text_cleaned: str
├─ encoding_normalized: bool
├─ filters_passed: list[str] (Tier 1, 2, 3 status)
├─ boilerplate_fraction: float
├─ language_consistency: float
└─ [Blog 3 signals]

↓ (Blog 4 extracts structures)

EnrichedDocument
├─ doc_id: str
├─ text_main: str
├─ tables: list[TableExtract]
│  └─ TableExtract: {id, summary, json_repr, location}
├─ figures: list[FigureMetadata]
├─ metadata: dict {source, date, author, version, doc_type}
└─ [Blog 4 enrichments]

↓ (Blog 5 deduplicates)

DedupDocument
├─ doc_id: str
├─ content_hash: str (SHA-256)
├─ exact_dup_status: str | None
├─ near_dup_cluster_id: str | None
├─ minhash_signature: list[int]
├─ is_canonical: bool
└─ [Blog 5 dedup info]

↓ (Chunking before embedding)

Chunk
├─ chunk_id: str
├─ doc_id: str
├─ text: str
├─ chunk_type: str (main_text | table | figure_caption | metadata)
├─ provenance: {source_location, format_type, blog_stage}
├─ chunk_score: float (quality indicator)
├─ global_rank: int (for topk retrieval)
└─ embedding: None (computed at embedding stage)

↓ (Embedding)

IndexedChunk
├─ chunk_id: str
├─ embedding: np.array (384-dim, sentence-transformers)
├─ metadata: dict
└─ [FAISS indexed]

↓ (Retrieval)

RetrievalResult
├─ query: str
├─ retrieved_chunks: list[Chunk]
├─ scores: list[float]
├─ metadata: dict
└─ [For LLM generation]
```

---

## Part 4: Stage-by-Stage Implementation Plan

### **STAGE 1: Blog 1 — Corpus Audit & Quality Baselining**

**Inputs:** Raw files from `data/raw_corpus/`

**Outputs:**
- `data/metadata/quality_scores.json` — All 35 docs with quality vectors
- `data/metadata/routing_table.json` — Format → parsing strategy mapping
- `data/processed/audit_logs/` — Detailed per-doc audit logs

**Key Components:**
```
blog1_audit/
├── format_detector.py
│   └─ Detects format from file extension + magic bytes
│   └─ classify_pdf(): pdf_text vs pdf_scanned
│   └─ classify_html(): measure content ratio with trafilatura
│
├── quality_scorer.py
│   └─ NO kenlm! Use transformers perplexity instead
│   └─ Language detection: FastText or transformers
│   └─ Perplexity: GPT-2 model from transformers (free, CPU-runnable)
│   └─ Boilerplate detection: n-gram analysis
│
├── pdf_auditor.py
│   └─ OCR quality check via character density
│   └─ Multi-column detection via x-coordinate clustering
│   └─ Text vs scanned classification
│
├── html_auditor.py
│   └─ Content ratio: trafilatura extraction / total text
│   └─ Heading hierarchy analysis
│   └─ Table density measurement
│
└── auditor.py (orchestrator)
    └─ Runs all 35 docs
    └─ Produces routing_table.json
    └─ Logs quality_scores.json
```

**Key Functions:**
- `audit_corpus()` — Main entry point
- `detect_format()` — Format classification
- `score_quality()` — Perplexity + language score (NO kenlm!)
- `route_document()` — Assigns routing_tag
- `save_audit_results()` — Persists JSON

---

### **STAGE 2: Blog 2 — Format-Aware Parsing**

**Inputs:** Raw files + routing_table.json from Blog 1

**Outputs:**
- `data/processed/parsed/` — One JSON per document with structured text

**Key Components:**
```
blog2_parsing/
├── parser.py (router)
│   └─ Reads routing_table.json
│   └─ Dispatches each doc to correct format parser
│
├── pdf_parser.py
│   └─ PyMuPDF for text PDFs
│   └─ Reading order reconstruction: column detection + y-sort
│   └─ No layout analysis needed for 5 text PDFs
│
├── pdf_ocr_parser.py
│   └─ Tesseract via pytesseract for scanned PDFs
│   └─ Simple per-page extraction (no Docling complexity)
│   └─ Handles 5 scanned PDFs if any
│
├── html_parser.py
│   └─ trafilatura.extract() for main content
│   └─ BeautifulSoup for heading structure
│   └─ Removes boilerplate automatically
│
├── json_parser.py
│   └─ Flatten nested JSON to text
│   └─ Preserve key names for context
│
├── code_parser.py
│   └─ Basic AST parsing for Python files
│   └─ Extract functions, classes, docstrings
│
└── markdown_parser.py
    └─ Extract heading hierarchy
    └─ Preserve # structure (not just text)
```

**Key Functions:**
- `parse_document()` — Main entry point (uses routing_tag)
- `parse_pdf_text()` — Reading order reconstruction
- `parse_pdf_scanned()` — Tesseract OCR
- `parse_html()` — Trafilatura extraction
- `parse_json()` — Recursive flattening
- `parse_code()` — AST extraction
- `parse_markdown()` — Structure preservation

---

### **STAGE 3: Blog 3 — Text Cleaning (3-Tier)**

**Inputs:** parsed/*.json from Blog 2

**Outputs:**
- `data/processed/cleaned/` — Filtered, normalized docs
- `data/processed/audit_logs/cleaning_decisions.json` — Why each doc kept/removed

**Key Components:**
```
blog3_cleaning/
├── tier1_heuristics.py
│   └─ Word count bounds (50-100k)
│   └─ Mean word length (3-10 chars)
│   └─ Symbol ratio (<10%)
│   └─ Repetition detection (duplicate lines, n-grams)
│   └─ Terminal punctuation (C4 filter)
│   └─ Cost: ~1ms/doc, 99% throughput
│
├── tier2_quality.py
│   └─ Perplexity threshold (GPT-2)
│   └─ Language confidence threshold
│   └─ Encoding consistency check
│   └─ Cost: ~100ms/doc, 95% of Tier 1 survivors
│
├── tier3_llm.py (optional, disable for laptop)
│   └─ Use HF Inference API free tier
│   └─ Semantic coherence check
│   └─ Only applied to borderline cases (~5% of corpus)
│
├── boilerplate_detector.py
│   └─ trafilatura for HTML
│   └─ Corpus-level n-gram analysis (8-grams)
│   └─ Finds phrases in >5% of docs = boilerplate
│   └─ Strips boilerplate phrases
│
├── encoding_normalizer.py
│   └─ UTF-8 NFC normalization
│   └─ Mojibake detection & repair
│   └─ Invalid character removal
│
└── cleaner.py (orchestrator)
    └─ Sequential filtering: Tier 1 → Tier 2 → Tier 3
    └─ Preserves audit log for each rejection
    └─ Outputs cleaned_corpus_v1
```

**Key Functions:**
- `clean_corpus()` — Main orchestrator
- `tier1_heuristics_filter()` — Fast pass/fail
- `tier2_quality_score()` — ML-based filtering
- `tier3_llm_gate()` — LLM-based final check (optional)
- `detect_and_strip_boilerplate()` — Corpus-level analysis
- `normalize_encoding()` — UTF-8 normalization

---

### **STAGE 4: Blog 4 — Structured Knowledge Extraction**

**Inputs:** cleaned/*.json from Blog 3

**Outputs:**
- `data/processed/extracted/` — Tables, figures, metadata extracted
- `data/processed/extracted/tables.json` — All tables with summaries
- `data/processed/extracted/figures.json` — Figure metadata

**Key Components:**
```
blog4_extraction/
├── table_extractor.py
│   └─ pdfplumber for text PDFs (simple!)
│   └─ Camelot for scanned PDFs
│   └─ Pandas for CSVs (simpler case)
│   └─ Outputs: {table_id, summary, json_repr, location}
│
├── figure_extractor.py
│   └─ Extract image objects from PDFs
│   └─ Link captions to figures
│   └─ Basic cross-reference parsing ("Figure 1 shows...")
│
├── metadata_enricher.py
│   └─ Extract document metadata: source, date, author
│   └─ Section hierarchy from headings
│   └─ Document type classification (report, spec, article, etc.)
│
└── extractor.py (orchestrator)
    └─ Runs per-document extraction
    └─ Creates enriched_corpus_v1
```

**Key Functions:**
- `extract_tables_from_pdf()` — pdfplumber/camelot
- `extract_tables_from_csv()` — Pandas
- `extract_figures()` — Image extraction
- `extract_metadata()` — Doc-level metadata
- `generate_table_summary()` — Natural language summary

---

### **STAGE 5: Blog 5 — Deduplication & Validation**

**Inputs:** extracted/*.json from Blog 4

**Outputs:**
- `data/processed/deduplicated/` — Final canonical corpus
- `data/metadata/dedup_clusters.json` — Dedup decisions
- `data/metadata/retrieval_baseline.json` — Baseline metrics

**Key Components:**
```
blog5_dedup/
├── exact_dedup.py
│   └─ SHA-256 hashing of normalized text
│   └─ Keep newest version of duplicates
│   └─ Logs exact_dup_cluster_id for rejects
│
├── near_dedup.py
│   └─ MinHash LSH from datasketch
│   └─ Jaccard threshold: calibrated per corpus
│   └─ 5-gram shingles, 128 hash functions
│   └─ Finds similar docs (paraphrased, versioned)
│
├── validator.py
│   └─ Schema validation (Great Expectations-lite)
│   └─ Chunk coherence scoring
│   └─ Structural integrity checks
│
├── quality_baseline.py
│   └─ Embed 5% of corpus (sample)
│   └─ Create reference query set (200 queries)
│   └─ Measure baseline metrics: precision@5, RAGAS
│
└── deduplicator.py (orchestrator)
    └─ Exact dedup → Near dedup → Validation
    └─ Produces deduplicated_corpus_v1
    └─ Sets up baseline metrics
```

**Key Functions:**
- `exact_dedup()` — SHA-256 based
- `near_dedup()` — MinHash LSH
- `calibrate_jaccard_threshold()` — Find optimal threshold
- `validate_corpus()` — Schema + coherence checks
- `establish_baseline()` — Baseline metrics

---

## Part 5: Chunking & Embedding Strategy

### **Chunking Module**

**Input:** deduplicated_corpus_v1 from Blog 5

**Output:** chunks.json (all chunks with metadata)

```
src/chunking/
├── chunk_strategy.py
│   └─ Fixed-size chunking: 512 tokens, 100 token overlap
│   └─ Semantic boundaries: split at paragraph ends
│   └─ Preserve heading structure for hierarchical chunks
│
├── semantic_chunker.py
│   └─ Split at sentence boundaries (not mid-word)
│   └─ Use spaCy for sentence tokenization
│   └─ Don't chunk across table boundaries
│
└── chunk_metadata.py
    └─ Track: chunk_id, doc_id, source_location, format_type
    └─ Attach Blog 1-5 metadata to each chunk
```

**Key Challenge:** Balance between:
- Too small chunks: poor context for LLM
- Too large chunks: poor retrieval precision
- **Solution:** 512 tokens with semantic boundaries

---

### **Embedding Module**

**Input:** chunks.json

**Output:** embeddings.faiss + chunk_metadata.json

```
src/embedding/
├── embedder.py
│   └─ Model: sentence-transformers/all-MiniLM-L6-v2
│   └─ Dims: 384
│   └─ Speed: ~50k chunks/min on CPU
│   └─ Cost: FREE (no API calls)
│
├── faiss_store.py
│   └─ FAISS CPU index (no GPU needed)
│   └─ Save to embeddings.faiss (laptop-friendly)
│   └─ Load in <1 second
│
└── retriever.py
    └─ Semantic search via FAISS
    └─ Return top-k with metadata
```

**Key Functions:**
- `embed_chunks()` — Batch embedding
- `save_to_faiss()` — Persist index
- `semantic_search()` — Query embedding + retrieval

---

## Part 6: Retrieval & LLM Interface

### **Retrieval Stack**

```
src/embedding/retriever.py
├─ Query embedding (same model: all-MiniLM-L6-v2)
├─ Semantic search (FAISS.search())
├─ Rerank by metadata (recency, source reliability)
├─ Return top-5 chunks + metadata
└─ Format as context for LLM

app.py (Gradio Interface)
├─ Input: User query
├─ Process: Embed → FAISS search → Retrieve context
├─ LLM Options:
│  ├─ Ollama (local, free, requires Ollama installed)
│  └─ Hugging Face Inference API (free tier, online)
├─ Output: Query + Retrieved context + LLM response
└─ Gradio handles web UI
```

---

## Part 7: Deployment Targets

### **Target 1: Laptop (Development)**

**Requirements:**
- Python 3.11+
- ~4GB RAM (embeddings + FAISS)
- ~500MB disk (for all data + embeddings)
- Optional: Ollama for local LLM

**Run:**
```bash
python run_pipeline.py --stage all  # Run full 5-blog pipeline
python app.py                       # Start Gradio UI
```

---

### **Target 2: Hugging Face Spaces (Production)**

**How it works:**
- Hugging Face Spaces runs Gradio apps free
- Pre-process corpus on laptop → upload embeddings.faiss
- User queries: Spaces handles search + response
- Uses HF Inference API free tier for LLM

**Deployment Process:**
1. Create Hugging Face account (free)
2. Set up git repo: `huggingface_hub`
3. Upload code + embeddings to Space
4. Spaces runs Gradio app automatically
5. Share URL with anyone → instant RAG demo!

**Pre-processing:** All heavy lifting (Blogs 1-5) runs on laptop, outputs are lightweight JSON files + FAISS index.

---

## Part 8: Free Tech Stack Summary & Why These Choices

| Component | Tool | Free? | Reason |
|-----------|------|-------|--------|
| PDF Text | PyMuPDF (fitz) | ✅ | Better parsing than pdfplumber |
| PDF OCR | Tesseract | ✅ | Free, open source, apt-get install |
| Tables | pdfplumber + camelot | ✅ | Zero cost, good accuracy |
| HTML | trafilatura | ✅ | Boilerplate removal built-in |
| Language | fasttext-language (or transformers) | ✅ | Fast language detection |
| Perplexity | transformers (GPT-2) | ✅ | Replaces kenlm (which doesn't work) |
| Embeddings | sentence-transformers (all-MiniLM) | ✅ | 384d, CPU-runnable, fast |
| Vector DB | FAISS | ✅ | Meta's open source, CPU-only |
| LLM | Ollama (local) + HF Inference | ✅ | Free tier available |
| UI | Gradio | ✅ | Deploy to HF Spaces free |
| Dedup | datasketch | ✅ | Pure Python MinHash |
| Orchestration | APScheduler | ✅ | Lightweight, no Airflow overhead |

---

## Part 9: Minimal Corpus Structure (7 Formats × 5 Docs)

```
data/raw_corpus/

## 1. PDFs (2 text, 1 scanned)
├── pdfs/
│   ├── academic_paper_1.pdf         (regular PDF - text extractable)
│   ├── financial_report_1.pdf       (2-column layout - needs heading structure)
│   ├── old_scanned_doc_1.pdf        (OCR needed)
│   ├── technical_spec_1.pdf         (tables + structure)
│   └── whitepaper_1.pdf             (standard)

## 2. HTMLs (5)
├── htmls/
│   ├── wikipedia_article_1.html     (navigation boilerplate)
│   ├── blog_post_1.html             (header/footer)
│   ├── documentation_1.html         (code + text mix)
│   ├── news_article_1.html          (ads, comments)
│   └── product_page_1.html          (structured data)

## 3. JSONs (5)
├── jsons/
│   ├── api_response_1.json          (nested structure)
│   ├── config_file_1.json           (key-value structure)
│   ├── dataset_1.json               (array of objects)
│   ├── log_entries_1.json           (timestamp+message)
│   └── structured_data_1.json       (complex schema)

## 4. CSVs (treated as SQL-like) (5)
├── csvs/
│   ├── financial_data_1.csv         (table with headers)
│   ├── user_data_1.csv              (large CSV)
│   ├── measurements_1.csv           (numeric table)
│   ├── survey_results_1.csv         (categorical)
│   └── timeseries_1.csv             (temporal data)

## 5. TXTs (5)
├── txts/
│   ├── book_excerpt_1.txt           (long prose)
│   ├── README_1.txt                 (formatted text)
│   ├── log_file_1.txt               (repetitive lines)
│   ├── transcript_1.txt             (dialog + timestamps)
│   └── email_1.txt                  (multi-part message)

## 6. Markdowns (5)
├── mds/
│   ├── guide_1.md                   (headings + lists)
│   ├── readme_1.md                  (structured)
│   ├── tutorial_1.md                (steps with code)
│   ├── faq_1.md                     (Q&A structure)
│   └── changelog_1.md               (version history)

## 7. Python Code (5)
└── codes/
    ├── utils_1.py                   (utility functions)
    ├── data_processor_1.py          (classes, docstrings)
    ├── config_parser_1.py           (simple script)
    ├── api_client_1.py              (async patterns)
    └── main_app_1.py                (full application)
```

**Total:** 5 × 7 = 35 documents (Minimum viable for showing all blog concepts)

---

## Part 10: Key Implementation Decisions

### **Decision 1: NO kenlm — Use Transformers GPT-2 Instead**

**Why:** kenlm requires C++ compilation, ARPA model download, complex setup. For 35 docs, it's overkill.

**Solution:**
```python
# Instead of kenlm:
from transformers import GPT2Tokenizer, GPT2LMHeadModel

def compute_perplexity(text: str) -> float:
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    
    tokens = tokenizer.encode(text)
    loss = model(torch.tensor([tokens]), labels=torch.tensor([tokens])).loss
    return torch.exp(loss).item()
```

✅ Free, CPU-runnable, no compilation needed

---

### **Decision 2: Laptop-Friendly Storage — JSON + SQLite, No Delta Lake**

**Why:** Delta Lake is overkill for 35 docs. JSON + Pandas + SQLite is faster to prototype.

**Solution:**
- Quality scores → `quality_scores.json` (JSON)
- Parsed docs → `parsed/{doc_id}.json` (one file per doc)
- Embeddings → `embeddings.faiss` (FAISS binary format)
- Metadata → `chunk_metadata.json` (JSON lines format)

✅ Laptop-native, fast loads, human-readable

---

### **Decision 3: Elastic Scale — Start Simple, Grow Complex**

**Blog 1-2:** Basic format detection + parsing (no Docling, no LayoutLMv3 for 5 PDFs)

**Blog 3:** Standard heuristics + basic ML (Tier 3 LLM gate is optional)

**Blog 4:** pdfplumber for tables (not TATR for 5 docs)

**Blog 5:** datasketch MinHash (not Spark MLlib for 35 docs)

✅ Scales from laptop to 10TB if needed, but starts simple

---

### **Decision 4: No External APIs (Except Hugging Face Inference Optional)**

- All text processing: local (transformers, NLTK, spaCy)
- All embeddings: local (sentence-transformers)
- Vector search: local (FAISS)
- LLM: Ollama (local) or HF Inference (free tier, online)

✅ Zero cost, works offline

---

## Part 11: Success Metrics for Final Year Project

### **Completion Checklist:**

- [ ] Blog 1: Audit all 35 docs, generate quality_scores.json + routing_table.json
- [ ] Blog 2: Parse all docs using format-specific strategies
- [ ] Blog 3: Clean corpus through 3-tier filtering
- [ ] Blog 4: Extract tables + figures from relevant docs
- [ ] Blog 5: Deduplicate + validate final corpus
- [ ] Chunking: Split into ~500-token semantic chunks
- [ ] Embedding: Generate FAISS index (all-MiniLM-L6-v2)
- [ ] Retrieval: Semantic search working end-to-end
- [ ] UI: Gradio interface for querying
- [ ] Deployment: Working Hugging Face Space (or docker file)

### **Quality Metrics:**

- **Precision:** Top-5 retrieval contains ≥ 3 relevant chunks
- **Diversity:** No more than 2 chunks from same document in top-10
- **Latency:** Query → results < 500ms (laptop)
- **Throughput:** All 35 docs through full pipeline < 5 minutes

---

## Part 12: Project Timeline (Recommended for Semester)

**Week 1-2:** Setup + Corpus prep
- Install dependencies
- Create 35 sample documents (7 formats × 5 each)
- Set up directory structure

**Week 3-4:** Blog 1-2 Implementation
- Format detection
- Quality scoring (without kenlm)
- Format-aware parsing (all 7 formats)

**Week 5-6:** Blog 3 Implementation
- Tier 1 heuristics
- Tier 2 ML quality
- Boilerplate detection

**Week 7-8:** Blog 4-5 Implementation
- Table extraction
- Deduplication (exact + near-dedup)
- Validation gates

**Week 9-10:** Embedding + Retrieval
- Chunking strategy
- FAISS embedding
- Semantic search

**Week 11-12:** UI + Deployment
- Gradio interface
- Local Ollama setup (or HF Inference)
- Deploy to Hugging Face Spaces
- Testing + documentation

---

## Next Steps

**ACTION ITEMS:**

1. ✅ You have the architecture document (you're reading it now)
2. → Next: I'll create the **project skeleton** (all directories + init files)
3. → Then: **Blog 1 implementation** (complete, working code)
4. → Then: **Blog 2, 3, 4, 5** (modular, one by one)
5. → Finally: **Retrieval UI + deployment**

Each module will be **complete, tested, and working** (no placeholders).

---

**This architecture is production-tested (conceptually) on the full 10TB, but implemented for your 35-doc laptop project. All decisions prioritize**: ✅ **Working code > fancy architecture** and ✅ **Free tech stack > premium services.**

Ready to start building? Type "ready" and I'll create all the project files!
