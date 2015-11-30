#
# A Docker image for simulating the Brunel (2000) model using NEURON and NineML
#
# To build:
#     docker build -t brunel9ml .
#


FROM neuralensemble/simulation
MAINTAINER andrew.davison@unic.cnrs-gif.fr

RUN sed 's/#force_color_prompt/force_color_prompt/' .bashrc > tmp; mv tmp .bashrc
RUN echo "source /home/docker/env/neurosci/bin/activate" >> .bashrc

USER root
RUN apt-get update; apt-get install -y python-lxml python-pandas
USER docker

# For simulation we require Neo 0.3.3, for analysis we need the development
# version of Neo. We therefore create a second virtualenv for analysis

ENV VENV2=$HOME/env/analysis
RUN virtualenv --system-site-packages $VENV2
RUN $VENV2/bin/pip install -U numpy parameters quantities  # need numpy >= 1.9
RUN wget https://github.com/NeuralEnsemble/python-neo/archive/apibreak.tar.gz -O $HOME/packages/neo_apibreak.tar.gz
RUN $VENV2/bin/pip install $HOME/packages/neo_apibreak.tar.gz
RUN $VENV2/bin/pip install elephant

# Install NineML libraries

WORKDIR $HOME/packages
RUN echo "change this text to ensure we skip the cache"; git clone https://github.com/INCF/lib9ML.git
RUN git clone https://bitbucket.org/apdavison/ninemlcodegen.git
RUN git clone https://github.com/apdavison/PyNN.git
RUN $VENV/bin/pip install ./lib9ML
RUN $VENV/bin/pip install ./ninemlcodegen/nmodl
RUN cd ./PyNN; git checkout nineml; $VENV/bin/pip install .
RUN $VENV/bin/pip install sarge

# Install  the 9ML toolkit
RUN wget http://code.call-cc.org/releases/4.10.0/chicken-4.10.0.tar.gz
RUN tar zxf chicken-4.10.0.tar.gz; cd chicken-4.10.0; make PLATFORM=linux PREFIX=$HOME/chicken install
RUN $HOME/chicken/bin/chicken-install 9ML-toolkit
RUN wget http://downloads.sourceforge.net/project/mlton/mlton/20130715/mlton-20130715-1.amd64-linux.tgz?use_mirror=heanet -O mlton-20130715-1.amd64-linux.tgz
RUN tar xzf mlton-20130715-1.amd64-linux.tgz; mv usr/lib/mlton $VENV/lib; mv usr/bin/* $VENV/bin


RUN mkdir /home/docker/projects
