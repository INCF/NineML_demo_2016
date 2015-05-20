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

with open(os.path.join(results_dir, "sweeps.csv"), "w") as sweep_fp:
    for g in range(0, 9, 2):
        for eta in range(0, 5):
            id = str(uuid1())[:8]
            parameters["network"]["g"] = g
            parameters["network"]["eta"] = eta
            output_file = os.path.join(results_dir,
                                       "brunel_network_alpha_{}_{}.h5".format(implementation, id))
            parameters["experiment"]["full_filename"] = output_file
            parameter_file = "{}/parameters_{}.yml".format(results_dir, id)
            with open(parameter_file, "w") as fp:
                yaml.dump(parameters, fp)

            command = "python run_brunel_network_alpha.py {} {}".format(implementation, parameter_file)
            print(command)
            run(command)

            sweep_fp.write("{} {} {}\n".format(g, eta, output_file))
            sweep_fp.flush()  # flush file buffers in case a later iteration crashes
