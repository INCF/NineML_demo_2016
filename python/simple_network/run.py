# encoding: utf-8
"""
Run a simulation of a simple network model.


Usage: run.py [-h] [--plot-figure] implementation parameter_file

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
parser.add_argument("parameter_file",
                    help="parameter file for this experiment")
parser.add_argument("implementations",
                    help="the implementation(s) to use ('nineml', 'nest', 'pyNN.nest' or 'pyNN.neuron'",
                    default=[], nargs='+')
parser.add_argument("--plot-figure",
                    help="plot the simulation results to a PNG file",
                    action="store_true")
config = parser.parse_args()


with open(config.parameter_file) as fp:
    parameters = yaml.load(fp)

vm_vars = []
all_data = []
for implementation in config.implementations:

    if implementation == "nineml":
        from simple_network_nineml import run_simulation
        vm_vars.append("nrn_v")
    # elif implementation == "ninemlpartial":
    #     from brunel_network_nineml_partial import run_simulation
    #     vm_vars.append("nrn_v")
    # elif implementation == "nest":
    #     from brunel_network_nest import run_simulation
    #     vm_vars.append("V_m")
    # elif "pyNN" in implementation:
    #     from brunel_network_PyNN import run_simulation
    #     parameters["simulator"] = config.implementation
    #     vm_vars.append("v")
    elif "9mltoolkit" in implementation:
        from simple_network_9ml_toolkit import run_simulation
        vm_vars.append("signal0")
    else:
        raise NotImplementedError("{} not supported".format(config.implementation))

    data = run_simulation(parameters, config.plot_figure)
    all_data.append(data)

#import pdb; pdb.set_trace()

if config.plot_figure:
    print("Plotting figure")
    if len(config.implementations) == 1:
        label = config.implementations[0]
    else:
        label = "comparison"
    filename = "{}_{}_{:%Y%m%d%H%M%S}.png".format(
                    parameters["experiment"]["base_filename"],
                    label,
                    datetime.now())
    plot_limits = parameters["experiment"]["plot_limits"]

    vm = [data["exc"].filter(name=vm_var)[0][:, 0:3].rescale('mV')
          for data, vm_var in zip(all_data, vm_vars)]
    data_labels = [data["exc"].annotations["simulator"] for data in all_data]
    Figure(
        ##Panel(data["stim"].spiketrains, markersize=0.2, xlim=plot_limits),
        Panel(*vm, yticks=True, xticks=True, xlim=plot_limits, data_labels=data_labels),
        #Panel(data["exc"].analogsignalarrays[1], yticks=True, xlim=plot_limits),
        #Panel(data["exc"].spiketrains[:100], markersize=0.5, xlim=plot_limits),
        #Panel(instantaneous_firing_rate(data["exc"], *plot_limits), yticks=True, xticks=True),
    ).save(filename)
