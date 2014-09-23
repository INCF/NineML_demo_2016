# encoding: utf-8
"""
Simulation script for the Brunel (2000) network model as described in NineML.

This script imports a Python lib9ml network description from
"brunel_network_alpha.py", exports it as XML, and then
runs a simulation using the pyNN.nineml module with the NEURON
backend.

"""

import pyNN.neuron as sim
from pyNN.nineml.read import Network
from pyNN.utility.plotting import Figure, Panel
from brunel_network_alpha import model

xml_file = "brunel_network_alpha.xml"
model.write(xml_file)

sim.setup()
net = Network(sim, xml_file)
#all = net.assemblies["All neurons"]
#all.record("spikes")
stim = net.assemblies['BrunelCaseC'].get_population("Ext")
stim.record('spikes')
exc = net.assemblies['BrunelCaseC'].get_population("Exc")
exc.record("spikes")
exc.sample(3).record(["nrn_V", "syn_A"])
inh = net.assemblies['BrunelCaseC'].get_population("Inh")
inh.record("spikes")
inh.sample(3).record(["nrn_V", "syn_A"])

sim.run(100.0)

#data = all.get_data()
stim_data = stim.get_data().segments[0]
exc_data = exc.get_data().segments[0]
inh_data = inh.get_data().segments[0]

sim.end()


Figure(
    Panel(stim_data.spiketrains),
    Panel(exc_data.analogsignalarrays[0], yticks=True),
    Panel(exc_data.analogsignalarrays[1], yticks=True),
    Panel(exc_data.spiketrains),
    Panel(inh_data.analogsignalarrays[0], yticks=True),
    Panel(inh_data.analogsignalarrays[1], yticks=True),
    Panel(inh_data.spiketrains),
).save("brunel_network_alpha.png")
