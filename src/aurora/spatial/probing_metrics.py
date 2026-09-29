"""
State Coercion and Boundary-Probing Metrics
Quantifies grey-zone spatial behavior, boundary dwell time, penetration depth, and trajectory dynamics.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


def compute_dwell_time_seconds(track_df: pd.DataFrame, time_col: str = "timestamp") -> float:
    """Calculates total dwell time in seconds for a specific aircraft/vessel track in the zone."""
    if track_df.empty or len(track_df) < 2:
        return 0.0
    times = pd.to_datetime(track_df[time_col]).sort_values()
    delta = times.iloc[-1] - times.iloc[0]
    return delta.total_seconds()


def compute_track_penetration(track_df: pd.DataFrame, boundary_polygon) -> Dict[str, float]:
    """
    Computes spatial penetration metrics:
    - Minimum distance to polygon centroid or baseline (proxy for penetration depth)
    - Total points recorded inside the volumetric volume
    """
    if track_df.empty or "geometry" not in track_df.columns:
        return {"point_count": len(track_df), "max_penetration_deg": 0.0}

    # Centroid proximity proxy
    centroid = boundary_polygon.centroid
    distances = track_df.geometry.distance(centroid)

    return {
        "point_count": len(track_df),
        "min_dist_to_centroid_deg": float(distances.min()) if not distances.empty else 0.0,
        "mean_altitude_ft": float(track_df["altitude_ft"].mean()) if "altitude_ft" in track_df.columns else 0.0,
    }


def aggregate_probing_events(
    detected_df: pd.DataFrame,
    track_id_col: str = "icao24",
    time_col: str = "timestamp",
) -> pd.DataFrame:
    """
    Aggregates point detections into discrete boundary-probing incursion events.
    """
    if detected_df.empty:
        return pd.DataFrame()

    events = []
    for track_id, group in detected_df.groupby(track_id_col):
        sorted_group = group.sort_values(by=time_col)
        dwell_sec = compute_dwell_time_seconds(sorted_group, time_col=time_col)

        events.append({
            "track_id": track_id,
            "start_time": sorted_group[time_col].iloc[0],
            "end_time": sorted_group[time_col].iloc[-1],
            "dwell_time_minutes": round(dwell_sec / 60.0, 2),
            "detection_points": len(sorted_group),
            "min_altitude_ft": sorted_group["altitude_ft"].min() if "altitude_ft" in sorted_group else None,
            "max_altitude_ft": sorted_group["altitude_ft"].max() if "altitude_ft" in sorted_group else None,
            "region_id": sorted_group["region_id"].iloc[0] if "region_id" in sorted_group else "UNKNOWN",
        })

    return pd.DataFrame(events)
