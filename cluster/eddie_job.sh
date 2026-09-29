#!/bin/bash
# ==============================================================================
# Project Aurora - Eddie HPC Batch Job Script
# University of Edinburgh Information Services / EIDF
# Scheduler: Sun Grid Engine (SGE)
# ==============================================================================

#$ -N aurora_spatial_pipeline
#$ -cwd
#$ -l h_rt=06:00:00
#$ -pe sharedmem 4
#$ -l h_vmem=16G
#$ -o cluster/logs/aurora_$JOB_ID.out
#$ -e cluster/logs/aurora_$JOB_ID.err
#$ -m ea

# 1. Environment Initialization
echo "Starting Project Aurora pipeline on Eddie worker node: $(hostname)"
echo "Job ID: $JOB_ID | Start Time: $(date)"

# Load Edinburgh module or activate conda environment
. /etc/profile.d/modules.sh
module load python/3.10.8 2>/dev/null || true

# Activate Aurora Virtualenv
if [ -d "$HOME/aurora_env" ]; then
    source "$HOME/aurora_env/bin/activate"
fi

# 2. Memory & Thread Safeguards
export OMP_NUM_THREADS=$NSLOTS
export OPENBLAS_NUM_THREADS=$NSLOTS
export MKL_NUM_THREADS=$NSLOTS
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# 3. Create logs and processed output dirs
mkdir -p cluster/logs data/processed

# 4. Execute Chunked Spatial Processing
python3 -m aurora.spatial.batch_runner \
    --regions config/regions.geojson \
    --input data/raw/ \
    --output data/processed/incursions_${JOB_ID}.parquet \
    --chunk-size 100000 \
    --memory-budget-mb 14000

echo "Pipeline completed successfully at $(date)"
