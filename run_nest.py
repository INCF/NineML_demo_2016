"""

Based on the brunel-alpha-nest.py example from the NEST distribution
"""

from datetime import datetime
import numpy as np
from quantities import ms
import nest
#from numpy import exp
import neo

#
# def ComputePSPnorm(tauMem, CMem, tauSyn):
#   """Compute the maximum of postsynaptic potential
#      for a synaptic input current of unit amplitude
#      (1 pA)"""
#
#   a = (tauMem / tauSyn)
#   b = (1.0 / tauSyn - 1.0 / tauMem)
#
#   # time of maximum
#   t_max = 1.0/b * ( -nest.sli_func('LambertWm1',-exp(-1.0/a)/a) - 1.0/a )
#
#   # maximum of PSP for current of unit amplitude
#   return exp(1.0)/(tauSyn*CMem*b) * ((exp(-t_max/tauMem) - exp(-t_max/tauSyn)) / b - t_max*exp(-t_max/tauSyn))
#

def segment_from_recording_device(devices, variables_to_include, id_lists, t_stop, name="segment00"):

    def get_data(device, variable, id_list):
        events = nest.GetStatus(device, 'events')[0]
        ids = events['senders']
        values = events[variable]
        data = {}
        for id in id_list:
            data[id] = values[ids==id]
        assert len(data) > 0
        return data

    segment = neo.Segment(name=name, rec_datetime=datetime.now())

    for device, variable, id_list in zip(devices, variables_to_include, id_lists):
        print name, device, variable
        data = get_data(device, variable, id_list)
        if variable == 'times':
            print "  adding spiketrain"
            id0 = min(id_list)
            segment.spiketrains = [
                neo.SpikeTrain(spiketrain,
                               t_start=0.0,
                               t_stop=t_stop,
                               units='ms',
                               source_id=id,
                               source_index=id - id0)
                for id, spiketrain in data.items()]
        else:
            print "  adding signal"
            source_ids = np.array(id_list)
            channel_indices = source_ids - source_ids.min()
            signal_array = np.vstack(data.values()).T
            segment.analogsignalarrays = [
                neo.AnalogSignalArray(
                    signal_array,
                    units='mV',
                    t_start=0.0*ms,
                    sampling_period=0.1*ms,
                    name=variable,
                    channel_index=channel_indices,
                    source_ids=source_ids)]
    return segment


def run_simulation(parameters, plot_figure=False):
    """

    """
    dt = 0.1
    nest.ResetKernel()
    nest.SetKernelStatus({"resolution": dt, "print_time": True, 'local_num_threads': 1})

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
            nest.SetStatus(device, {"record_from": ["V_m"], "to_memory": True})

        #nest.SetStatus(ispikes, [{"label": "brunel-py-stim", "withtime": True, "withgid": True}])
        #nest.SetStatus(espikes, [{"label": "brunel-py-ex", "withtime": True, "withgid": True}])
        #nest.SetStatus(ispikes, [{"label": "brunel-py-in", "withtime": True, "withgid": True}])

        nest.Connect(stim[:100], sspikes, syn_spec="excitatory")
#         exc.sample(50).record("spikes")
        nest.Connect(exc[:50], espikes, syn_spec="excitatory")  # should be a random sample
#         exc.sample(3).record(["nrn_V", "syn_A"])
        nest.Connect(evm, exc[:3], syn_spec="excitatory")
#         inh.sample(50).record("spikes")
        nest.Connect(inh[:50], ispikes, syn_spec="excitatory")  # should be a random sample
#         inh.sample(3).record(["nrn_V", "syn_A"])
        nest.Connect(ivm, inh[:3], syn_spec="excitatory")
    else:
        all_spikes = nest.Create("spike_detector")
        nest.SetStatus(all_spikes, [{"label": "brunel-py-all", "withtime": True, "withgid": True}])
        nest.Connect(exc + inh, all_spikes, syn_spec="excitatory")
#         all = net.assemblies["All neurons"]
#         #all.sample(50).record("spikes")
#         all.record("spikes")

    print("Simulating")
    simtime = parameters["experiment"]["duration"]
    nest.Simulate(simtime)

    print("Handling data")
    data = {}
    if plot_figure:
        data["stim"] = segment_from_recording_device([sspikes], ['times'], [stim[:100]], simtime, "stim")
        data["exc"] = segment_from_recording_device([espikes, evm], ['times', 'V_m'], [exc[:50], exc[:3]], simtime, "exc")
        data["inh"] = segment_from_recording_device([ispikes, ivm], ['times', 'V_m'], [inh[:50], inh[:3]], simtime, "inh")
    else:
        data["all"] = segment_from_recording_device([all_spikes], ['times'], [exc + inh], simtime, "all")
        block = neo.Block()
        block.segments.append(data["all"])
        filename = "{}_nineml.h5".format(parameters["experiment"]["base_filename"])
        io = neo.get_io(filename)
        io.write(data["all"])

    #import pdb; pdb.set_trace()
    return data


def build_network(order=1000, epsilon=0.1, delay=1.5, J=0.1, theta=20.0,
                  tau=20.0, tau_syn=0.1, tau_refrac=2.0, v_reset=10.0,
                  R=1.5, g=5, eta=2):

    NE = 4 * order
    NI = 1 * order
    N_neurons = NE + NI
    CE = int(epsilon * NE)  # number of excitatory synapses per neuron
    CI = int(epsilon * NI)  # number of inhibitory synapses per neuron
    C_tot = CI + CE         # total number of synapses per neuron

    J_unit = 0.001/24.0  #ComputePSPnorm(tauMem, CMem, tauSyn)
    J_ex  = J / J_unit
    J_in  = -g * J_ex

    CMem = 1000 * tau/R  #  ??
    nu_th = theta / (J * CE * tau)
    #nu_th  = (theta * CMem) / (J_ex*CE*exp(1)*tauMem*tauSyn)
    nu_ex  = eta*nu_th
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




