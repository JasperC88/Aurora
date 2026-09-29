"""Project Aurora: Visualization & Cartographic Rendering Engine."""

try:
    from .kepler_formatter import format_kepler_trip_geojson, export_kepler_json
except ImportError:
    format_kepler_trip_geojson = None
    export_kepler_json = None

try:
    from .live_monitor import generate_monitor_html
except ImportError:
    generate_monitor_html = None

try:
    from .arcgis_export import (
        export_arcgis_3d_geojson,
        export_adiz_arcgis_extrusions,
        export_arcgis_geopackage,
    )
except ImportError:
    export_arcgis_3d_geojson = None
    export_adiz_arcgis_extrusions = None
    export_arcgis_geopackage = None

__all__ = [
    "format_kepler_trip_geojson",
    "export_kepler_json",
    "generate_monitor_html",
    "export_arcgis_3d_geojson",
    "export_adiz_arcgis_extrusions",
    "export_arcgis_geopackage",
]
