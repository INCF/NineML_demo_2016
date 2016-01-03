"""

"""

import nineml.abstraction as al
from nineml.units import voltage, time, resistance, current

model = al.Dynamics(
    name="BrunelIaF",
    regimes=[
        al.Regime(
            name="subthreshold",
            time_derivatives=["dv/dt = (-v + R*i_synaptic)/tau"],
            transitions=al.On("v > v_threshold",
                              do=["refractory_end = t + refractory_period",
                                  "v = v_reset",
                                  al.OutputEvent('spike_output')],
                              to="refractory"),
        ),
        al.Regime(
            name="refractory",
            transitions=[al.On("t > refractory_end",
                               to="subthreshold")],
        )
    ],
    state_variables=[
        al.StateVariable('v', dimension=voltage),
        al.StateVariable('refractory_end', dimension=time)],
    analog_ports=[
        al.AnalogSendPort("v", dimension=voltage),
        al.AnalogSendPort("refractory_end", dimension=time),
        al.AnalogReducePort("i_synaptic", operator="+", dimension=current)],
    event_ports=[
        al.EventSendPort('spike_output'),
        ],
    parameters=[
        al.Parameter('tau', time),
        al.Parameter('v_threshold', voltage),
        al.Parameter('refractory_period', time),
        al.Parameter('v_reset', voltage),
        al.Parameter('R', resistance)]
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
