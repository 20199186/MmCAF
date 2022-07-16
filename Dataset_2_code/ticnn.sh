#!/bin/bash
#SBATCH -N 1 #1 Node
#SBATCH --ntasks-per-node=8
#SBATCH --time=3-00:00:00
#SBATCH --job-name=run_models_gpu_1_16GB
#SBATCH --error=%J.err
#SBATCH --output=%J.out
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1


conda activate test_multimod

~/.conda/envs/test_multimod/bin/python /scratch/satyendrac.mnitjaipur/codes/monika/ticnn/ticnn_usc1.py

