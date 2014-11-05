import nineml.abstraction_layer as al


model = al.ComponentClass(
    name="AlphaPSR",
    aliases=["Isyn := A"],
    regimes=[
        al.Regime(
            name="default",
            time_derivatives=[
                "dA/dt = (B - A)/tau_syn",
                "dB/dt = (-B)/tau_syn"],
            transitions=al.On('spike',
                              do=["B = B + q"]),  # would be nice to allow constant quantities, so we could make q dimensionless
        )
    ],
    state_variables=[
        al.StateVariable('A', dimension="current"),
        al.StateVariable('B', dimension="current"),
    ],
    analog_ports=[al.SendPort("Isyn", dimension="current"),
                  al.SendPort("A", dimension="current"),
                  al.SendPort("B", dimension="current"),
                  al.RecvPort("q", dimension="current")],
    parameters=[al.Parameter('tau_syn', 'time')]
)


if __name__ == "__main__":
    from nineml.abstraction_layer.dynamics.writers import XMLWriter
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    XMLWriter.write(model, filename)
