"""
Simulation script for the Brunel (2000) network model as described in NineML.

This script imports a Python lib9ml network description from
"brunel_network_alpha.py", exports it as XML, and then
runs a simulation using the pyNN.nineml module with the NEURON
backend.

"""

from datetime import datetime
from brunel_network_alpha import build_model
import pyNN.neuron as sim
from pyNN.nineml.read import Network
from pyNN.utility import SimulationProgressBar


def run_simulation(parameters, plot_figure=False):
    """

    """
    timestamp = datetime.now()
    model = build_model(**parameters["network"])
    if "full_filename" in parameters["experiment"]:
        xml_file = parameters["experiment"]["full_filename"].replace(".h5", ".xml")
    else:
        xml_file = "{}.xml".format(parameters["experiment"]["base_filename"])
    model.write(xml_file)

    sim.setup()

    print("Building network")
    net = Network(sim, xml_file)

    if plot_figure:
        stim = net.populations["Ext"]
        stim[:100].record('spikes')
        exc = net.populations["Exc"]
        exc.sample(50).record("spikes")
        exc.sample(3).record(["nrn_V", "syn_A"])
        inh = net.populations["Inh"]
        inh.sample(50).record("spikes")
        inh.sample(3).record(["nrn_V", "syn_A"])
    else:
        all = net.assemblies["All neurons"]
        all.sample(parameters["experiment"]["n_record"]).record("spikes")
        all.record("spikes")

    print("Running simulation")
    t_stop = parameters["experiment"]["duration"]
    pb = SimulationProgressBar(t_stop/80, t_stop)
    sim.run(t_stop, callbacks=[pb])

    print("Handling data")
    data = {}
    if plot_figure:
        data["stim"] = stim.get_data().segments[0]
        data["exc"] = exc.get_data().segments[0]
        data["inh"] = inh.get_data().segments[0]
    else:
        if "full_filename" in parameters["experiment"]:
            filename = parameters["experiment"]["full_filename"]
        else:
            filename = "{}_nineml_{:%Y%m%d%H%M%S}.h5".format(parameters["experiment"]["base_filename"],
                                                             timestamp)
        all.write_data(filename)

    sim.end()
    return data
