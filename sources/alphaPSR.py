import nineml.abstraction as al
from nineml.units import current, time

model = al.Dynamics(
    name="AlphaPSR",
    aliases=["i_synaptic := a"],
    regimes=[
        al.Regime(
            name="default",
            time_derivatives=[
                "da/dt = (b - a)/tau",
                "db/dt = -b/tau"],
            transitions=al.On('spike',
                              do=["b = b + weight"]),
        )
    ],
    state_variables=[
        al.StateVariable('a', dimension=current),
        al.StateVariable('b', dimension=current),
    ],
    analog_ports=[al.AnalogSendPort("i_synaptic", dimension=current),
                  al.AnalogSendPort("a", dimension=current),
                  al.AnalogSendPort("b", dimension=current),
                  al.AnalogReceivePort("weight", dimension=current)],
    parameters=[al.Parameter('tau', dimension=time)]
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
