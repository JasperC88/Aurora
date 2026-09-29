"""
Memory-Disciplined Spatial Join Engine
Executes chunked spatial joins on telemetry points against volumetric boundary polygons.
"""

from typing import Iterator, Optional, Union, List
import pandas as pd
import logging
from ..utils.memory import enforce_memory_limit

logger = logging.getLogger("aurora.spatial.joins")


class SpatialJoinEngine:
    """
    Performs chunked spatial joins and volumetric boundary filtering
    without loading the entire telemetry catalog into memory.
    """

    def __init__(self, target_region_gdf=None):
        self.target_region_gdf = target_region_gdf

    @enforce_memory_limit(max_mb=512.0)
    def process_chunk(
        self,
        chunk_df: pd.DataFrame,
        lon_col: str = "lon",
        lat_col: str = "lat",
        alt_col: str = "altitude_ft",
        crs: str = "EPSG:4326",
    ) -> pd.DataFrame:
        """
        Executes spatial join on a single DataFrame chunk against the region boundary,
        applying 2D polygon containment followed by 1D vertical altitude validation.
        """
        if chunk_df.empty:
            return chunk_df

        try:
            import geopandas as gpd
        except ImportError:
            raise RuntimeError("GeoPandas is required for spatial join operations.")

        # Coarse envelope pre-filtering if target_region_gdf is set
        if self.target_region_gdf is not None:
            minx, miny, maxx, maxy = self.target_region_gdf.total_bounds
            coarse_mask = (
                (chunk_df[lon_col] >= minx)
                & (chunk_df[lon_col] <= maxx)
                & (chunk_df[lat_col] >= miny)
                & (chunk_df[lat_col] <= maxy)
            )
            filtered_df = chunk_df[coarse_mask].copy()
            if filtered_df.empty:
                return pd.DataFrame()
        else:
            filtered_df = chunk_df.copy()

        # Construct GeoDataFrame
        gdf = gpd.GeoDataFrame(
            filtered_df,
            geometry=gpd.points_from_xy(filtered_df[lon_col], filtered_df[lat_col]),
            crs=crs,
        )

        if self.target_region_gdf is None:
            return gdf

        # Spatial Join (Points within Region Polygons)
        joined = gpd.sjoin(gdf, self.target_region_gdf, how="inner", predicate="within")

        # Volumetric vertical check
        if alt_col in joined.columns and "min_altitude_ft" in joined.columns:
            joined = joined[
                (joined[alt_col] >= joined["min_altitude_ft"])
                & (joined[alt_col] <= joined["max_altitude_ft"])
            ]

        return joined

    def process_stream(
        self,
        chunk_stream: Iterator[pd.DataFrame],
        lon_col: str = "lon",
        lat_col: str = "lat",
        alt_col: str = "altitude_ft",
    ) -> Iterator[pd.DataFrame]:
        """
        Yields filtered spatial join results iteratively across a stream of telemetry chunks.
        """
        for chunk in chunk_stream:
            result = self.process_chunk(chunk, lon_col=lon_col, lat_col=lat_col, alt_col=alt_col)
            if not result.empty:
                yield result
