#!/bin/bash

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=4
#SBATCH --time=48:00:00
#SBATCH --partition=long
#SBATCH --job-name=femtech_MG_test
#SBATCH --output=arc_%j.log

# module load OpenMPI/5.0.3-GCC-13.3.0
# export PMIX_MCA_psec=native

SIF=/data/engs-brain-health/math2084/organ_level_head_impact_model/femtech.sif
WORKDIR=/data/engs-brain-health/math2084/organ_level_head_impact_model/FemTechRun/test_run_20261007

cd "$WORKDIR" || exit 1
mkdir -p results/vtu

echo "FEMTech mouthguard simulation"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_JOB_NODELIST"
echo "MPI ranks: $SLURM_NTASKS"
echo "CPUs per rank: $SLURM_CPUS_PER_TASK"
echo "Total CPUs: $((SLURM_NTASKS * SLURM_CPUS_PER_TASK))"

singularity exec "$SIF" \
  mpirun -np "$SLURM_NTASKS" \
  --mca btl_base_warn_component_unused 0 \
  /home/ubuntu/FemTechRun/ex5 input.json
exit $?
