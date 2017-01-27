"""
Simple feed-forward network
expressed in NineML using the Python API and then
simulated using the pyNN.nineml module with the NEURON
backend.

"""

from __future__ import division
from os.path import dirname, join
from datetime import datetime
from pyNN.nineml.read import Network
from pyNN.utility import SimulationProgressBar
import nineml.user as nineml
from nineml.units import ms, mV, nA, unitless, Hz, Mohm
from utility import psp_height

#CATALOG_URL = "/home/docker/projects/nineml_demo_2016/catalog/xml/"
CATALOG_URL = "/home/andrew/dev/NineML_demo_2016/catalog/xml/"

def run_simulation(parameters, plot_figure=False):
    """

    """
    import pyNN.neuron as sim

    timestamp = datetime.now()
    model = build_model(**parameters["network"])
    if "full_filename" in parameters["experiment"]:
        xml_file = parameters["experiment"]["full_filename"].replace(".h5", ".xml")
    else:
        xml_file = "{}.xml".format(parameters["experiment"]["base_filename"])
    model.write(xml_file)
    print("Exported model to file {}".format(xml_file))

    sim.setup()

    print("Building network")
    net = Network(sim, xml_file)

    stim = net.populations["Ext"]
    stim.record('spikes')
    exc = net.populations["Exc"]
    exc.record("spikes")
    exc[:3].record(["nrn_v", "syn_a"])

    print("Running simulation")
    t_stop = parameters["experiment"]["duration"]
    pb = SimulationProgressBar(t_stop/80, t_stop)
    sim.run(t_stop, callbacks=[pb])

    print("Handling data")
    data = {}
    if plot_figure:
        data["stim"] = stim.get_data().segments[0]
        data["exc"] = exc.get_data().segments[0]
        data["exc"].annotate(simulator="lib9ML with pyNN.neuron")
    else:
        if "full_filename" in parameters["experiment"]:
            filename = parameters["experiment"]["full_filename"]
        else:
            filename = "{}_nineml_{:%Y%m%d%H%M%S}.pkl".format(parameters["experiment"]["base_filename"],
                                                              timestamp)
        print("Writing data to {}".format(filename))
        exc.write_data(filename)

    sim.end()
    return data


def build_model(N=100, delay=1.5, weight=0.1, theta=20.0,
                tau=20.0, tau_syn=0.1, tau_refrac=2.0, v_reset=10.0,
                R=1.5, interval=5.0):
    """
    docstring missing
    """

    neuron_parameters = nineml.PropertySet(tau=(tau, ms),
                                           v_threshold=(theta, mV),
                                           refractory_period=(tau_refrac, ms),
                                           v_reset=(v_reset, mV),
                                           R=(R, Mohm))
    psr_parameters = nineml.PropertySet(tau=(tau_syn, ms))
    v_init = v_reset
    neuron_initial_values = {"v": (v_init, mV),
                             "refractory_end": (0.0, ms)}
    synapse_initial_values = {"a": (0.0, nA), "b": (0.0, nA)}

    celltype = nineml.SpikingNodeType("nrn", CATALOG_URL + "neuron/LeakyIntegrateAndFire.xml",
                                      neuron_parameters,
                                      initial_values=neuron_initial_values)
    ext_stim = nineml.SpikingNodeType("stim", join(dirname(__file__), "Tonic.xml"),
                                      nineml.PropertySet(interval=(interval, ms)),
                                      initial_values={"t_next": (10.0, ms)})
    psr = nineml.SynapseType("syn", CATALOG_URL + "postsynapticresponse/Alpha.xml",
                             psr_parameters,
                             initial_values=synapse_initial_values)

    exc_cells = nineml.Population("Exc", N, celltype, positions=None)
    external = nineml.Population("Ext", N, ext_stim, positions=None)

    one_to_one = nineml.ConnectionRuleComponent("AllToAll",
                                                CATALOG_URL + "connectionrule/AllToAll.xml")

    static_ext = nineml.ConnectionType("ExternalPlasticity",
                                       CATALOG_URL + "plasticity/Static.xml",
                                       nineml.PropertySet(weight=(weight, nA)))

    input_prj = nineml.Projection("External", external, exc_cells,
                                  connectivity=one_to_one,
                                  response=psr,
                                  plasticity=static_ext,
                                  port_connections=[nineml.PortConnection("plasticity", "response", "fixed_weight", "weight"),
                                                    nineml.PortConnection("response", "destination", "i_synaptic", "i_synaptic")],
                                  delay=(delay, ms))

    network = nineml.Network("SimpleNetwork")
    network.add(exc_cells, external)
    network.add(input_prj)

    return network
