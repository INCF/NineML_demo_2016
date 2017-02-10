"""

Based on the brunel-alpha-nest.py example from the NEST distribution
"""

from __future__ import division, print_function
from datetime import datetime
import nest
from numpy import exp, random
import neo
from utility import segment_from_recording_device, psp_height


def run_simulation(parameters, plot_figure=False):
    """

    """
    timestamp = datetime.now()
    dt = parameters["experiment"]["timestep"]
    nest.ResetKernel()
    seed = parameters["experiment"]["seed"]
    nest.SetKernelStatus({"resolution": dt, "print_time": True, 'local_num_threads': 1,
                          "rng_seeds": [seed],
                          "grng_seed": seed + 1})

    stim, exc, inh = build_network(**parameters["network"])

    if plot_figure:
        sspikes = nest.Create("spike_detector")
        espikes = nest.Create("spike_detector")
        ispikes = nest.Create("spike_detector")
        for device in (sspikes, espikes, ispikes):
            nest.SetStatus(device, {"to_memory": True, "withtime": True, "withgid": True})
        evm = nest.Create("multimeter")
        ivm = nest.Create("multimeter")
        for device in (evm, ivm):
            nest.SetStatus(device, {"record_from": ["V_m"], "to_memory": True,
                                    "interval": dt})

        nest.Connect(stim[:100], sspikes, syn_spec="excitatory")
        nest.Connect(exc[:50], espikes, syn_spec="excitatory")  # should be a random sample
        nest.Connect(evm, exc[:3], syn_spec="excitatory")
        nest.Connect(inh[:50], ispikes, syn_spec="excitatory")  # should be a random sample
        nest.Connect(ivm, inh[:3], syn_spec="excitatory")
    else:
        all_spikes = nest.Create("spike_detector")
        nest.SetStatus(all_spikes, [{"label": "brunel-py-all", "withtime": True, "withgid": True}])
        to_record = random.permutation(exc + inh)[:parameters["experiment"]["n_record"]].tolist()
        nest.Connect(to_record, all_spikes, syn_spec="excitatory")

    print("Simulating")
    simtime = parameters["experiment"]["duration"]
    nest.Simulate(simtime + dt)

    print("Handling data")
    data = {}
    if plot_figure:
        data["stim"] = segment_from_recording_device([sspikes], ['times'], [stim[:100]], simtime, "stim")
        data["exc"] = segment_from_recording_device([espikes, evm], ['times', 'V_m'], [exc[:50], exc[:3]], simtime, "exc")
        data["inh"] = segment_from_recording_device([ispikes, ivm], ['times', 'V_m'], [inh[:50], inh[:3]], simtime, "inh")
    else:
        data["all"] = segment_from_recording_device([all_spikes], ['times'], [to_record], simtime, "all")
        block = neo.Block()
        block.segments.append(data["all"])
        if "full_filename" in parameters["experiment"]:
            filename = parameters["experiment"]["full_filename"]
        else:
            filename = "{}_nest_{:%Y%m%d%H%M%S}.h5".format(parameters["experiment"]["base_filename"],
                                                           timestamp)
        io = neo.get_io(filename)
        io.write(block)

    #import pdb; pdb.set_trace()
    return data


def build_network(order=1000, epsilon=0.1, delay=1.5, J=0.1, theta=20.0,
                  tau=20.0, tau_syn=0.1, tau_refrac=2.0, v_reset=10.0,
                  R=1.5, g=5, eta=2):

    NE = 4 * order
    NI = 1 * order
    CE = int(epsilon * NE)  # number of excitatory synapses per neuron
    CI = int(epsilon * NI)  # number of inhibitory synapses per neuron

    CMem = 1000 * tau/R

    J_unit = 0.001*exp(1)*psp_height(tau, R, tau_syn)
    J_ex  = J / J_unit
    J_in  = -g * J_ex

    nu_th  = (theta * CMem) / (J_ex * CE * exp(1) * tau * tau_syn)
    nu_ex = eta*nu_th
    p_rate = 1000.0*nu_ex*CE

    print("Building network")

    neuron_params = {"C_m":        CMem,
                     "tau_m":      tau,
                     "tau_syn_ex": tau_syn,
                     "tau_syn_in": tau_syn,
                     "t_ref":      tau_refrac,
                     "E_L":        0.0,
                     "V_reset":    v_reset,
                     "V_m":        0.0,
                     "V_th":       theta}

    nest.SetDefaults("iaf_psc_alpha", neuron_params)

    exc = nest.Create("iaf_psc_alpha", NE)
    inh = nest.Create("iaf_psc_alpha", NI)

    nest.SetDefaults("poisson_generator", {"rate": p_rate})
    stim = nest.Create("poisson_generator")

    print("Connecting network")

    nest.CopyModel("static_synapse", "excitatory", {"weight": J_ex, "delay": delay})
    nest.CopyModel("static_synapse", "inhibitory", {"weight": J_in, "delay": delay})

    nest.Connect(stim, exc, syn_spec="excitatory")
    nest.Connect(stim, inh, syn_spec="excitatory")


    # We now iterate over all neuron IDs, and connect the neuron to
    # the sources from our array. The first loop connects the excitatory neurons
    # and the second loop the inhibitory neurons.

    print("Excitatory connections")

    conn_params_ex = {'rule': 'fixed_indegree', 'indegree': CE}
    nest.Connect(exc, exc + inh, conn_params_ex, "excitatory")

    print("Inhibitory connections")

    conn_params_in = {'rule': 'fixed_indegree', 'indegree': CI}
    nest.Connect(inh, exc + inh, conn_params_in, "inhibitory")

    return stim, exc, inh
