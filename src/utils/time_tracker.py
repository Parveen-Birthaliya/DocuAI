"""
Time tracking utilities for pipeline performance monitoring.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime
import json
from .json_store import JSONStore
from .logger import logger


class TimeTracker:
    """Track execution time of pipeline stages."""
    
    def __init__(self):
        self.timings: Dict[str, Dict[str, Any]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start(self, stage_name: str) -> None:
        """Start timing a stage."""
        self.start_times[stage_name] = time.time()
        logger.info(f"Starting: {stage_name}")
    
    def end(self, stage_name: str, item_count: int = 1) -> float:
        """
        End timing a stage.
        
        Args:
            stage_name: Name of stage
            item_count: Number of items processed
        
        Returns:
            Elapsed time in seconds
        """
        if stage_name not in self.start_times:
            logger.warning(f"No start time for {stage_name}")
            return 0.0
        
        elapsed = time.time() - self.start_times[stage_name]
        
        self.timings[stage_name] = {
            "elapsed_seconds": round(elapsed, 2),
            "items_processed": item_count,
            "items_per_second": round(item_count / elapsed, 2) if elapsed > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(
            f"Completed: {stage_name} ({item_count} items in {elapsed:.2f}s)"
        )
        
        del self.start_times[stage_name]
        return elapsed
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all timings."""
        total_time = sum(t["elapsed_seconds"] for t in self.timings.values())
        total_items = sum(t["items_processed"] for t in self.timings.values())
        
        return {
            "stages": self.timings,
            "total_time_seconds": round(total_time, 2),
            "total_items_processed": total_items,
            "average_items_per_second": round(
                total_items / total_time, 2
            ) if total_time > 0 else 0,
        }
    
    def save(self, path: str) -> None:
        """Save timings to JSON file."""
        JSONStore.save_single(self.get_summary(), path, pretty=True)
        logger.info(f"Saved timing report: {path}")
    
    def print_summary(self) -> None:
        """Print timing summary to console."""
        summary = self.get_summary()
        print("\n" + "=" * 60)
        print("PIPELINE TIMING SUMMARY")
        print("=" * 60)
        for stage, timing in summary["stages"].items():
            print(
                f"{stage:30} | Time: {timing['elapsed_seconds']:8.2f}s | "
                f"Items: {timing['items_processed']:5} | "
                f"Rate: {timing['items_per_second']:8.2f} items/s"
            )
        print("-" * 60)
        print(f"Total time: {summary['total_time_seconds']:.2f}s")
        print(f"Total items: {summary['total_items_processed']}")
        print(f"Avg rate: {summary['average_items_per_second']:.2f} items/s")
        print("=" * 60 + "\n")


# Global time tracker
tracker = TimeTracker()
