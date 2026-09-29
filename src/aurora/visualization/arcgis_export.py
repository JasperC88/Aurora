"""
ArcGIS Integration & Volumetric Export Module for Project Aurora
Tailored for University of Edinburgh ArcGIS Online (eduni.maps.arcgis.com) and ArcGIS Pro.
Exports 3D volumetric layers (Z-aware PointZ and LineStringZ), 3D extruded bounding volumes,
and ArcGIS-compatible Feature Collections.
"""

import json
import os
import csv
import logging
from typing import Dict, Any, List, Optional, Union

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger("aurora.arcgis")


def export_arcgis_geopackage(
    gdf_or_df,
    output_path: str = "data/processed/aurora_arcgis.gpkg",
    layer_name: str = "incursions"
) -> str:
    """
    Exports spatial telemetry to an OGC GeoPackage (.gpkg), natively supported
    by both ArcGIS Pro and QGIS with full 3D Z-geometry fidelity.
    """
    try:
        import geopandas as gpd
        if not isinstance(gdf_or_df, gpd.GeoDataFrame):
            gdf = gpd.GeoDataFrame(
                gdf_or_df,
                geometry=gpd.points_from_xy(gdf_or_df["lon"], gdf_or_df["lat"], z=gdf_or_df.get("altitude_ft", 0) * 0.3048),
                crs="EPSG:4326"
            )
        else:
            gdf = gdf_or_df

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        gdf.to_file(output_path, layer=layer_name, driver="GPKG")
        logger.info(f"Exported GeoPackage layer '{layer_name}' to {output_path}")
        return output_path
    except ImportError:
        logger.warning("GeoPandas not installed; skipping GeoPackage export.")
        return ""


def export_arcgis_3d_geojson(
    telemetry_df: Any,
    output_path: str = "data/processed/aurora_arcgis_3d.geojson",
    lon_col: str = "lon",
    lat_col: str = "lat",
    alt_col: str = "altitude_ft",
    track_id_col: str = "flight",
) -> str:
    """
    Exports telemetry tracks into 3D (X, Y, Z) GeoJSON LineStringZ features
    optimized for ArcGIS Pro 3D Local Scenes and ArcGIS Online Scene Viewer.
    Altitude is stored both as the 3rd geometry coordinate (in meters) and as an attribute.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if isinstance(telemetry_df, str) and os.path.exists(telemetry_df):
        with open(telemetry_df, "r", encoding="utf-8") as f:
            records = list(csv.DictReader(f))
    elif pd is not None and isinstance(telemetry_df, pd.DataFrame):
        records = telemetry_df.to_dict(orient="records")
    else:
        records = list(telemetry_df)

    if not records:
        empty_fc = {"type": "FeatureCollection", "features": []}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(empty_fc, f, indent=2)
        return output_path

    # Group by track id
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        tid = str(r.get(track_id_col) or r.get("hex") or "TRACK_UNKNOWN")
        grouped.setdefault(tid, []).append(r)

    features = []
    for track_id, group_rows in grouped.items():
        coords_3d = []
        alt_values = []

        for row in group_rows:
            try:
                lon = float(row.get(lon_col, 0.0))
                lat = float(row.get(lat_col, 0.0))
                alt_ft = float(row.get(alt_col, 0.0) or 0.0)
            except (ValueError, TypeError):
                continue
            alt_m = round(alt_ft * 0.3048, 1)
            coords_3d.append([lon, lat, alt_m])
            alt_values.append(alt_ft)

        if len(coords_3d) >= 1:
            first_row = group_rows[0]
            geom_type = "LineString" if len(coords_3d) > 1 else "Point"
            geom_coords = coords_3d if len(coords_3d) > 1 else coords_3d[0]

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": geom_type,
                    "coordinates": geom_coords,
                },
                "properties": {
                    "TrackID": str(track_id),
                    "Hex": str(first_row.get("hex", "")).upper(),
                    "AircraftType": str(first_row.get("aircraft_type", first_row.get("type", "UNK"))),
                    "IsMilitary": bool(first_row.get("is_military", False)),
                    "MinAlt_ft": min(alt_values) if alt_values else 0.0,
                    "MaxAlt_ft": max(alt_values) if alt_values else 0.0,
                    "Velocity_kts": float(first_row.get("velocity_kts", 0.0) or 0.0),
                    "Heading_deg": float(first_row.get("track_deg", first_row.get("heading_deg", 0.0)) or 0.0),
                    "PointCount": len(coords_3d),
                    "TheoreticalFramework": "Stuart Elden Volumetric Sovereignty",
                }
            }
            features.append(feature)

    feature_collection = {
        "type": "FeatureCollection",
        "name": "Project_Aurora_3D_Telemetry",
        "crs": {
            "type": "name",
            "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" }
        },
        "features": features
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, indent=2)

    return output_path


def export_adiz_arcgis_extrusions(
    regions_path: str = "config/regions.geojson",
    output_path: str = "data/processed/adiz_3d_volumes.geojson"
) -> str:
    """
    Exports 3D volumetric boundaries (Taiwan ADIZ, GIUK Gap) with extrusion attributes
    (BaseHeight_m, ExtrusionHeight_m) for instantaneous 3D polygon extrusion in ArcGIS Pro.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if not os.path.exists(regions_path):
        return ""

    with open(regions_path, "r", encoding="utf-8") as f:
        regions_data = json.load(f)

    arcgis_features = []
    for feat in regions_data.get("features", []):
        props = feat.get("properties", {})
        min_ft = props.get("min_altitude_ft", 0)
        max_ft = props.get("max_altitude_ft", 60000)

        # Metres conversion for ArcGIS 3D Extrusion
        base_m = max(0, int(min_ft * 0.3048))
        top_m = int(max_ft * 0.3048)
        extrusion_height_m = top_m - base_m

        new_props = {
            "RegionID": props.get("region_id", "UNKNOWN"),
            "Name": props.get("name", "Contested Airspace"),
            "Theater": props.get("theater", "Taiwan Strait"),
            "Domain": props.get("domain", "Airspace"),
            "BaseHeight_m": base_m,
            "TopHeight_m": top_m,
            "ExtrusionHeight_m": extrusion_height_m,
            "MinAlt_ft": min_ft,
            "MaxAlt_ft": max_ft,
            "SovereigntyType": "Air Defense Identification Zone (Volumetric)",
        }

        arcgis_features.append({
            "type": "Feature",
            "geometry": feat.get("geometry"),
            "properties": new_props
        })

    out_fc = {
        "type": "FeatureCollection",
        "name": "Project_Aurora_Volumetric_Sectors",
        "crs": {
            "type": "name",
            "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" }
        },
        "features": arcgis_features
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out_fc, f, indent=2)

    return output_path
