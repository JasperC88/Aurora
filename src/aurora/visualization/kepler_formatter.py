"""
Kepler.gl Formatting Module
Formats 4D spatio-temporal trajectories (lat, lon, altitude, epoch) for volumetric Kepler.gl visualization.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import json


def format_kepler_trip_geojson(
    df: pd.DataFrame,
    track_id_col: str = "icao24",
    lon_col: str = "lon",
    lat_col: str = "lat",
    alt_col: str = "altitude_ft",
    time_col: str = "timestamp",
) -> Dict[str, Any]:
    """
    Converts telemetry points into Kepler.gl 4D Trips layer GeoJSON.
    Each feature is a LineString with coordinates: [longitude, latitude, altitude_meters, timestamp_epoch_sec].
    """
    if df.empty:
        return {"type": "FeatureCollection", "features": []}

    df_copy = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_copy[time_col]):
        df_copy["_epoch"] = pd.to_datetime(df_copy[time_col]).astype("int64") // 10**9
    else:
        df_copy["_epoch"] = df_copy[time_col].astype("int64") // 10**9

    # Convert altitude feet to meters for 3D visualization scaling
    alt_meters = (df_copy[alt_col] * 0.3048).fillna(0.0) if alt_col in df_copy else 0.0
    df_copy["_alt_m"] = alt_meters

    features = []
    for track_id, group in df_copy.groupby(track_id_col):
        sorted_points = group.sort_values(by="_epoch")
        coordinates = [
            [
                float(row[lon_col]),
                float(row[lat_col]),
                float(row["_alt_m"]),
                int(row["_epoch"]),
            ]
            for _, row in sorted_points.iterrows()
        ]

        if len(coordinates) >= 2:
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "track_id": str(track_id),
                        "start_epoch": int(coordinates[0][3]),
                        "end_epoch": int(coordinates[-1][3]),
                        "point_count": len(coordinates),
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates,
                    },
                }
            )

    return {"type": "FeatureCollection", "features": features}


def export_kepler_json(geojson_data: Dict[str, Any], output_path: str):
    """Saves Kepler 4D trip GeoJSON to disk."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)
