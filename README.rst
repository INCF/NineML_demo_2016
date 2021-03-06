=====================
NineML demonstrations
=====================

This repository contains code related to an article in preparation on the NineML model description
language (http://nineml.net).

A Docker image with everything already installed is available from Docker Hub:
https://hub.docker.com/r/nineml/nineml_demo_2016/

Once you have Docker installed::

    docker pull nineml/nineml_demo_2016
    mkdir myresults
    cd myresults
    docker run -v `pwd`:/home/docker/projects/nineml_demo_2016/results -t -i nineml/nineml_demo_2016 /bin/bash

This will start a Docker container running the bash shell, in which you can run simulations
as described below. The directory `myresults` on your host machine will be shared with the
Docker container; data and image files generated by the simulations will be written there.


Running simulations with the 9ML-toolkit
========================================

::

    cd ~/projects/nineml_demo_2016/9ML-toolkit/examples/Brunel2000
    9ML-network -m crk3 brunel_network_alpha_AI.xml  # creates Sim_brunel_network_alpha_AI
    ./Sim_brunel_network_alpha_AI -d 1200.0 --timestep=0.01 -s "All neurons"

Data are recorded to `brunel_network_alpha_AI.dat`. Each line consists of the time followed by the indices of the neurons which spiked during that time step.

Or, based on the XML files from the NineML Catalog::

    cd ~/projects/nineml_demo_2016/catalog/xml/network/Brunel2000/
    9ML-network -m crk3 AI.xml
    cd ~/projects/nineml_demo_2016/results
    ~/projects/nineml_demo_2016/catalog/xml/network/Brunel2000/Sim_AI -d 1200.0 --timestep=0.01 -s "All"


Running simulations with Python
===============================

Single simulation
-----------------

To run a single simulation and plot a figure::

    cd ~/projects/nineml_demo_2016/python/brunel2000
    python run.py --plot-figure nineml parameters/AI.yml

Replace "nineml" with one of "nest", "pyNN.nest", "pyNN.neuron" or "ninemlpartial"
to run one of the other implementations.
This produces a figure, showing spike rasters and membrane potentials, as
"results/brunel_network_alpha_AI_nineml_<timestamp>.png"


Four simulations with different parameters
------------------------------------------

To generate a figure similar to Figure 8 in Brunel (2000), run::

    python run.py nineml parameters/AI.yml
    python run.py nineml parameters/SR.yml
    python run.py nineml parameters/SIfast.yml
    python run.py nineml parameters/SIslow.yml

Then to plot spike rasters and the instantaneous firing rate, run::

    python four_panel_figure.py <datafile1> <datafile2> <datafile3> <datafile4> -o output.png

where <datafile[1-4]> are the ".h5" files produced by the four simulations.


The results and figures will be created in the directory `~/projects/nineml_demo_2016/results`
directory in the Docker image, which should be mapped to the `myresults` directory on your host


For more information, contact andrew.davison@unic.cnrs-gif.fr
