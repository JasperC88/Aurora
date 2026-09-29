# Project Aurora: Spatial Telemetry & Volumetric Sovereignty

## Project Overview
**Project Aurora** is an academic dissertation and computational research pipeline investigating **state coercion, grey-zone tactics, and boundary-probing behavior** through the lens of **volumetric sovereignty** (Stuart Elden). 

By analyzing massive spatio-temporal telemetry datasets (ADS-B aerial tracking and AIS maritime vessel telemetry) across critical geopolitical chokepoints—primarily the **Taiwan Air Defense Identification Zone (ADIZ)** and the **Greenland-Iceland-United Kingdom (GIUK) Gap**—Project Aurora operationalizes vertical and volumetric borders using high-performance spatial data science.

---

## Architectural & Engineering Rules

### 1. Memory-First Processing Paradigm
- **Never load raw telemetry datasets entirely into memory.** Datasets easily reach tens to hundreds of gigabytes.
- Telemetry processing must always operate via **chunked iteration**, **Dask partitioned dataframes**, or **streamed batch iterators** (e.g. Trino fetch batches / PyArrow Parquet partition chunks).
- Maximum memory footprint per local chunk during prototyping in Antigravity must remain strictly **$\le 512$ MB RAM**.
- Explicitly delete intermediate GeoDataFrames and call `gc.collect()` when processing large batches.

### 2. High-Performance Spatial Indexing
- Use **GeoPandas** with spatial indexes (`sindex` backed by R-tree/STRtree) for all point-in-polygon queries against ADIZ/maritime boundary polygons.
- Pre-filter telemetry coordinates using vectorized bounding box pre-checks (`cx` indexer or min/max latitude-longitude envelope filtering) before executing full polygon intersection joins.
- Model airspace and maritime space volumetrically: incorporate altitude ($z$) and time ($t$) alongside surface coordinates ($x, y$).

### 3. Progressive Scale: Antigravity $\rightarrow$ Eddie Cluster (UoE)
- **Phase 1 (Local / Antigravity IDE):** Develop, lint, and unit-test chunked ingestion and spatial joins using synthetic and localized sample datasets in `data/samples/`.
- **Phase 2 (Version Control / GitHub Actions):** Validate pipeline stability and memory boundaries on GitHub before submission.
- **Phase 3 (Cluster / UoE Eddie HPC):** Deploy containerized or modularized batch jobs via Sun Grid Engine (`qsub`) on Edinburgh's Eddie compute nodes without risking Out-Of-Memory (OOM) node evictions.

### 4. Code Structure & Conventions
- `src/aurora/ingestion/`: Trino queries, SQL chunk generation, Dask parquet partitions.
- `src/aurora/spatial/`: Spatial joins, bounding volumes (ADIZ sectors, median line, maritime straits), boundary-probing metrics (dwell time, incursion depth, vector angle).
- `src/aurora/visualization/`: Kepler.gl GeoJSON trip layers with 4D timestamp and altitude/depth attributes.
- `src/aurora/utils/`: Memory guards, logging, and benchmarking helpers.
- `tests/`: Automated unit tests asserting memory efficiency and geometric correctness.

---

## Key Deadlines & Milestones
- **Formative Proposal Submission:** Thursday 12th November 2026.
- Deliverable: Validated, version-controlled computational pipeline demonstrating successful memory-efficient processing of boundary-probing telemetry and theoretical grounding in volumetric territoriality.
