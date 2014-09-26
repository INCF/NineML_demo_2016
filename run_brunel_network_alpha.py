# encoding: utf-8
"""
Simulation script for the Brunel (2000) network model as described in NineML.

This script imports a Python lib9ml network description from
"brunel_network_alpha.py", exports it as XML, and then
runs a simulation using the pyNN.nineml module with the NEURON
backend.

"""

import sys
import numpy as np
from neo import AnalogSignal
from quantities import ms, dimensionless
import pyNN.neuron as sim
from pyNN.nineml.read import Network
from pyNN.utility.plotting import Figure, Panel
from brunel_network_alpha import build_model

case = sys.argv[1]

parameters = {
    "SR": {"g": 3, "eta": 2},
    "SR2": {"g": 2, "eta": 2},
    "SIfast": {"g": 6, "eta": 4},
    "AI": {"g": 5, "eta": 2},
    "SIslow": {"g": 4.5, "eta": 0.9}
}

plot_limits = (1000, 1200)


model = build_model(**parameters[case])

xml_file = "brunel_network_alpha_%s.xml" % case
model.write(xml_file)

sim.setup()
net = Network(sim, xml_file)

stim = net.assemblies['BrunelCaseC'].get_population("Ext")
stim[:100].record('spikes')
exc = net.assemblies['BrunelCaseC'].get_population("Exc")
exc.record("spikes")
exc.sample(3).record(["nrn_V", "syn_A"])
inh = net.assemblies['BrunelCaseC'].get_population("Inh")
inh.record("spikes")
inh.sample(3).record(["nrn_V", "syn_A"])

sim.run(plot_limits[1])

stim_data = stim.get_data().segments[0]
exc_data = exc.get_data().segments[0]
inh_data = inh.get_data().segments[0]

sim.end()


def instantaneous_firing_rate(segment, begin, end):
    """Computed in bins of 0.1 ms """
    bins = np.arange(begin, end, 0.1)
    hist, _ = np.histogram(segment.spiketrains[0].time_slice(begin, end), bins)
    for st in segment.spiketrains[1:]:
        h, _ = np.histogram(st.time_slice(begin, end), bins)
        hist += h
    return AnalogSignal(hist, sampling_period=0.1*ms, units=dimensionless,
                        channel_index=0, name="Spike count")


Figure(
    Panel(stim_data.spiketrains, markersize=0.2, xlim=plot_limits),
    Panel(exc_data.analogsignalarrays[0], yticks=True, xlim=plot_limits),
    Panel(exc_data.analogsignalarrays[1], yticks=True, xlim=plot_limits),
    Panel(exc_data.spiketrains[:100], markersize=0.5, xlim=plot_limits),
    Panel(instantaneous_firing_rate(exc_data, *plot_limits), yticks=True),
    Panel(inh_data.analogsignalarrays[0], yticks=True, xlim=plot_limits),
    Panel(inh_data.analogsignalarrays[1], yticks=True, xlim=plot_limits),
    Panel(inh_data.spiketrains[:100], markersize=0.5, xlim=plot_limits),
    Panel(instantaneous_firing_rate(inh_data, *plot_limits), xticks=True, xlabel="Time (ms)", yticks=True),
).save("brunel_network_alpha.png")
