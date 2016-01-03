"""
Network model from

    Brunel, N. (2000) J. Comput. Neurosci. 8: 183-208

expressed in NineML using the Python API and then
simulated using the pyNN.nineml module with the NEURON
backend.

"""

from __future__ import division
from datetime import datetime
import pyNN.neuron as sim
from pyNN.nineml.read import Network
from pyNN.utility import SimulationProgressBar
import nineml.user as nineml
from nineml.units import ms, mV, nA, unitless, Hz, Mohm
from utility import psp_height


def run_simulation(parameters, plot_figure=False):
    """

    """
    timestamp = datetime.now()
    model = build_model(**parameters["network"])
    if "full_filename" in parameters["experiment"]:
        xml_file = parameters["experiment"]["full_filename"].replace(".h5", ".xml")
    else:
        xml_file = "{}.xml".format(parameters["experiment"]["base_filename"])
    model.write(xml_file)

    sim.setup()

    print("Building network")
    net = Network(sim, xml_file)

    if plot_figure:
        stim = net.populations["Ext"]
        stim[:100].record('spikes')
        exc = net.populations["Exc"]
        exc.sample(50).record("spikes")
        exc.sample(3).record(["nrn_v", "syn_a"])
        inh = net.populations["Inh"]
        inh.sample(50).record("spikes")
        inh.sample(3).record(["nrn_v", "syn_a"])
    else:
        all = net.assemblies["All"]
        all.sample(parameters["experiment"]["n_record"]).record("spikes")

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
            filename = "{}_nineml_{:%Y%m%d%H%M%S}.h5".format(parameters["experiment"]["base_filename"],
                                                             timestamp)
        print("Writing data to {}".format(filename))
        all.write_data(filename)

    sim.end()
    return data


def build_model(order=1000, epsilon=0.1, delay=1.5, J=0.1, theta=20.0,
                tau=20.0, tau_syn=0.1, tau_refrac=2.0, v_reset=10.0,
                R=1.5, g=5, eta=2):
    """
    Build a NineML representation of the Brunel (2000) network model.

    Arguments:
        g: relative strength of inhibitory synapses
        eta: nu_ext / nu_thresh

    Returns:
        a nineml user layer Model object
    """
    Ne = 4 * order     # number of excitatory neurons
    Ni = 1 * order     # number of inhibitory neurons
    Ce = int(epsilon * Ne)  # number of excitatory synapses per neuron
    Ci = int(epsilon * Ni)  # number of inhibitory synapses per neuron
    Cext = Ce          # effective number of external synapses per neuron
    scale_factor = psp_height(tau, R, tau_syn)
    Jeff = J/scale_factor  # (nA) synaptic weight
    Je = Jeff          # excitatory weights
    Ji = -g * Je       # inhibitory weights
    Jext = Je          # external weights
    nu_thresh = theta / (Je * Ce * R * tau_syn)  # threshold rate
    nu_ext = eta * nu_thresh      # external rate per synapse
    input_rate = 1000.0 * nu_ext * Cext   # mean input spiking rate

    neuron_parameters = nineml.PropertySet(tau=(tau, ms),
                                           v_threshold=(theta, mV),
                                           refractory_period=(tau_refrac, ms),
                                           v_reset=(v_reset, mV),
                                           R=(R, Mohm))
    psr_parameters = nineml.PropertySet(tau=(tau_syn, ms))
    v_init = nineml.RandomDistributionComponent(
        "uniform_rest_to_threshold",
        "sources/UniformDistribution.xml",
        {'minimum': (0.0, unitless),
         'maximum': (theta, unitless)})
    neuron_initial_values = {"v": (v_init, mV),
                             "refractory_end": (0.0, ms)}
    synapse_initial_values = {"a": (0.0, nA), "b": (0.0, nA)}

    celltype = nineml.SpikingNodeType("nrn", "sources/BrunelIaF.xml", neuron_parameters,
                                      initial_values=neuron_initial_values)
    tpoisson_init = nineml.RandomDistributionComponent(
        "exponential_first_spike_time",
        "sources/ExponentialDistribution.xml",
        {"rate": (input_rate, unitless)})

    ext_stim = nineml.SpikingNodeType("stim", "sources/Poisson.xml",
                                      nineml.PropertySet(rate=(input_rate, Hz)),
                                      initial_values={"t_next": (tpoisson_init, ms)})
    psr = nineml.SynapseType("syn", "sources/AlphaPSR.xml", psr_parameters,
                             initial_values=synapse_initial_values)

    exc_cells = nineml.Population("Exc", Ne, celltype, positions=None)
    inh_cells = nineml.Population("Inh", Ni, celltype, positions=None)
    external = nineml.Population("Ext", Ne + Ni, ext_stim, positions=None)

    all_cells = nineml.Selection("All",
                                 nineml.Concatenate(exc_cells, inh_cells))

    one_to_one = nineml.ConnectionRuleComponent("OneToOne", "sources/OneToOne.xml")
    random_exc = nineml.ConnectionRuleComponent("RandomExc", "sources/RandomFanIn.xml", {"number": (Ce, unitless)})
    random_inh = nineml.ConnectionRuleComponent("RandomInh", "sources/RandomFanIn.xml", {"number": (Ci, unitless)})

    static_ext = nineml.ConnectionType("ExternalPlasticity", "sources/StaticConnection.xml",
                                       initial_values={"weight": (Jext, nA)})
    static_exc = nineml.ConnectionType("ExcitatoryPlasticity", "sources/StaticConnection.xml",
                                       initial_values={"weight": (Je, nA)})
    static_inh = nineml.ConnectionType("InhibitoryPlasticity", "sources/StaticConnection.xml",
                                       initial_values={"weight": (Ji, nA)})

    input_prj = nineml.Projection("External", external, all_cells,
                                  connectivity=one_to_one,
                                  response=psr,
                                  plasticity=static_ext,
                                  port_connections=[nineml.PortConnection("plasticity", "response", "fixed_weight", "weight"),
                                                    nineml.PortConnection("response", "destination", "i_synaptic", "i_synaptic")],
                                  delay=(delay, ms))
    exc_prj = nineml.Projection("Excitation", exc_cells, all_cells,
                                connectivity=random_exc,
                                response=psr,
                                plasticity=static_exc,
                                port_connections=[nineml.PortConnection("plasticity", "response", "fixed_weight", "weight"),
                                                  nineml.PortConnection("response", "destination", "i_synaptic", "i_synaptic")],
                                delay=(delay, ms))
    inh_prj = nineml.Projection("Inhibition", inh_cells, all_cells,
                                connectivity=random_inh,
                                response=psr,
                                plasticity=static_inh,
                                port_connections=[nineml.PortConnection("plasticity", "response", "fixed_weight", "weight"),
                                                  nineml.PortConnection("response", "destination", "i_synaptic", "i_synaptic")],
                                delay=(delay, ms))

    network = nineml.Network("BrunelCaseC")
    network.add(exc_cells, inh_cells, external, all_cells)
    network.add(input_prj, exc_prj, inh_prj)

    return network
