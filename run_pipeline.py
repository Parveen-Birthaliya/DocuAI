#!/usr/bin/env python3
"""
CLI entry point for DocuAI RAG pipeline.

Usage:
    python run_pipeline.py --stage all
    python run_pipeline.py --stage blog1
    python run_pipeline.py --stage blog2 --config /path/to/config.yaml
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipeline import run_pipeline
from src.utils import logger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DocuAI RAG Pipeline - Multi-format document processing"
    )
    
    parser.add_argument(
        "--stage",
        default="all",
        choices=["all", "blog1", "blog2", "blog3", "blog4", "blog5"],
        help="Which pipeline stage to run (default: all)",
    )
    
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml (default: ./config.yaml)",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    logger.info(f"DocuAI Pipeline starting: stage={args.stage}, config={args.config}")
    
    try:
        run_pipeline(stage=args.stage, config_path=args.config)
        logger.info("Pipeline completed successfully!")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
