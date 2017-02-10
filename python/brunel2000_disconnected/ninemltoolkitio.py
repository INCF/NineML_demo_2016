# -*- coding: utf-8 -*-

"""
Module for reading SpikeTrains created by simulations with 9ML-toolkit from Ivan Raikov.

Each line contains a time, followed by the IDs of the neurons that spiked in that time bin, e.g.:

19.300000000000  28 2813 23723
19.310000000000
19.320000000000  2909 6078 7175 7212 23827
19.330000000000  7311
19.340000000000  2522 6673 22881
19.350000000000  9144 6070 4831 434
19.360000000000  1769 4173 5581 5667 8156
19.370000000000  9710 9634 7862 7421 5444 2000 23898

Supported : Read

Author: Andrew Davison

"""

import os
from collections import defaultdict
from glob import glob
import numpy as np
import quantities as pq

from neo.io.baseio import BaseIO
from neo.core import Block, Segment, SpikeTrain, AnalogSignalArray as AnalogSignal  #, ChannelIndex


class NineMLToolkitIO(BaseIO):
    """
    Class for reading SpikeTrains created by simulations with 9ML-toolkit from Ivan Raikov.

    Usage:
        >>> from neo import io
        >>> r = io.NineMLToolkitIO(filename='simulation_data')
        >>> block = r.read()[0]
        >>> print block.segments[0].spiketrains
        [<SpikeTrain(array([ 3.89981604,  4.73258781,  0.608428  ,  4.60246277,  1.23805797,
        ...

    """

    is_readable = True
    is_writable = False
    supported_objects = [Block, Segment, SpikeTrain] #, AnalogSignal, ChannelIndex]
    readable_objects = [Block]
    writeable_objects = []
    has_header = False
    is_streameable = False
    name = "NineMLToolkit"
    extensions = ['dat']
    mode = 'dir'


    def __init__(self, filename=None):
        # note that filename should actually be a directory name
        BaseIO.__init__(self)
        self.filename = filename

    def read_block(self, lazy=False, cascade=True, signal_names=None, signal_units=None):
        block = Block(file_origin=self.filename)
        segment = Segment(name="default")
        block.segments.append(segment)
        segment.block = block

        spike_times = defaultdict(list)
        spike_file = self.filename + ".dat"
        print("SPIKEFILE: {}".format(spike_file))
        if os.path.exists(spike_file):
            print("Loading data from {}".format(spike_file))
            with open(spike_file, 'r') as fp:
                for line in fp:
                    if line[0] != '#':
                        entries = line.strip().split()
                        if len(entries) > 1:
                            time = float(entries[0])
                            for id in entries[1:]:
                                spike_times[id].append(time)
                t_stop = float(entries[0])
            if spike_times:
                min_id = min(map(int, spike_times))
            segment.spiketrains = [SpikeTrain(times, t_stop=t_stop, units="ms",
                                              id=int(id), source_index=int(id) - min_id)
                                   for id, times in spike_times.items()]
        signal_files = glob("{}_state.*.dat".format(self.filename))
        print(signal_files)
        for signal_file in signal_files:
            print("Loading data from {}".format(signal_file))
            population = os.path.basename(signal_file).split(".")[1]
            try:
                data = np.loadtxt(signal_file, delimiter=", ")
            except ValueError:
                print("Couldn't load data from file {}".format(signal_file))
                continue
            t_start = data[0, 1]
            ids = data[:, 0]
            unique_ids = np.unique(ids)
            for column in range(2, data.shape[1]):
                if signal_names is None:
                    signal_name = "signal{}".format(column - 2)
                else:
                    signal_name = signal_names[column - 2]
                if signal_units is None:
                    units = "mV"  # seems like a reasonable default
                else:
                    units = signal_units[column - 2]
                signals_by_id = {}
                for id in unique_ids:
                    times = data[ids==id, 1]
                    unique_times, idx = np.unique(times, return_index=True)  # some time points are represented twice
                    signals_by_id[id] = data[ids==id, column][idx]
                channel_ids = np.array(list(signals_by_id.keys()))
                if len(unique_times) > 1:
                    sampling_period = unique_times[1] - unique_times[0]
                    assert sampling_period != 0.0, sampling_period
                    signal_lengths = np.array([s.size for s in signals_by_id.values()])
                    min_length = signal_lengths.min()
                    if not (signal_lengths == signal_lengths[0]).all():
                        print("Warning: signals have different sizes: min={}, max={}".format(min_length,
                                                                                             signal_lengths.max()))
                        print("Truncating to length {}".format(min_length))
                    signal = AnalogSignal(np.vstack([s[:min_length] for s in signals_by_id.values()]).T,
                                          units=units,
                                          t_start=t_start * pq.ms,
                                          sampling_period=sampling_period*pq.ms,
                                          name=signal_name,
                                          population=population)
                    #signal.channel_index = ChannelIndex(np.arange(signal.shape[1], int),
                    #                                    channel_ids=channel_ids)
                    signal.channel_index = channel_ids
                    segment.analogsignals.append(signal)

        return block


