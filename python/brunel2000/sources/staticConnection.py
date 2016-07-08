import nineml.abstraction as al
from nineml.units import current, A, s

model = al.Dynamics(
    name="StaticConnection",
    regimes=[
        al.Regime(
            name="default",
            time_derivatives=[
                "dfixed_weight/dt = zero"],
        )
    ],
    state_variables=[
        al.StateVariable('fixed_weight', dimension=current),  # TGC 4/15 what is the point of this state variable, where is it read? @IgnorePep8
    ],
    analog_ports=[al.AnalogSendPort("fixed_weight", dimension=current)],
    constants=[al.Constant('zero', 0.0, A / s)],
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
