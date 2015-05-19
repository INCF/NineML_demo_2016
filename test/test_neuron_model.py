"""
This script models a pair of neurons defined by a NineML model.

Each neuron receives the same synaptic input. For the convenience of
plotting we overwrite the synaptic current recorded from the second neuron
with the expected current.

Andrew Davison, May 2015
"""

import numpy as np
from quantities import nA
from nineml import read
from nineml.abstraction_layer import DynamicsClass
import pyNN.neuron as sim
from pyNN.neuron.nineml import nineml_cell_type
from pyNN.utility.plotting import Figure, Panel

t_stop = 120
dt = 0.01

sim.setup(timestep=dt)

celltype = DynamicsClass(name='iaf',
                         subnodes={'nrn': read("../BrunelIaF.xml")['BrunelIaF'],
                                   'syn': read("../AlphaPSR.xml")['AlphaPSR']})
celltype.connect_ports('syn.Isyn', 'nrn.Isyn')
cell_parameters = {'nrn_R': 1.5, 'nrn_Vreset': 10.0, 'nrn_tau': 20.0,
                   'nrn_tau_rp': 2.0, 'nrn_theta': 20.0, 'syn_tau_syn': 2.0}
p = sim.Population(2, nineml_cell_type('BrunelIaF', celltype, {'syn': 'syn_q'})(**cell_parameters))

spike_times = np.arange(45, 155, 10.0)
spike_times[0] = 5
stim = sim.Population(1, sim.SpikeSourceArray(spike_times=spike_times))

weight = 0.1
delay = 0.5
prj = sim.Projection(stim, p,
                     sim.AllToAllConnector(),
                     sim.StaticSynapse(weight=weight, delay=delay),
                     receptor_type='syn')

p.record(['nrn_V', 'syn_A', 'syn_B'])

sim.run(t_stop)

nrn_data = p.get_data().segments[0]

expected = np.zeros((1 + int(round(t_stop/dt)),))
tau_syn = cell_parameters["syn_tau_syn"]
tp = np.arange(0, t_stop - spike_times[0] - delay, dt)/tau_syn
expected[1 + int(round((spike_times[0] + delay)/dt)):] = weight * tp * np.exp(-tp)

synaptic_current = nrn_data.filter(name='syn_A')[0]
# for convenience of plotting, we overwrite the data recorded from the second neuron
# with the expected time course for the first EPSC
synaptic_current[:, 1] = expected * nA

Figure(
    Panel(synaptic_current, yticks=True, xlim=(0, 120)),
    Panel(nrn_data.filter(name='nrn_V')[0], yticks=True, xlim=(0, 120), xticks=True, xlabel="Time (ms)"),

).save("test_neuron_model.png")

sim.end()
