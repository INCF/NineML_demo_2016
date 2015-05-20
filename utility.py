"""


"""

import nest
from datetime import datetime
import numpy as np
from numpy import exp
from quantities import ms
import neo


def psp_height(tau_m, R_m, tau_syn):
    """
    Calculate the height of the EPSP for a synaptic current with
    peak amplitude 1 nA.

    tau_m and tau_syn: ms
    R_m: Mohm
    """
    a = (tau_m / tau_syn)
    b = (1.0 / tau_syn - 1.0 / tau_m)
    # time of maximum
    t_max = 1.0/b * (-nest.sli_func('LambertWm1', -exp(-1.0/a)/a) - 1.0/a)
    # height of PSP for current of amplitude 1 nA
    return 1/(tau_syn*tau_m*b/R_m) * ((exp(-t_max/tau_m) - exp(-t_max/tau_syn)) / b - t_max*exp(-t_max/tau_syn))


def segment_from_recording_device(devices, variables_to_include, id_lists, t_stop, name="segment00"):

    def get_data(device, variable, id_list):
        events = nest.GetStatus(device, 'events')[0]
        ids = events['senders']
        values = events[variable]
        data = {}
        for id in id_list:
            data[id] = values[ids==id]
        assert len(data) > 0
        return data

    segment = neo.Segment(name=name, rec_datetime=datetime.now())

    for device, variable, id_list in zip(devices, variables_to_include, id_lists):
        print(name, device, variable)
        data = get_data(device, variable, id_list)
        if variable == 'times':
            print("  adding spiketrain")
            id0 = min(id_list)
            segment.spiketrains = [
                neo.SpikeTrain(spiketrain,
                               t_start=0.0,
                               t_stop=t_stop,
                               units='ms',
                               source_id=id,
                               source_index=id - id0)
                for id, spiketrain in data.items()]
        else:
            print("  adding signal")
            source_ids = np.array(id_list)
            channel_indices = source_ids - source_ids.min()
            signal_array = np.vstack(data.values()).T
            segment.analogsignalarrays = [
                neo.AnalogSignalArray(
                    signal_array,
                    units='mV',
                    t_start=0.0*ms,
                    sampling_period=0.1*ms,
                    name=variable,
                    channel_index=channel_indices,
                    source_ids=source_ids)]
    return segment
