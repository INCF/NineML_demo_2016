# encoding: utf-8
"""
Calculate spike train statistics over multiple runs with different random seeds,
 for the Brunel (2000) model

"""

from __future__ import division, print_function
import os
import argparse
import numpy as np
import pandas
from joblib import Parallel, delayed
import neo.io
from ninemltoolkitio import NineMLToolkitIO
from analysis import spike_statistics


parser = argparse.ArgumentParser()
parser.add_argument("directory",
                    help="directory containing data generated by running sweep.py")
parser.add_argument("--io", help="name of Neo IO class to use for reading data")
config = parser.parse_args()

results_dir = config.directory

statistics_file = os.path.join(results_dir, "statistics.csv")

if config.io:
    if config.io == "NineMLToolkitIO":
        ioclass = NineMLToolkitIO
    else:
        ioclass = getattr(neo.io, config.io)
else:
    ioclass = None

if os.path.exists(statistics_file):
    # read the previously calculated spike train statistics from file
    data = pandas.read_csv(statistics_file,
                           delim_whitespace=True)
else:
    # for each data file, read the spike trains and calculate the metrics
    data = pandas.read_csv(os.path.join(results_dir, "sweeps.csv"),
                           names=("seed", "output_file"),
                           delim_whitespace=True, comment="#")

    for idx, row in data.iterrows():
        results = spike_statistics(idx, row, ioclass=ioclass)
        for key, value in results.items():
            data.ix[idx, key] = value

    # results = Parallel(n_jobs=4)(delayed(
    #               spike_statistics)(idx, row) for idx, row in data.iterrows())
    # for idx, result in enumerate(results):
    #     for key, value in result.items():
    #         data.ix[idx, key] = value


    print(data)

    # save statistics to file
    data.to_csv(os.path.join(results_dir, "statistics.csv"),
                sep=" ", index=False)
