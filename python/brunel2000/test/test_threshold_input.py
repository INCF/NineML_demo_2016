"""
This script models three neurons defined by a NineML model.

Each receives Poisson input of a different rate. The rates are
calculated so that the first neuron is always sub-threshold,
the second neuron would have a mean membrane potential exactly
at threshold in the absence of spiking, and the third neuron would
have a mean potential above threshold in the absence of spiking.

Andrew Davison, November 2015
"""

from __future__ import division, print_function
from copy import copy
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


t_stop = 500
dt = 0.01
cell_parameters = {'nrn_R': 1.5, 'nrn_v_reset': 10.0, 'nrn_tau': 20.0,
                   'nrn_refractory_period': 2.0, 'nrn_v_threshold': 20.0, 'syn_tau': 0.1}
weight = 0.1  # EPSP height from a single spike received at resting potential
scale_factor = psp_height(cell_parameters['nrn_tau'],
                          cell_parameters["nrn_R"],
                          cell_parameters["syn_tau"])
w_eff = weight/scale_factor
delay = 0.5
cm = cell_parameters['nrn_tau']/cell_parameters['nrn_R']
nu_thresh = 1000.0 * cell_parameters['nrn_v_threshold'] * cm / (
               w_eff * cell_parameters['nrn_tau'] * cell_parameters['syn_tau'])

print("\ntau = {}, R = {}, tau_syn = {}".format(cell_parameters['nrn_tau'],
                                                cell_parameters["nrn_R"],
                                                cell_parameters["syn_tau"]))
print("\nEffective weight = {} nA".format(w_eff))
print("Threshold rate = {} Hz\n".format(nu_thresh))

# PyNN/NineML simulation

sim.setup(timestep=dt)

celltype = Dynamics(name='iaf',
                    subnodes={'nrn': read("../sources/BrunelIaF.xml")['BrunelIaF'],
                              'syn': read("../sources/AlphaPSR.xml")['AlphaPSR']})
celltype.connect_ports('syn.i_synaptic', 'nrn.i_synaptic')
p1 = sim.Population(4, nineml_cell_type('BrunelIaF', celltype, {'syn': 'syn_weight'})(**cell_parameters))
cell_parameters_no_spikes = copy(cell_parameters)
cell_parameters_no_spikes["nrn_v_threshold"] = 1000.0
p2 = sim.Population(4, nineml_cell_type('BrunelIaF', celltype, {'syn': 'syn_weight'})(**cell_parameters_no_spikes))

stim = sim.Population(4,
                      nineml_cell_type('Poisson', read("../sources/Poisson.xml")['Poisson'], {})(
                          rate=[0.5*nu_thresh, nu_thresh, 2*nu_thresh, 0.0]))

prj1 = sim.Projection(stim, p1,
                      sim.OneToOneConnector(),
                      sim.StaticSynapse(weight=w_eff, delay=delay),
                      receptor_type='syn')
prj2 = sim.Projection(stim, p2,
                      sim.OneToOneConnector(),
                      sim.StaticSynapse(weight=w_eff, delay=delay),
                      receptor_type='syn')

p1.record(['nrn_v', 'syn_a', 'syn_b'])
p2.record(['nrn_v', 'syn_a', 'syn_b'])

sim.run(t_stop)

v_m1 = p1.get_data().segments[0].filter(name='nrn_v')[0]
v_m2 = p2.get_data().segments[0].filter(name='nrn_v')[0]


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
                 "V_th":       cell_parameters_no_spikes["nrn_v_threshold"]}

nest.SetDefaults("iaf_psc_alpha", neuron_params)
p2 = nest.Create("iaf_psc_alpha", 1)
stim2 = nest.Create("poisson_generator")
nest.SetStatus(stim2, {"rate": nu_thresh})
# Note the factor of e^-1 in the normalisation of the NEST alpha function
nest.Connect(stim2, p2, syn_spec={"model": "static_synapse", "weight": np.exp(-1)*1000*w_eff, "delay": delay})

recorder = nest.Create("multimeter")
nest.SetStatus(recorder, {"record_from": ["V_m"], "to_memory": True, "interval": dt})
nest.Connect(recorder, p2)

nest.Simulate(t_stop + dt)

# for convenience of plotting, we overwrite the V_m recorded from the 4th NineML neuron
# with that recorded from the NEST neuron
events = nest.GetStatus(recorder, 'events')[0]
ids = events['senders']
values = events["V_m"]
print("Weight (NEST): {}".format(np.exp(-1)*1000*w_eff))
print("nu_thresh: {}".format(nu_thresh))
print("V_m in NEST: {} += {} mV".format(values.mean(), values.std()))
v_m2[1:, 3] = values[ids == p2[0]] * mV


# Plot results

Figure(
    Panel(v_m1, yticks=True, xlim=(0, t_stop), xticks=True, xlabel="Time (ms)"),
    Panel(v_m2, yticks=True, xlim=(0, t_stop), xticks=True, xlabel="Time (ms)"),
).save("test_threshold_input.png")

sim.end()
