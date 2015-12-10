"""


"""

from __future__ import division
import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import neo
from quantities import ms, dimensionless


def instantaneous_firing_rate(segment, begin, end):
    """Computed in bins of 0.1 ms """
    bin_width = 0.1
    bins = np.arange(begin, end, bin_width)
    hist, _ = np.histogram(segment.spiketrains[0].time_slice(begin*ms, end*ms)/ms, bins)
    for st in segment.spiketrains[1:]:
        h, _ = np.histogram(st.time_slice(begin*ms, end*ms)/ms, bins)
        hist += h
    hist *= 1000/bin_width/len(segment.spiketrains)
    return neo.AnalogSignal(hist, sampling_period=bin_width*ms, units=dimensionless,
                            channel_index=0, t_start=begin*ms, name="Instantaneous firing rate")


def mean_firing_rate(segment):
    duration = segment.spiketrains[0].t_stop - segment.spiketrains[0].t_start
    n = sum(st.size for st in segment.spiketrains)
    print duration, n, len(segment.spiketrains), n/len(segment.spiketrains)
    return n/len(segment.spiketrains)/duration.rescale('s')


def plot_case(gs, data, t_start=900.0, t_stop=1200.0, title="", yticks=None):
    global j

    gs1 = gridspec.GridSpecFromSubplotSpec(2, 1,
                                           subplot_spec=gs[j//2, j%2],
                                           height_ratios=[4, 1],
                                           hspace=0.3)
    ax1 = plt.subplot(gs1[0])
    ax2 = plt.subplot(gs1[1])

    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_visible(False)
    ax1.set_ylim(-1, 50)
    ax1.set_title(title + " (%.1f) Hz" % mean_firing_rate(data))

    sample = np.arange(len(data.spiketrains))
    np.random.shuffle(sample)
    sample = sample[:50]
    for i, spiketrain in enumerate(np.array(data.spiketrains)[sample]):
        ax1.plot(spiketrain,
                 np.ones_like(spiketrain) * i,
                 'k.', markersize=1.0)

    ifr = instantaneous_firing_rate(data, t_start, t_stop)
    t = ifr.times.rescale(ms)
    ax2.plot(t, ifr, color='0.5', lw=0.001, solid_joinstyle='miter')
    ax2.fill_between(t, 0, ifr, color='0.5', lw=0)

    if yticks:
        ticks = yticks
    else:
	start, stop = ax2.get_ylim()
        stop50 = (stop//50 + 1) * 50
        yres = stop50/5
        ticks = np.arange(0, stop + yres, yres)
    ax2.set_yticks(ticks)

    for ax in (ax1, ax2):
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_xlim(t_start, t_stop)

    ax2.yaxis.set_ticks_position('left')
    ax2.xaxis.set_ticks_position('bottom')

    if j//2 == 1:
        ax2.set_xlabel("Time [ms]")
    if j%2 == 0:
        ax2.set_ylabel("Firing rate [/s]")

    plt.show(block=False)
    fig.canvas.draw()
    j += 1


parser = argparse.ArgumentParser()
parser.add_argument("datafiles", nargs=4,
                    help="Input data files")
parser.add_argument("-o", "--output",
                    help="filename for the figure",
                    default="brunel_network_alpha_combined.png"
                    )
config = parser.parse_args()


plt.rcParams.update({
    'lines.linewidth': 0.01,
    'xtick.labelsize': 'x-small',
    'ytick.labelsize': 'x-small',
    'legend.fontsize': 'x-small',
    'axes.titlesize': 'medium',
    'axes.linewidth': 0.01,
    'font.size': 8,
    'savefig.dpi': 200,
    'interactive': False
})


fig = plt.figure(1, facecolor='white', figsize=(6, 8))
gs = gridspec.GridSpec(2, 2)
#gs.update(hspace=0.5, wspace=0.4)
j = 0


titles = {
    "SR": "A: Synchronous Regular",
    "SIfast": "B: Synchronous Irregular (fast)",
    "AI": "C: Asynchronous Irregular",
    "SIslow": "D: Synchronous Irregular (slow)"
}

time_range = {
    "SR": (500, 600),
    "SIfast": (1000, 1200),
    "AI": (1000, 1200),
    "SIslow": (1000, 1200)
}

firing_rate_ticks = {
    "SR": (0, 1000, 2000, 3000, 4000, 5000, 6000),
    "SIfast": (0, 100, 200, 300, 400),
    "AI": (0, 50, 100, 150, 200),
    "SIslow": (0, 50, 100, 150, 200, 250)
}


def get_case(filename):
    for case in ("SR", "SIfast", "AI", "SIslow"):
        if filename.find(case) > 0:
            return case
    raise Exception("Couldn't determine case")


for data_file in config.datafiles:
    io = neo.io.get_io(data_file)
    data = io.read()[0].segments[0]
    case = get_case(data_file)
    t_start, t_stop = time_range[case]
    plot_case(gs, data, t_start, t_stop, titles[case], yticks=firing_rate_ticks[case])


fig.savefig(config.output)
