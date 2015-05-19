"""


"""

import numpy as np
from neo import AnalogSignal
from quantities import ms, dimensionless


def instantaneous_firing_rate(segment, begin, end):
    """Computed in bins of 0.1 ms """
    bins = np.arange(begin, end, 0.1)
    hist, _ = np.histogram(segment.spiketrains[0].time_slice(begin, end), bins)
    for st in segment.spiketrains[1:]:
        h, _ = np.histogram(st.time_slice(begin, end), bins)
        hist += h
    return AnalogSignal(hist, sampling_period=0.1*ms, units=dimensionless,
                        channel_index=0, name="Spike count")
