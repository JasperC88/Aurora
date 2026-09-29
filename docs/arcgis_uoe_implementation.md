# Project Aurora: ArcGIS Implementation & University of Edinburgh Guide

This document details the **ArcGIS implementation** for Project Aurora, utilizing the University of Edinburgh's site license ([UoE Student Software Agreement 2024–2029](https://information-services.ed.ac.uk/computing/desktop-personal/software/main-software-deals/arcgis)).

---

## 1. University of Edinburgh ArcGIS Access

Under the University of Edinburgh site license, all students are entitled to full access to **ArcGIS Online** and **ArcGIS Pro**:

1. **ArcGIS Online Portal:**
   - University-wide Portal: [https://eduni.maps.arcgis.com/](https://eduni.maps.arcgis.com/)
   - Geosciences Portal: [https://edgeos.maps.arcgis.com/](https://edgeos.maps.arcgis.com/)
   - **Login:** Select *"Your ArcGIS organization's URL"* or click **University of Edinburgh (EASE SSO)** using your standard student credentials (`sXXXXXXX@ed.ac.uk`).
2. **ArcGIS Pro Desktop Installation:**
   - Once logged into [eduni.maps.arcgis.com](https://eduni.maps.arcgis.com/), click your profile name (top-right) &rarr; **My Settings** &rarr; **Licenses**.
   - Download the **ArcGIS Pro** installer (for Windows / Parallels / University managed lab desktops).

---

## 2. Volumetric 3D Architecture in ArcGIS

Stuart Elden’s theory of *volumetric sovereignty* requires analyzing borders in three spatial dimensions $(x, y, z)$ and time $(t)$. ArcGIS provides native 3D visualization capabilities (3D Local Scenes, 3D PointZ/LineStringZ geometries, and Voxel Space-Time Cubes) that perfectly operationalize this theoretical framework.

```
       =========================================================
       ARCGIS 3D LOCAL SCENE / SCENE VIEWER
       ---------------------------------------------------------
       TOP OF ADIZ CYLINDER (18,288 m / FL 600)
       ---------------------------------------------------------
       ▲
       │  3D Extruded Polygon Prism (ExtrusionHeight_m: 18,288m)
       │  Semi-transparent rose fill (Alpha: 0.25)
       │
       ▼  [3D LineStringZ Trajectories: lat, lon, altitude_m]
          • Incursion Flight (e.g. KJ-500 @ 7,315 m / FL 240)
          • Commercial Airway (e.g. CAL006 @ 10,972 m / FL 360)
       ---------------------------------------------------------
       SEA LEVEL / BATHYMETRIC BASELINE (0 m)
       =========================================================
```

---

## 3. Project Aurora ArcGIS Modules

Project Aurora provides native export tools in [`src/aurora/visualization/arcgis_export.py`](file:///Users/jasper/Documents/Project%20Aurora/src/aurora/visualization/arcgis_export.py):

### A. Export 3D Telemetry Tracks (`export_arcgis_3d_geojson`)
Generates 3D $(X, Y, Z)$ LineStringZ coordinates where altitude is mathematically modeled in meters:
```python
from aurora.visualization import export_arcgis_3d_geojson

# Exports 3D trajectories with flight level, speed, and military classification
export_arcgis_3d_geojson(
    telemetry_df="data/samples/sample_telemetry.csv",
    output_path="data/processed/aurora_arcgis_3d.geojson"
)
```

### B. Export Volumetric Airspace Extrusions (`export_adiz_arcgis_extrusions`)
Transforms 2D boundary polygons into 3D extruded volumetric boundaries with `BaseHeight_m` and `ExtrusionHeight_m` properties:
```python
from aurora.visualization import export_adiz_arcgis_extrusions

export_adiz_arcgis_extrusions(
    regions_path="config/regions.geojson",
    output_path="data/processed/adiz_3d_volumes.geojson"
)
```

### C. OGC GeoPackage Export (`export_arcgis_geopackage`)
When `geopandas` is installed, exports directly to an OGC GeoPackage (`.gpkg`), preserving spatial index STRtrees and 3D Z-geometry for ArcGIS Pro and QGIS:
```python
from aurora.visualization import export_arcgis_geopackage

export_arcgis_geopackage(df, output_path="data/processed/aurora_incursions.gpkg")
```

---

## 4. Live Streaming into ArcGIS Online & ArcGIS Pro

[`tactical_server.py`](file:///Users/jasper/Documents/Project%20Aurora/src/aurora/visualization/tactical_server.py) provides live REST GeoJSON endpoints directly consumable by ArcGIS as web layers.

### Step 1: Start Aurora Server
```bash
python3 run_tactical_server.py --port 8050
```

### Step 2: Add Live Layer in ArcGIS
1. Open [ArcGIS Online Map Viewer / Scene Viewer](https://eduni.maps.arcgis.com/) or **ArcGIS Pro**.
2. Click **Add Layer** &rarr; **Add Layer from Web** &rarr; select **GeoJSON**.
3. Enter either URL:
   * **Live Telemetry Stream:** `http://localhost:8050/arcgis/features/live`
   * **3D Volumetric ADIZ Extrusions:** `http://localhost:8050/arcgis/features/adiz`
4. The live aircraft and volumetric boundary layers will stream directly into your ArcGIS session.

---

## 5. Visualizing 3D Volumetric Extrusions in ArcGIS Pro

To replicate Stuart Elden's volumetric borders in **ArcGIS Pro**:

1. Create a **New Local Scene** (3D View).
2. Add `data/processed/adiz_3d_volumes.geojson`.
3. In the **Contents** pane, select the layer &rarr; go to the **Appearance** ribbon tab &rarr; **Extrusion**.
4. Set:
   * **Extrusion Type:** *Absolute Height*
   * **Field / Expression:** `[ExtrusionHeight_m]`
5. In **Symbology**, set the fill color to semi-transparent red/rose (Hex: `#F43F5E`, Transparency: `70%`).
6. Add `data/processed/aurora_arcgis_3d.geojson`.
   - ArcGIS Pro will immediately render the flight paths suspended at their true altitudes (e.g. 7,300 meters above sea level), clearly showing trajectories traversing through the extruded ADIZ volume.

---

## 6. Advanced Methodology: 3D Space-Time Cubes for the Proposal

For your **Formative Proposal due on Thursday 12th November 2026**, you can generate an empirical **Space-Time Cube** in ArcGIS Pro:

1. Open **Geoprocessing Toolbox** &rarr; **Space Time Pattern Mining Tools**.
2. Run **Create Space Time Cube By Aggregating Points**:
   * **Input Features:** `aurora_arcgis_3d.geojson` (or aggregated incursion parquet points).
   * **Time Step Interval:** `1 Day` or `1 Week`.
   * **Distance Interval:** `10 Kilometers`.
3. Run **Emerging Hot Spot Analysis (3D)** to statistically prove the temporal clustering and escalation pattern of PLA boundary-probing behavior in the Southwest ADIZ.
