# encoding: utf-8
"""
Network model from

    Brunel, N. (2000) J. Comput. Neurosci. 8: 183-208

expressed in NineML using the Python API

Author: Andrew P. Davison, UNIC, CNRS
June 2014
"""

from __future__ import division
from math import exp
import nineml.user_layer as nineml


def build_model(g, eta):
    """
    Build a NineML representation of the Brunel (2000) network model.

    Arguments:
        g: relative strength of inhibitory synapses
        eta: nu_ext / nu_thresh

    Returns:
        a nineml user layer Model object
    """
    order = 250        # scales the size of the network
    Ne = 4 * order     # number of excitatory neurons
    Ni = 1 * order     # number of inhibitory neurons
    epsilon = 0.1      # connection probability
    Ce = int(epsilon * Ne)  # number of excitatory synapses per neuron
    Ci = int(epsilon * Ni)  # number of inhibitory synapses per neuron
    Cext = Ce          # effective number of external synapses per neuron
    delay = 1.5        # (ms) global delay for all neurons in the group
    J = 0.1            # (mV) EPSP size
    Jeff = 24.0*J      # (nA) synaptic weight
    Je = Jeff          # excitatory weights
    Ji = -g * Je       # inhibitory weights
    Jext = Je          # external weights
    theta = 20.0       # firing thresholds
    tau = 20.0         # membrane time constant
    tau_syn = 0.5      # synapse time constant
    #nu_thresh = theta / (Je * Ce * tau * exp(1.0) * tau_syn)  # threshold rate
    nu_thresh = theta / (J * Ce * tau)
    nu_ext = eta * nu_thresh      # external rate per synapse
    input_rate = 1000.0 * nu_ext * Cext   # mean input spiking rate

    neuron_parameters = nineml.ParameterSet(tau=(tau, "ms"),
                                            theta=(theta, "ms"),
                                            tau_rp=(2.0, "ms"),
                                            Vreset=(10.0, "mV"),
                                            R=(1.5, "dimensionless"))  # units??
    psr_parameters = nineml.ParameterSet(tau_syn=(tau_syn, "ms"))
    v_init = nineml.RandomDistribution("uniform(rest,threshold)",
                                       "catalog/randomdistributions/uniform_distribution.xml",  # hack - this file doesn't exist
                                       {'lowerBound': (0.0, "dimensionless"),
                                        'upperBound': (theta, "dimensionless")})
    neuron_initial_values = {"V": (v_init, "mV"),
                             "t_rpend": (0.0, "ms")}
    synapse_initial_values = {"A": (0.0, "nA"), "B": (0.0, "nA")}

    celltype = nineml.SpikingNodeType("nrn", "BrunelIAF.xml", neuron_parameters, initial_values=neuron_initial_values)

    tpoisson_init = nineml.RandomDistribution("exponential(beta)",
                                              "catalog/randomdistributions/exponential_distribution.xml",
                                              {"beta": (1000.0/input_rate, "dimensionless")})
    ext_stim = nineml.SpikingNodeType("stim", "Poisson.xml",
                                      nineml.ParameterSet(rate=(input_rate, "Hz")),
                                      initial_values={"t_next": (tpoisson_init, "ms")})
    psr = nineml.SynapseType("syn", "AlphaPSR.xml", psr_parameters,
                             initial_values=synapse_initial_values)

    exc_cells = nineml.Population("Exc", Ne, celltype, positions=None)
    inh_cells = nineml.Population("Inh", Ni, celltype, positions=None)
    external = nineml.Population("Ext", Ne + Ni, ext_stim, positions=None)

    all_cells = nineml.Selection("All neurons",
                                 nineml.Any(
                                    nineml.Eq("population[@name]", exc_cells.name),
                                    nineml.Eq("population[@name]", inh_cells.name)))

    one_to_one = nineml.ConnectionRule("OneToOne", "OneToOneConnection.xml")
    random_exc = nineml.ConnectionRule("RandomExc", "RandomFanInConnection.xml", {"N": (Ce, "dimensionless")})
    random_inh = nineml.ConnectionRule("RandomInh", "RandomFanInConnection.xml", {"N": (Ci, "dimensionless")})

    static_ext = nineml.ConnectionType("ExternalPlasticity", "StaticConnection.xml",
                                       {"delay": (delay, "ms")}, initial_values={"weight": (Jext, "nA"), "t_next": (1e12, "ms")})
    static_exc = nineml.ConnectionType("ExcitatoryPlasticity", "StaticConnection.xml",
                                       {"delay": (delay, "ms")}, initial_values={"weight": (Je, "nA"), "t_next": (1e12, "ms")})
    static_inh = nineml.ConnectionType("InhibitoryPlasticity", "StaticConnection.xml",
                                       {"delay": (delay, "ms")}, initial_values={"weight": (Ji, "nA"), "t_next": (1e12, "ms")})

    input_prj = nineml.Projection("External", external, all_cells,
                                  rule=one_to_one,
                                  synaptic_response=psr,
                                  synaptic_response_ports=[("Isyn", "Isyn")],
                                  connection_type=static_ext,
                                  connection_ports=[("weight", "q")])
    exc_prj = nineml.Projection("Excitation", exc_cells, all_cells,
                                rule=random_exc,
                                synaptic_response=psr,
                                synaptic_response_ports=[("Isyn", "Isyn")],
                                connection_type=static_exc,
                                connection_ports=[("weight", "q")])
    inh_prj = nineml.Projection("Inhibition", inh_cells, all_cells,
                                rule=random_inh,
                                synaptic_response=psr,
                                synaptic_response_ports=[("Isyn", "Isyn")],
                                connection_type=static_inh,
                                connection_ports=[("weight", "q")])

    network = nineml.Group("BrunelCaseC")
    network.add(exc_cells, inh_cells, external, all_cells)
    network.add(input_prj, exc_prj, inh_prj)
    model = nineml.Model("Brunel (2000) network with alpha synapses")
    model.add_group(network)

    return model


if __name__ == "__main__":
    model = build_model(g=5, eta=2)  # asynchronous irregular
    model.write(__file__.replace(".py", ".xml"))
