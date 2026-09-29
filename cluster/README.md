# Scaling Project Aurora to the Eddie HPC Cluster

This document outlines the operational roadmap for executing Project Aurora's high-throughput telemetry pipelines on the **University of Edinburgh's Eddie compute cluster**.

## Why Transition from Local/Antigravity to Eddie?
During early development, the pipeline is verified on local slices ($\le 512$ MB) inside Google Antigravity. However, full-scale historical telemetry datasets (ADS-B records spanning months across East Asia or the North Atlantic) encompass hundreds of gigabytes and billions of spatial points.

Eddie provides:
- High-memory nodes (`-l h_vmem=16G` to `64G` per slot)
- High-throughput parallel scratch storage (`/exports/csce/eddie/...` or `/scratch`)
- Multi-core Dask distributed workers

## Pre-Requisites & Information Services Request
When requesting Eddie access from University of Edinburgh Information Services (IS), provide the following verified profile from our local testing:

1. **Computational Profile:**
   - **Job Type:** Batch embarrassingly parallel spatial joins & trajectory aggregation.
   - **Memory Footprint:** Guaranteed memory-bounded ($< 16$ GB per slot via chunked streaming iterators).
   - **I/O Profile:** Sequential Parquet reading/writing without high random seek overhead.
2. **Environment:**
   - Python 3.10+
   - Key packages: `geopandas`, `shapely`, `pyarrow`, `dask`, `trino`.

## Job Submission
To submit the pipeline to the Sun Grid Engine scheduler:
```bash
qsub cluster/eddie_job.sh
```

Monitor job status:
```bash
qstat -u $USER
```

Review execution logs:
```bash
tail -f cluster/logs/aurora_<JOB_ID>.out
tail -f cluster/logs/aurora_<JOB_ID>.err
```
