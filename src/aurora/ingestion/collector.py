"""
Telemetry Stream Collector Daemon for Project Aurora
Periodically ingests live telemetry from ADS-B Exchange / OpenSky APIs,
enforces memory bounds, and writes partition-chunked Parquet/CSV files.
Usage:
    python3 -m aurora.ingestion.collector --source adsb --interval 15 --theater taiwan --out-dir data/raw
"""

import os
import sys
import time
import argparse
import datetime
import logging

# Ensure src is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from aurora.ingestion.adsb_exchange import LiveADSBClient
from aurora.utils.memory import MemoryGuard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aurora.collector")


def collect_batch(
    source: str = "adsb",
    theater: str = "taiwan",
    military_only: bool = False,
    out_dir: str = "data/raw",
) -> int:
    """Collects a single batch from the designated API and appends/writes to disk."""
    os.makedirs(out_dir, exist_ok=True)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    date_str = now_utc.strftime("%Y%m%d")
    hour_str = now_utc.strftime("%H")

    filename = f"telemetry_{theater}_{source}_{date_str}_{hour_str}.csv"
    filepath = os.path.join(out_dir, filename)

    with MemoryGuard(stage_name=f"Ingest-{source}", max_allowed_mb=512.0):
        if source == "adsb":
            lat = 23.5 if theater == "taiwan" else 63.0
            lon = 119.5 if theater == "taiwan" else -18.0
            dist = 250 if theater == "taiwan" else 400

            records = LiveADSBClient.fetch_adsb_exchange_radius(
                lat=lat, lon=lon, dist_nm=dist, military_only=military_only
            )
        elif source == "opensky":
            if theater == "taiwan":
                records = LiveADSBClient.fetch_opensky_live_bbox(20.0, 26.0, 116.0, 124.0)
            else:
                records = LiveADSBClient.fetch_opensky_live_bbox(58.0, 68.0, -30.0, -5.0)
        else:
            raise ValueError(f"Unknown source: {source}")

        count = len(records)
        if count == 0:
            logger.info("No aircraft records returned in this batch.")
            return 0

        # Append timestamp to each record
        for r in records:
            r["ingest_time_utc"] = now_utc.isoformat()

        # Write to CSV (zero external dependencies required)
        file_exists = os.path.exists(filepath)
        keys = list(records[0].keys())

        with open(filepath, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write(",".join(keys) + "\n")
            for r in records:
                row_vals = [str(r.get(k, "")).replace(",", " ") for k in keys]
                f.write(",".join(row_vals) + "\n")

        logger.info(f"Ingested {count} records into: {filepath}")
        return count


def run_daemon(
    source: str = "adsb",
    theater: str = "taiwan",
    interval: int = 15,
    military_only: bool = False,
    out_dir: str = "data/raw",
    max_batches: int = 0,
):
    logger.info(
        f"Starting Project Aurora Stream Collector | Source: {source.upper()} | "
        f"Theater: {theater.upper()} | Interval: {interval}s"
    )
    batch_num = 0
    try:
        while True:
            batch_num += 1
            logger.info(f"--- Collecting Batch #{batch_num} ---")
            collect_batch(source=source, theater=theater, military_only=military_only, out_dir=out_dir)

            if max_batches > 0 and batch_num >= max_batches:
                logger.info(f"Completed requested {max_batches} batches. Exiting.")
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Collector stopped by user.")


def main():
    parser = argparse.ArgumentParser(description="Project Aurora Live Telemetry Collector")
    parser.add_argument("--source", choices=["adsb", "opensky"], default="adsb", help="Telemetry API source")
    parser.add_argument("--theater", choices=["taiwan", "giuk"], default="taiwan", help="Geographic theater")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds (default: 15)")
    parser.add_argument("--mil-only", action="store_true", help="Filter for military aircraft only (ADS-B Exchange)")
    parser.add_argument("--out-dir", type=str, default="data/raw", help="Target output directory")
    parser.add_argument("--max-batches", type=int, default=0, help="Stop after N batches (0 for continuous)")

    args = parser.parse_args()
    run_daemon(
        source=args.source,
        theater=args.theater,
        interval=args.interval,
        military_only=args.mil_only,
        out_dir=args.out_dir,
        max_batches=args.max_batches,
    )


if __name__ == "__main__":
    main()
