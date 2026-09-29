"""
Dask Partition Loader for Project Aurora
Provides memory-disciplined distributed data structures for partitioned telemetry.
"""

from typing import Optional, List, Dict
import os
import logging

logger = logging.getLogger("aurora.ingestion.dask")


def load_partitioned_telemetry(
    file_pattern: str,
    columns: Optional[List[str]] = None,
    blocksize: str = "64MB",
):
    """
    Lazily loads telemetry files into a Dask DataFrame with controlled partition sizes.
    `blocksize` ensures partitions stay within safe memory bounds during execution.
    """
    try:
        import dask.dataframe as dd
    except ImportError:
        logger.warning("Dask is not installed. Dask loading disabled.")
        return None

    if file_pattern.endswith(".parquet") or "parquet" in file_pattern:
        logger.info(f"Loading parquet partitions from: {file_pattern}")
        return dd.read_parquet(file_pattern, columns=columns)
    else:
        logger.info(f"Loading CSV partitions with blocksize {blocksize} from: {file_pattern}")
        return dd.read_csv(file_pattern, usecols=columns, blocksize=blocksize)
