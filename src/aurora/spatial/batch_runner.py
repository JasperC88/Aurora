"""
Batch Runner CLI for Project Aurora
Orchestrates memory-bounded chunked spatial processing across telemetry files.
"""

import argparse
import glob
import os
import sys
import logging
import pandas as pd
from typing import List

from .geometries import RegionManager
from .spatial_join import SpatialJoinEngine
from .probing_metrics import aggregate_probing_events
from ..utils.memory import MemoryGuard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aurora.batch_runner")


def run_pipeline(
    regions_path: str,
    input_pattern: str,
    output_path: str,
    chunk_size: int = 50000,
    memory_budget_mb: float = 512.0,
):
    logger.info(f"Initializing RegionManager with: {regions_path}")
    rm = RegionManager(regions_path)

    # In a full run, we construct GeoDataFrame for region polygons
    try:
        import geopandas as gpd
        features = []
        for r_id, r_data in rm.regions.items():
            features.append({
                "region_id": r_id,
                "name": r_data["name"],
                "min_altitude_ft": r_data["min_altitude_ft"],
                "max_altitude_ft": r_data["max_altitude_ft"],
                "geometry": r_data["geometry"]
            })
        region_gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
    except ImportError:
        logger.error("GeoPandas is not installed. Aborting batch run.")
        sys.exit(1)

    engine = SpatialJoinEngine(target_region_gdf=region_gdf)

    # Resolve input files
    input_files = glob.glob(input_pattern)
    if not input_files:
        logger.warning(f"No files found matching input pattern: {input_pattern}")
        return

    logger.info(f"Found {len(input_files)} input files. Processing with chunk size {chunk_size}...")

    all_detections: List[pd.DataFrame] = []

    with MemoryGuard("BatchPipeline", max_allowed_mb=memory_budget_mb):
        for file_path in input_files:
            logger.info(f"Processing: {file_path}")
            if file_path.endswith(".csv"):
                # Stream CSV in chunks
                for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                    joined = engine.process_chunk(chunk)
                    if not joined.empty:
                        all_detections.append(joined)
            elif file_path.endswith(".parquet"):
                # Read parquet
                df = pd.read_parquet(file_path)
                joined = engine.process_chunk(df)
                if not joined.empty:
                    all_detections.append(joined)

    if all_detections:
        combined = pd.concat(all_detections, ignore_index=True)
        logger.info(f"Total incursion points detected: {len(combined)}")

        events = aggregate_probing_events(combined)
        logger.info(f"Aggregated probing events: {len(events)}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if output_path.endswith(".parquet"):
            combined.to_parquet(output_path, index=False)
        else:
            combined.to_csv(output_path, index=False)

        events_output = output_path.replace(".parquet", "_events.csv").replace(".csv", "_events.csv")
        events.to_csv(events_output, index=False)
        logger.info(f"Saved results to {output_path} and {events_output}")
    else:
        logger.info("No spatial intersections detected in target regions.")


def main():
    parser = argparse.ArgumentParser(description="Project Aurora Batch Spatial Processor")
    parser.add_argument("--regions", type=str, default="config/regions.geojson", help="Path to regions GeoJSON")
    parser.add_argument("--input", type=str, required=True, help="Input directory or file pattern")
    parser.add_argument("--output", type=str, required=True, help="Output destination file")
    parser.add_argument("--chunk-size", type=int, default=50000, help="Row chunk size per iteration")
    parser.add_argument("--memory-budget-mb", type=float, default=512.0, help="Memory ceiling per batch in MB")
    args = parser.parse_args()

    run_pipeline(
        regions_path=args.regions,
        input_pattern=args.input,
        output_path=args.output,
        chunk_size=args.chunk_size,
        memory_budget_mb=args.memory_budget_mb,
    )


if __name__ == "__main__":
    main()
