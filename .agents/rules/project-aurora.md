---
trigger: always_on
description: Core guidelines and coding standards for Project Aurora (spatial telemetry & volumetric sovereignty research)
---

# Project Aurora Agent Rules

You are assisting Jasper with **Project Aurora**, an academic research codebase investigating volumetric state coercion and boundary-probing behavior in contested air and maritime spaces (Taiwan ADIZ, GIUK Gap).

### Guiding Principles:
1. **Computational Discipline:** Always construct data pipelines that process telemetry in memory-bounded chunks or partitioned streams (Dask / PyArrow / Trino). Never write code that loads multi-gigabyte files into a single pandas DataFrame in memory.
2. **Volumetric Geometry:** Remember that borders are 3D/4D volumes, not flat 2D lines. Account for altitude (FL / feet / meters) and time dimensions when evaluating airspace incursions and maritime patrols.
3. **Reproducibility & HPC Readiness:** Ensure all code written in Antigravity can be easily packaged or submitted via SGE job scripts (`qsub`) to the University of Edinburgh's Eddie cluster. Keep configuration modular and decoupled from local paths.
4. **Theoretical Rigor:** Code naming and documentation should reflect both spatial data science precision and International Relations / Political Geography theoretical frameworks (Stuart Elden's volumetric sovereignty, grey-zone coercion, ADIZ protocols).
