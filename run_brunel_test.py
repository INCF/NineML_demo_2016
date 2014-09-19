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

sim.run(100.0)

stim_data = stim.get_data().segments[0]
exc_data = exc.get_data().segments[0]
#import pdb; pdb.set_trace()
#all.write_data("brunel_network_components_test.h5")

sim.end()


Figure(
    Panel(stim_data.spiketrains),
    Panel(exc_data.analogsignalarrays[0]),
    Panel(exc_data.analogsignalarrays[1]),
    Panel(exc_data.spiketrains),
).save("brunel_network_components_test.png")
