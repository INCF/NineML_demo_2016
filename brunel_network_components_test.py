# encoding: utf-8
"""
Test of the 9ML components for the Brunel (2000) network model
by creating a network of three neurons.

This script defines the network and exports to XML, but does not run any simulation.
It is used by "run_brunel_test.py"

Author: Andrew P. Davison, UNIC, CNRS
June 2014
"""

from __future__ import division
import nineml.user_layer as nineml

delay = 1.5          # (ms) global delay for all neurons in the group
J = 0.1              # (mV) EPSP size
Jeff = 24.0*J        # (nA) synaptic weight
g = 5.0              # relative strength of inhibitory synapses
eta = 2.0            # nu_ext / nu_thresh
Je = Jeff            # excitatory weights
Ji = -g * Je         # inhibitory weights
Jext = Je            # external weights
theta = 20.0         # firing thresholds
tau = 20.0           # membrane time constant
tau_syn = 0.5        # synapse time constant
input_rate = 10.0  # mean input spiking rate

neuron_parameters = nineml.ParameterSet(tau=(tau, "ms"),
                                        theta=(theta, "ms"),
                                        tau_rp=(2.0, "ms"),
                                        Vreset=(10.0, "mV"),
                                        R=(1.5, "dimensionless"))  # units??
psr_parameters = nineml.ParameterSet(tau_syn=(tau_syn, "ms"))
neuron_initial_values = {"V": (0.0, "mV"),  # todo: use random distr.
                         "t_rpend": (0.0, "ms")}
synapse_initial_values = {"A": (0.0, "nA"), "B": (0.0, "nA")}

celltype = nineml.SpikingNodeType("nrn", "BrunelIAF.xml", neuron_parameters, initial_values=neuron_initial_values)
ext_stim = nineml.SpikingNodeType("stim", "Poisson.xml", nineml.ParameterSet(rate=(input_rate, "Hz")),
                                  initial_values={"t_next": (0.0, "ms")})
psr = nineml.SynapseType("syn", "AlphaPSR.xml", psr_parameters, initial_values=synapse_initial_values)

exc_cells = nineml.Population("Exc", 1, celltype, positions=None)
inh_cells = nineml.Population("Inh", 1, celltype, positions=None)
external = nineml.Population("Ext", 1, ext_stim, positions=None)

all_cells = nineml.Selection("All neurons",
                             nineml.Any(
                                nineml.Eq("population[@name]", exc_cells.name),
                                nineml.Eq("population[@name]", inh_cells.name)))

all_to_all = nineml.ConnectionRule("AllToAll", "AllToAllConnection.xml")


static_ext = nineml.ConnectionType("ExternalPlasticity", "StaticConnection.xml",
                                   {"delay": (delay, "ms")}, initial_values={"weight": (Jext, "nA"), "t_next": (1e12, "ms")})
static_exc = nineml.ConnectionType("ExcitatoryPlasticity", "StaticConnection.xml",
                                   {"delay": (delay, "ms")}, initial_values={"weight": (Je, "nA"), "t_next": (1e12, "ms")})
static_inh = nineml.ConnectionType("InhibitoryPlasticity", "StaticConnection.xml",
                                   {"delay": (delay, "ms")}, initial_values={"weight": (Ji, "nA"), "t_next": (1e12, "ms")})

input_prj = nineml.Projection("External", external, all_cells,
                              rule=all_to_all,
                              synaptic_response=psr,
                              synaptic_response_ports=[("Isyn", "Isyn")],
                              connection_type=static_ext,
                              connection_ports=[("weight", "q")])
exc_prj = nineml.Projection("Excitation", exc_cells, all_cells,
                            rule=all_to_all,
                            synaptic_response=psr,
                            synaptic_response_ports=[("Isyn", "Isyn")],
                            connection_type=static_exc,
                            connection_ports=[("weight", "q")])
inh_prj = nineml.Projection("Inhibition", inh_cells, all_cells,
                            rule=all_to_all,
                            synaptic_response=psr,
                            synaptic_response_ports=[("Isyn", "Isyn")],
                            connection_type=static_inh,
                            connection_ports=[("weight", "q")])

network = nineml.Group("BrunelCaseC")
network.add(exc_cells, inh_cells, external, all_cells)
network.add(input_prj, exc_prj, inh_prj)
model = nineml.Model("Three-neuron network with alpha synapses")
model.add_group(network)


if __name__ == "__main__":
    model.write(__file__.replace(".py", ".xml"))
