# encoding: utf-8
"""
Run a simulation of the Brunel (2000) network model.


Usage: run_brunel_network_alpha.py [-h] [--plot-figure]
                                   implementation parameter_file

positional arguments:
  implementation  the implementation to use ('nineml', 'nest',
                  'pyNN.nest' or 'pyNN.neuron')
  parameter_file  parameter file for this experiment

optional arguments:
  -h, --help      show this help message and exit
  --plot-figure   plot the simulation results to a PNG file

"""

from __future__ import division, print_function
from datetime import datetime
import argparse
import yaml
import matplotlib
matplotlib.use("Agg")
from pyNN.utility.plotting import Figure, Panel
from analysis import instantaneous_firing_rate

parser = argparse.ArgumentParser()
parser.add_argument("implementation",
                    help="the implementation to use ('nineml', 'nest', 'pyNN.nest' or 'pyNN.neuron'")
parser.add_argument("parameter_file",
                    help="parameter file for this experiment")
parser.add_argument("--plot-figure",
                    help="plot the simulation results to a PNG file",
                    action="store_true")
config = parser.parse_args()

# parameters = {
#     "SR": {"g": 3, "eta": 2},
#     "SR2": {"g": 2, "eta": 2},
#     "SR3": {"g": 0, "eta": 2},
#     "SIfast": {"g": 6, "eta": 4},
#     "AI": {"g": 5, "eta": 2},
#     "SIslow": {"g": 4.5, "eta": 0.9},
#     "SIslow": {"g": 4.5, "eta": 0.95}
# }
with open(config.parameter_file) as fp:
    parameters = yaml.load(fp)


if config.implementation == "nineml":
    from run_nineml import run_simulation
elif config.implementation == "nest":
    from run_nest import run_simulation
elif "pyNN" in config.implementation:
    from run_PyNN import run_simulation
    parameters["simulator"] = config.implementation
else:
    raise NotImplementedError()


data = run_simulation(parameters, config.plot_figure)

if config.plot_figure:
    print("Plotting figure")
    filename = "{}_{}_{:%Y%m%d%H%M%S}.png".format(
                    parameters["experiment"]["base_filename"],
                    config.implementation,
                    datetime.now())
    plot_limits = parameters["experiment"]["plot_limits"]
    Figure(
        Panel(data["stim"].spiketrains, markersize=0.2, xlim=plot_limits),
        Panel(data["exc"].analogsignalarrays[0], yticks=True, xlim=plot_limits),
        #Panel(data["exc"].analogsignalarrays[1], yticks=True, xlim=plot_limits),
        Panel(data["exc"].spiketrains[:100], markersize=0.5, xlim=plot_limits),
        Panel(instantaneous_firing_rate(data["exc"], *plot_limits), yticks=True),
        Panel(data["inh"].analogsignalarrays[0], yticks=True, xlim=plot_limits),
        #Panel(data["inh"].analogsignalarrays[1], yticks=True, xlim=plot_limits),
        Panel(data["inh"].spiketrains[:100], markersize=0.5, xlim=plot_limits),
        Panel(instantaneous_firing_rate(data["inh"], *plot_limits),
              xticks=True, xlabel="Time (ms)", yticks=True),
    ).save(filename)
