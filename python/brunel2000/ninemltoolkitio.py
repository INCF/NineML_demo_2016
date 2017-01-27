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
import numpy as np
import quantities as pq

from neo.io.baseio import BaseIO
from neo.core import Block, Segment, SpikeTrain


class NineMLToolkitIO(BaseIO):
    """
    Class for reading SpikeTrains created by simulations with 9ML-toolkit from Ivan Raikov.

    Usage:
        >>> from neo import io
        >>> r = io.NineMLToolkitIO(filename = 'simulation_data.dat')
        >>> block = r.read()[0]
        >>> print block.segments[0].spiketrains
        [<SpikeTrain(array([ 3.89981604,  4.73258781,  0.608428  ,  4.60246277,  1.23805797,
        ...

    """

    is_readable = True
    is_writable = False
    supported_objects = [Block, Segment, SpikeTrain]
    readable_objects = [Block]
    writeable_objects = []
    has_header = False
    is_streameable = False
    name = "NineMLToolkit"
    extensions = ['dat']
    mode = 'file'


    def __init__(self, filename=None) :
        BaseIO.__init__(self)
        self.filename = filename

    def read_block(self, lazy=False, cascade=True):
        spike_times = defaultdict(list)
        with open(self.filename, 'r') as fp:
            for line in fp:
                if line[0] != '#':
                    entries = line.strip().split()
                    if len(entries) > 1:
                        time = float(entries[0])
                        for id in entries[1:]:
                            spike_times[id].append(time)
            t_stop = float(entries[0])
        block = Block(file_origin=self.filename)
        segment = Segment(name="default")
        block.segments.append(segment)
        segment.block = block
        segment.spiketrains = [SpikeTrain(times, t_stop=t_stop, units="ms", id=int(id))
                               for id, times in spike_times.items()]
        return block


