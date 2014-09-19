import pyNN.neuron as sim
from pyNN.nineml.read import Network
from pyNN.utility.plotting import Figure, Panel

sim.setup()
net = Network(sim, "brunel_network_alpha.xml")
all = net.assemblies["All neurons"]
all.record("spikes")

sim.run(10.0)

data = all.get_data()

sim.end()


Figure(
    Panel(data.segments[0].spiketrains),
).save("brunel_network_alpha.png")
