"""
This script models a pair of neurons defined by a PyNN model.

Each neuron receives the same synaptic input from a Poisson process defined in NineML. For the convenience of
plotting we overwrite the synaptic current recorded from the second neuron
with the expected current.

Andrew Davison, May 2015
"""

from __future__ import division
import matplotlib
matplotlib.use("Agg")
import numpy.random
from nineml import read
import pyNN.neuron as sim
from pyNN.neuron.nineml import nineml_cell_type
from pyNN.utility.plotting import Figure, Panel


t_stop = 100000
dt = 0.1

sim.setup(timestep=dt)

cell_parameters = {'v_reset': 10.0, 'tau_m': 20.0, 'v_rest': 0.0,
                   'tau_refrac': 2.0, 'v_thresh': 20.0, 'tau_syn_E': 2.0}
p = sim.Population(1, sim.IF_curr_alpha(**cell_parameters))
p.initialize(v=0.0)

rate = 20
stim = sim.Population(1, nineml_cell_type('Poisson', read("../sources/Poisson.xml")['Poisson'], {})(rate=rate))
stim.initialize(t_next=numpy.random.exponential(1000/rate))

weight = 0.1
delay = 0.5
prj = sim.Projection(stim, p,
                     sim.AllToAllConnector(),
                     sim.StaticSynapse(weight=weight, delay=delay),
                     receptor_type='excitatory')

stim.record('spikes')
p.record('v')

sim.run(t_stop)

nrn_data = p.get_data().segments[0]
stim_data = stim.get_data().segments[0]

print("Expected spike count: {}".format(t_stop*rate/1000))
print("Actual spike count: {}".format(stim.mean_spike_count()))

Figure(
    Panel(stim_data.spiketrains, markersize=0.5, xlim=(0, t_stop)),
    Panel(nrn_data.filter(name='v')[0], yticks=True, xlim=(0, t_stop), xticks=True, xlabel="Time (ms)"),
).save("test_poisson_generator.png")

sim.end()
