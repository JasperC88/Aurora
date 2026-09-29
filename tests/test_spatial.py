"""
Tests for Spatial Join, Incursion Metrics, and Kepler Formatting
"""

import os
import pandas as pd
import pytest
from aurora.spatial.geometries import RegionManager
from aurora.spatial.probing_metrics import (
    compute_dwell_time_seconds,
    aggregate_probing_events,
)
from aurora.visualization.kepler_formatter import format_kepler_trip_geojson


@pytest.fixture
def sample_telemetry_df():
    sample_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "samples", "sample_telemetry.csv"
    )
    return pd.read_csv(sample_path)


@pytest.fixture
def region_manager():
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "regions.geojson"
    )
    return RegionManager(config_path)


def test_region_manager_load(region_manager):
    regions = region_manager.list_regions()
    assert "TW_ADIZ_SW" in regions
    assert "GIUK_GAP" in regions

    tw_bbox = region_manager.get_bbox("TW_ADIZ_SW")
    assert tw_bbox is not None
    assert tw_bbox["min_lon"] == 117.5
    assert tw_bbox["max_lat"] == 23.5


def test_dwell_time_calculation(sample_telemetry_df):
    kj500_df = sample_telemetry_df[sample_telemetry_df["icao24"] == "78019A"]
    dwell_sec = compute_dwell_time_seconds(kj500_df, time_col="timestamp")
    # 04:00:00 to 04:35:00 is 35 minutes = 2100 seconds
    assert dwell_sec == 2100.0


def test_kepler_trip_formatting(sample_telemetry_df):
    geojson = format_kepler_trip_geojson(sample_telemetry_df)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 2  # Two distinct tracks (KJ500 and BAW123)

    first_feat = geojson["features"][0]
    assert first_feat["geometry"]["type"] == "LineString"
    assert len(first_feat["geometry"]["coordinates"][0]) == 4  # [lon, lat, alt, epoch]
