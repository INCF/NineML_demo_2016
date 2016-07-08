"""
Run a parameter sweep for the Brunel (2000) model

Usage: sweep.py [-h] implementation

positional arguments:
  implementation  the implementation to use ('nineml', 'nest', 'pyNN.nest' or
                  'pyNN.neuron'

optional arguments:
  -h, --help      show this help message and exit
"""

import os
from datetime import datetime
from uuid import uuid1
import argparse
import yaml
import numpy as np
from sarge import run

parser = argparse.ArgumentParser()
parser.add_argument("implementation",
                    help="the implementation to use ('nineml', 'nest', 'pyNN.nest' or 'pyNN.neuron'")
parser.add_argument("parameter_file",
                    help="baseline parameter file for this experiment")
config = parser.parse_args()

implementation = config.implementation

timestamp = datetime.now()
results_dir = "results/{:%Y%m%d-%H%M%S}".format(timestamp)
os.mkdir(results_dir)

with open(config.parameter_file) as fp:
    parameters = yaml.load(fp)
parameters["experiment"].pop("base_filename")

#n_jobs = 1
#jobs = []

with open(os.path.join(results_dir, "sweeps.csv"), "w") as sweep_fp:
    #for g in np.arange(0, 9, 0.5):
    for g in np.arange(1.5, 9, 0.5):
        for eta in np.arange(0, 5, 0.25):
            id = str(uuid1())[:8]
            parameters["network"]["g"] = float(g)   # yaml treats numpy floats differently
            parameters["network"]["eta"] = float(eta)
            output_file = os.path.join(results_dir,
                                       "brunel_network_alpha_{}_{}.h5".format(implementation, id))
            parameters["experiment"]["full_filename"] = output_file
            parameter_file = "{}/parameters_{}.yml".format(results_dir, id)
            with open(parameter_file, "w") as fp:
                yaml.dump(parameters, fp)

            sweep_fp.write("{} {} {}\n".format(g, eta, output_file))
            sweep_fp.flush()  # flush file buffers in case a later iteration crashes

            command = "python run_brunel_network_alpha.py {} {}".format(implementation, parameter_file)
            #command = "echo '{} {}'".format(g, eta)

            print(command)
            run(command)
            #jobs.append(
            #    run(command, async=True))
            #if len(jobs) == n_jobs:
            #    for job in jobs:
            #        job.close()
            #    jobs = []
