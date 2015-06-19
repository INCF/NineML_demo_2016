"""

"""

from __future__ import division, print_function
from datetime import datetime
from numpy import exp, random
from pyNN.utility import SimulationProgressBar
from utility import psp_height


def run_simulation(parameters, plot_figure=False):
    """

    """
    timestamp = datetime.now()
    dt = 0.1
    simulator_name = parameters["simulator"]
    exec("import {} as sim".format(simulator_name))

    sim.setup(timestep=dt)

    print("Building network")
    stim, exc, inh = build_network(sim, **parameters["network"])

    if plot_figure:
        stim[:100].record('spikes')
        exc.sample(50).record("spikes")
        exc.sample(3).record("v")
        inh.sample(50).record("spikes")
        inh.sample(3).record("v")
    else:
        all = exc + inh
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
            filename = "{}_{}_{:%Y%m%d%H%M%S}.h5".format(parameters["experiment"]["base_filename"],
                                                         parameters["simulator"],
                                                         timestamp)
        all.write_data(filename)

    sim.end()
    return data


def build_network(sim, order=1000, epsilon=0.1, delay=1.5, J=0.1, theta=20.0,
                  tau=20.0, tau_syn=0.1, tau_refrac=2.0, v_reset=10.0,
                  R=1.5, g=5, eta=2):

    NE = 4 * order
    NI = 1 * order
    CE = int(epsilon * NE)  # number of excitatory synapses per neuron
    CI = int(epsilon * NI)  # number of inhibitory synapses per neuron

    CMem = tau/R

    J_unit = exp(1)*psp_height(tau, R, tau_syn)
    J_ex  = J / J_unit
    J_in  = -g * J_ex

    nu_th = theta / (J * CE * tau)
    #nu_th  = (theta * CMem) / (J_ex*CE*exp(1)*tauMem*tauSyn)
    nu_ex = eta * nu_th
    p_rate = 1000.0 * nu_ex * CE

    print("Building network")

    neuron_params = {"cm":        CMem,
                     "tau_m":      tau,
                     "tau_syn_E":  tau_syn,
                     "tau_syn_I":  tau_syn,
                     "tau_refrac": tau_refrac,
                     "v_rest":     0.0,
                     "v_reset":    v_reset,
                     "v_thresh":   theta}

    exc = sim.Population(NE, sim.IF_curr_alpha(**neuron_params))
    inh = sim.Population(NI, sim.IF_curr_alpha(**neuron_params))
    all = exc + inh
    all.initialize(v=0.0)

    stim = sim.Population(NE + NI, sim.SpikeSourcePoisson(rate=p_rate))

    print("Connecting network")

    exc_synapse = sim.StaticSynapse(weight=J_ex, delay=delay)
    inh_synapse = sim.StaticSynapse(weight=J_in, delay=delay)

    input_connections = sim.Projection(stim, all, sim.OneToOneConnector(), exc_synapse)
    exc_connections = sim.Projection(exc, all, sim.FixedNumberPreConnector(n=CE), exc_synapse)  # check is Pre not Post
    inh_connections = sim.Projection(inh, all, sim.FixedNumberPreConnector(n=CI), inh_synapse)

    return stim, exc, inh
