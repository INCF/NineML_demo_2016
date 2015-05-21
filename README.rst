===================
Brunel (2000) model
===================

This project contains several implementions of a network model closely based on:

  Brunel, Nicolas (2000) “Dynamics of Sparsely Connected Networks of Excitatory and Inhibitory
    Spiking Neurons.” Journal of Computational Neuroscience 8(3):183–208.
    `doi:10.1023/A:1008925309027 <http://dx.doi.org/10.1023/A:1008925309027>`_.

The main difference is that the current model uses current-based synapses with an alpha-function
profile, rather than voltage-step synapses.

The implementations are as follows:

1. Model description in NineML, simulated using NEURON, via PyNN
2. Model description and simulation in PyNEST
3. (TODO) Model description in PyNN, simulated using NEURON
4. (TODO) Model description in PyNN, simulated using NEST


Requirements
============

We strongly recommend installing the following packages in a virtualenv or Conda environment.

* Development version of lib9ML, "master" branch (https://github.com/INCF/lib9ML)
* Development version of 9ml2nmodl (https://bitbucket.org/apdavison/ninemlcodegen)
* Development version of PyNN, "nineml" branch, with NEURON 7.3+ and NEST 2.6
  (see http://neuralensemble.org/docs/PyNN/installation.html)
* Development version of Neo, "apibreak" branch (https://github.com/NeuralEnsemble/python-neo)
* PyTables
* Matplotlib
* PyYAML

For running parameters sweeps, you will need the following additional packages:

* Elephant
* Sarge
* Pandas

TODO: provide Docker image with everything already installed.

NineML descriptions
===================

The NineML abstraction layer components are provided in the repository as XML files.
You may also regenerate the abstraction layer XML files from Python lib9ML descriptions as follows::

    python alphaPSR.py
    python brunelIaF.py
    python poisson.py
    python staticConnection.py

The NineML user layer (network) description is generated when running simulations (see below).


Running simulations
===================

The ``run_brunel_network_alpha.py`` script runs a single simulation.


Single simulation
-----------------

To run a single simulation and plot a figure::

    python run_brunel_network_alpha.py --plot-figure nineml parameters/AI.yml

Replace "nineml" with one of "nest", "pyNN.nest" or "pyNN.neuron" to run one of the other implementations.
This produces a figure, showing spike rasters and membrane potentials, as
"results/brunel_network_alpha_AI_nineml_<timestamp>.png"


Four simulations with different parameters
------------------------------------------

To generate a figure similar to Figure 8 in Brunel (2000), run::

    python run_brunel_network_alpha.py nineml parameters/AI.yml
    python run_brunel_network_alpha.py nineml parameters/SR.yml
    python run_brunel_network_alpha.py nineml parameters/SIfast.yml
    python run_brunel_network_alpha.py nineml parameters/SIslow.yml

Then to plot spike rasters and the instantaneous firing rate, run::

    python four_panel_figure.py <datafile1> <datafile2> <datafile3> <datafile4> -o output.png

where <datafile[1-4]> are the ".h5" files produced by the four simulations.


Parameter sweeps
----------------

To run parameter sweeps over the parameters "g" (ratio of inhibitory to excitatory synaptic weights)
and "eta" (ratio of the external firing rate to the threshold rate), as in Figure 2 (and several
other figures) of Brunel (2000), run::

    python sweep.py nineml <parameter_file>

Replace "nineml" with one of "nest", "pyNN.nest" or "pyNN.neuron" to run one of the other
implementations. <parameter_file> is the baseline parameter file to use, e.g. "parameters/AI.yml"
This creates a subdirectory of "results" labelled with the timestamp, into which is saved all the
spike recordings (in Neo HDF5 format) and a CSV-format index file named "sweeps.csv" which links
the values of "g" and "eta" to the output filenames.

From the spike recordings, we can now calculate a number of spike train statistics:

* the mean firing rate
* the mean of the coefficient of variation of the inter-spike intervals
  (close to zero for regular firing, close to one for irregular firing patterns)
* the population average of the cross-correlation matrix (close to zero for asynchronous
  firing patterns, close to one for highly-synchronous patterns).

To calculate these statistics and plot them as functions of g and eta, run::

    python phase_plots.py <output_directory>

where <output_directory> is the subdirectory created by "sweep.py".


For more information, contact andrew.davison@unic.cnrs-gif.fr
