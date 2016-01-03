"""
This script models a pair of neurons defined by a NineML model.

Each neuron receives the same synaptic input. For the convenience of
plotting we overwrite the synaptic current recorded from the second neuron
with the expected current.

We also implement the same model with NEST, and overwrite the membrane
potential recorded from the second neuron with that from the NEST
simulation.

Andrew Davison, May 2015
"""

from __future__ import division, print_function
import nest
import matplotlib
matplotlib.use("Agg")
import numpy as np
from numpy import exp
from quantities import nA, mV
from nineml import read
from nineml.abstraction import Dynamics
import pyNN.neuron as sim
from pyNN.neuron.nineml import nineml_cell_type
from pyNN.utility.plotting import Figure, Panel


def psp_height(tau_m, R_m, tau_syn):
    """
    Calculate the height of the EPSP for a synaptic current with
    peak amplitude 1 nA.

    tau_m and tau_syn: ms
    R_m: Mohm
    """
    a = (tau_m / tau_syn)
    b = (1.0 / tau_syn - 1.0 / tau_m)
    # time of maximum
    t_max = 1.0/b * (-nest.sli_func('LambertWm1', -exp(-1.0/a)/a) - 1.0/a)
    # height of PSP for current of amplitude 1 nA
    return 1/(tau_syn*tau_m*b/R_m) * ((exp(-t_max/tau_m) - exp(-t_max/tau_syn)) / b - t_max*exp(-t_max/tau_syn))


t_stop = 120
dt = 0.01
cell_parameters = {'nrn_R': 1.5, 'nrn_v_reset': 10.0, 'nrn_tau': 20.0,
                   'nrn_refractory_period': 2.0, 'nrn_v_threshold': 20.0, 'syn_tau': 0.5}
spike_times = np.arange(45, 155, 10.0)
spike_times[0] = 5
weight = 0.1  # EPSP height from a single spike received at resting potential
scale_factor = psp_height(cell_parameters['nrn_tau'],
                          cell_parameters["nrn_R"],
                          cell_parameters["syn_tau"])
w_eff = weight/scale_factor
delay = 0.5

print("\nEffective weight = {} nA\n".format(w_eff))


# PyNN/NineML simulation

sim.setup(timestep=dt)

celltype = Dynamics(name='iaf',
                    subnodes={'nrn': read("../sources/BrunelIaF.xml")['BrunelIaF'],
                              'syn': read("../sources/AlphaPSR.xml")['AlphaPSR']})
celltype.connect_ports('syn.i_synaptic', 'nrn.i_synaptic')

p = sim.Population(2, nineml_cell_type('BrunelIaF', celltype, {'syn': 'syn_weight'})(**cell_parameters))
stim = sim.Population(1, sim.SpikeSourceArray(spike_times=spike_times))

prj = sim.Projection(stim, p,
                     sim.AllToAllConnector(),
                     sim.StaticSynapse(weight=w_eff, delay=delay),
                     receptor_type='syn')

p.record(['nrn_v', 'syn_a', 'syn_b'])

sim.run(t_stop)

nrn_data = p.get_data().segments[0]

expected = np.zeros((1 + int(round(t_stop/dt)),))
tau_syn = cell_parameters["syn_tau"]
tp = np.arange(0, t_stop - spike_times[0] - delay, dt)/tau_syn
expected[1 + int(round((spike_times[0] + delay)/dt)):] = w_eff * tp * np.exp(-tp)

synaptic_current = nrn_data.filter(name='syn_a')[0]
# for convenience of plotting, we overwrite the synaptic current recorded from the second neuron
# with the expected time course for the first EPSC
synaptic_current[:, 1] = expected * nA

v_m = nrn_data.filter(name='nrn_v')[0]


# NEST simulation

nest.ResetKernel()
nest.SetKernelStatus({"resolution": dt, "print_time": True, 'local_num_threads': 1})


neuron_params = {"C_m":        1000*cell_parameters["nrn_tau"]/cell_parameters["nrn_R"],
                 "tau_m":      cell_parameters["nrn_tau"],
                 "tau_syn_ex": cell_parameters["syn_tau"],
                 "tau_syn_in": cell_parameters["syn_tau"],
                 "t_ref":      cell_parameters["nrn_refractory_period"],
                 "E_L":        0.0,
                 "V_reset":    cell_parameters["nrn_v_reset"],
                 "V_m":        0.0,
                 "V_th":       cell_parameters["nrn_v_threshold"]}

nest.SetDefaults("iaf_psc_alpha", neuron_params)
p2 = nest.Create("iaf_psc_alpha", 1)
stim2 = nest.Create("spike_generator")
nest.SetStatus(stim2, {"spike_times": spike_times})
# Note the factor of e^-1 in the normalisation of the NEST alpha function
nest.Connect(stim2, p2, syn_spec={"model": "static_synapse", "weight": np.exp(-1)*1000*w_eff, "delay": delay})

recorder = nest.Create("multimeter")
nest.SetStatus(recorder, {"record_from": ["V_m"], "to_memory": True, "interval": dt})
nest.Connect(recorder, p2)

nest.Simulate(t_stop + dt)

# for convenience of plotting, we overwrite the V_m recorded from the second NineML neuron
# with that recorded from the NEST neuron
events = nest.GetStatus(recorder, 'events')[0]
ids = events['senders']
values = events["V_m"][ids == p2[0]]
v_m[1:, 1] = values * mV

# Plot results

Figure(
    Panel(synaptic_current, yticks=True, xlim=(0, 120), ylabel="Synaptic current (nA)"),
    Panel(v_m, yticks=True, xlim=(0, 120), xticks=True, xlabel="Time (ms)", ylabel="Membrane potential (mV)"),

).save("test_neuron_model.png")

sim.end()
