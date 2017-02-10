"""
Network model from

    Brunel, N. (2000) J. Comput. Neurosci. 8: 183-208

expressed in NineML using the Python API and then
simulated using the 9ml-toolkit

"""

from __future__ import division
from datetime import datetime
import os, sys
from sarge import run
from brunel_network_nineml import build_model
from ninemltoolkitio import NineMLToolkitIO


def run_simulation(parameters, plot_figure=False):


    # create XML file using Python lib9ml
    timestamp = datetime.now()
    model = build_model(**parameters["network"])
    if "full_filename" in parameters["experiment"]:  # actually a directory name + prefix
        #ext = os.path.splitext(parameters["experiment"]["full_filename"])[1]
        #xml_file = parameters["experiment"]["full_filename"].replace(ext, ".xml")
        xml_file = parameters["experiment"]["full_filename"] + ".xml"
    else:
        xml_file = "{}.xml".format(parameters["experiment"]["base_filename"])
    model.write(xml_file)
    print("Exported model to file {}".format(xml_file))

    # run simulation using 9ML-toolkit
    working_dir = os.path.dirname(xml_file)
    xml_file = os.path.basename(xml_file)
    cmd = "{}/9ML-network -m crk3 {}".format(os.path.dirname(sys.executable),
                                             xml_file)
    print(cmd)
    run(cmd, cwd=working_dir, async=False)

    cmd = './Sim_{} -d {} --timestep={} --spikerecord="All" --statesample=1'.format(
                                                         os.path.splitext(xml_file)[0],
                                                         parameters["experiment"]["duration"],
                                                         parameters["experiment"]["timestep"],
                                                         parameters["experiment"]["n_record"])


    print(cmd)
    run(cmd, cwd=working_dir, async=False)

    if plot_figure:
        io = NineMLToolkitIO(parameters["experiment"]["base_filename"])
        block = io.read()[0]
        data = {"All": block.segments[0]}
    else:
        data = None

    return data
