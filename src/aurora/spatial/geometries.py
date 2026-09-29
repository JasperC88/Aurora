"""
Geometric Definitions and Boundary Loaders for Project Aurora
Handles contested airspace polygons (Taiwan ADIZ) and maritime corridors (GIUK Gap).
"""

from typing import Dict, Any, Optional
import json
import os
import logging
from shapely.geometry import shape, Polygon, MultiPolygon

logger = logging.getLogger("aurora.spatial.geometries")


class RegionManager:
    """Manages spatial geometries and volumetric bounding boxes for contested regions."""

    def __init__(self, geojson_path: Optional[str] = None):
        self.regions: Dict[str, Dict[str, Any]] = {}
        if geojson_path and os.path.exists(geojson_path):
            self.load_geojson(geojson_path)

    def load_geojson(self, path: str):
        """Loads regions and volumetric parameters from a GeoJSON feature collection."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            region_id = props.get("region_id", "UNKNOWN")
            geom = shape(feature.get("geometry"))
            bounds = geom.bounds  # (minx, miny, maxx, maxy)

            self.regions[region_id] = {
                "name": props.get("name", region_id),
                "theater": props.get("theater", "Unknown"),
                "domain": props.get("domain", "airspace"),
                "min_altitude_ft": props.get("min_altitude_ft", 0),
                "max_altitude_ft": props.get("max_altitude_ft", 60000),
                "geometry": geom,
                "bbox": {
                    "min_lon": bounds[0],
                    "min_lat": bounds[1],
                    "max_lon": bounds[2],
                    "max_lat": bounds[3],
                },
                "raw_properties": props,
            }
        logger.info(f"Loaded {len(self.regions)} regions from {path}")

    def get_region(self, region_id: str) -> Optional[Dict[str, Any]]:
        return self.regions.get(region_id)

    def get_bbox(self, region_id: str) -> Optional[Dict[str, float]]:
        reg = self.get_region(region_id)
        return reg["bbox"] if reg else None

    def list_regions(self) -> Dict[str, str]:
        return {r_id: data["name"] for r_id, data in self.regions.items()}
