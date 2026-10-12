# To run:
## On windows, linux
prompt> mpirun -n 2 podium_mouthguard input.json

## On a HPC platform, tested on Oxcord ARC
prompt> sbatch run_mg.sh

# To Plot:
prompt> gnuplot gnuplot.script

### Plot mps95 and movement trajectories
prompt> pvpython mps95Movie.py input.json
prompt> pvpython simulationMovie.py $PVD_FILE_NAME
