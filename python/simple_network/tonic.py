"""

"""

import nineml.abstraction as al
from nineml.units import time

model = al.Dynamics(
    name="Tonic",
    regimes=[
        al.Regime(
            name="default",
            transitions=al.On("t > t_next",
                              do=["t_next = t + interval",
                                  al.OutputEvent('spikeOutput')]))
    ],
    event_ports=[al.EventSendPort('spikeOutput')],
    state_variables=[al.StateVariable('t_next', dimension=time)],
    parameters=[al.Parameter('interval', dimension=time)],
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
