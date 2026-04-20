"""
Global constants for DocuAI RAG pipeline.
"""

# Supported formats
SUPPORTED_FORMATS = {
    "pdf": "application/pdf",
    "html": "text/html",
    "json": "application/json",
    "csv": "text/csv",
    "txt": "text/plain",
    "md": "text/markdown",
    "py": "text/x-python",
}

FORMAT_EXTENSIONS = {
    ".pdf": "pdf",
    ".html": "html",
    ".htm": "html",
    ".json": "json",
    ".csv": "csv",
    ".txt": "txt",
    ".md": "md",
    ".markdown": "md",
    ".py": "py",
}

# Blog stages
BLOG_STAGES = {
    1: "corpus_audit",
    2: "format_parsing",
    3: "text_cleaning",
    4: "knowledge_extraction",
    5: "deduplication",
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    "min_word_count": 50,
    "max_word_count": 100_000,
    "min_mean_word_length": 3.0,
    "max_mean_word_length": 10.0,
    "max_symbol_ratio": 0.10,
    "min_alpha_ratio": 0.70,
}

# Embedding settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBEDDING_BATCH_SIZE = 32
EMBEDDING_DEVICE = "cpu"

# Chunking settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 100
DEFAULT_MIN_CHUNK_SIZE = 50

# Retrieval settings
DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.0

# Deduplication settings
JACCARD_THRESHOLD = 0.80
MINHASH_NUM_PERM = 128
MINHASH_NGRAM_SIZE = 5

# LLM Settings
DEFAULT_LLM_MAX_LENGTH = 512
DEFAULT_LLM_TEMPERATURE = 0.7
DEFAULT_LLM_TOP_P = 0.9

# OCR Settings
OCR_ENGINE = "tesseract"

# Paths (relative to project root)
DEFAULT_RAW_CORPUS_PATH = "data/raw_corpus"
DEFAULT_PROCESSED_PATH = "data/processed"
DEFAULT_METADATA_PATH = "data/metadata"
DEFAULT_EMBEDDINGS_PATH = "data/processed/embeddings.faiss"
