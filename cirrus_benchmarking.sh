#!/bin/bash --login

# PBS job options (name, compute nodes, job time)
#PBS -N MOOBenchmarking
# Select 4 full nodes
#PBS -l select=1:ncpus=4
# Parallel jobs should always specify exclusive node access
#PBS -l place=scatter:excl
#PBS -l walltime=12:00:00

# Replace [budget code] below with your project code (e.g. t01)
#PBS -A z04

cd $PBS_O_WORKDIR

module load anaconda/python3
source activate MOO
python run.py &> stdout.txt