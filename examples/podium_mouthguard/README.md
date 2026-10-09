# To run:
## On windows, linux
prompt> mpirun -n 2 podium_mouthguard input.json

## On a HPC platform, tested on Oxcord ARC
prompt> sbatch run_mg.sh

# To Plot:
prompt> gnuplot gnuplot.script

## On windows:
-start x, at prompt type: startxwin
-cygstart plot.png