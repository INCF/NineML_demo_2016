# encoding: utf-8
"""
Test of the 9ML components for the Brunel (2000) network model
by simulating a network of three neurons.

This script imports a Python lib9ml network description from
"brunel_network_components_test.py", exports it as XML, and then
runs a simulation using the pyNN.nineml module with the NEURON
backend.

"""


import pyNN.neuron as sim
from pyNN.nineml.read import Network
from pyNN.utility.plotting import Figure, Panel
from brunel_network_components_test import model

xml_file = "brunel_network_components_test.xml"
model.write(xml_file)

sim.setup(timestep=0.01)
net = Network(sim, xml_file)
#all = net.assemblies["All neurons"]
stim = net.assemblies['BrunelCaseC'].get_population("Ext")
stim.record('spikes')
exc = net.assemblies['BrunelCaseC'].get_population("Exc")
exc.record(["spikes", "nrn_V", "syn_A"])
inh = net.assemblies['BrunelCaseC'].get_population("Inh")
inh.record(["spikes", "nrn_V", "syn_A"])

sim.run(100.0)

stim_data = stim.get_data().segments[0]
exc_data = exc.get_data().segments[0]
inh_data = inh.get_data().segments[0]
#import pdb; pdb.set_trace()
#all.write_data("brunel_network_components_test.h5")

sim.end()


Figure(
    Panel(stim_data.spiketrains),
    Panel(exc_data.analogsignalarrays[0], yticks=True),
    Panel(exc_data.analogsignalarrays[1], yticks=True),
    Panel(exc_data.spiketrains),
    Panel(inh_data.analogsignalarrays[0], yticks=True),
    Panel(inh_data.analogsignalarrays[1], yticks=True),
    Panel(inh_data.spiketrains, xticks=True, xlabel="Time (ms)"),
).save("brunel_network_components_test.png")
