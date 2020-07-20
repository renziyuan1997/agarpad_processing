#################### imports ####################
# standard
import sys
import os
import numpy as np
import scipy.sparse as ssp
import yaml
import argparse
import shutil
#from PIL import Image
import tifffile as ti
import cv2
import matplotlib.pyplot as plt
import matplotlib.gridspec as mgs
import matplotlib.ticker

# custom
origin=os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(origin,'..','image_processing'))
from utils import *

#################### global params ####################
# yaml formats
npfloat_representer = lambda dumper,value: dumper.represent_float(float(value))
nparray_representer = lambda dumper,value: dumper.represent_list(value.tolist())
float_representer = lambda dumper,value: dumper.represent_scalar('tag:yaml.org,2002:float', "{:<.8e}".format(value))
unicode_representer = lambda dumper,value: dumper.represent_unicode(value.encode('utf-8'))
yaml.add_representer(float,float_representer)
yaml.add_representer(np.float_,npfloat_representer)
yaml.add_representer(np.ndarray,nparray_representer)
yaml.add_representer(str,unicode_representer)

# matplotlib controls
plt.rcParams['svg.fonttype'] = 'none'  # to embed fonts in output ('path' is to convert as text as paths)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams['axes.linewidth']=0.5

#################### function ####################
def default_parameters():
    """Generate a default parameter dictionary."""

    print("Loading default parameters")
    params={}
    # filtering - select only a subset
    params['analysis_queen']={}
    mydict = params['analysis_queen']
    mydict['channels'] = [0,1]
    mydict['bins'] = [16, 16, 16]
    mydict['titles'] = ['390 ex', '475 ex', 'QUEEN']
    mydict['colors']=['darkblue', 'darkgreen', 'darkblue']
    mydict['units_dx']=[None, None, None]

    return params

def make_plot_queen(cells, outputdir='.', bins=['auto','auto','auto'], titles=['I1','I2','QUEEN'], channels=[0,1], colors=['darkblue', 'darkgreen', 'darkblue'], units_dx=[None, None, None]):
    """
    Make a plot of the QUEEN signal obtained from the input dictionary of cells.
    """

    # initialization
    ncells = len(cells)
    if ncells == 0:
        raise ValueError("Empty cell dictionary!")
    c1 = channels[0]
    c2 = channels[1]
    I1 = []
    I2 = []
    QUEEN=[]

    # make lists
    keys = list(cells.keys())
    for n in range(ncells):
        key = keys[n]
        cell = cells[key]
        fl = cell['fluorescence']['total']
        bg = cell['fluorescence']['background']
        x = fl[c1]-bg[c1]
        y = fl[c2]-bg[c2]
        z = float(x)/float(y)
        I1.append(x)
        I2.append(y)
        QUEEN.append(z)
        cell['queen_ratio']=z

    I1 = np.array(I1, dtype=np.uint16)
    I2 = np.array(I2, dtype=np.uint16)
    QUEEN = np.array(QUEEN, dtype=np.float_)

    # make plot
    N = len(I1)
    data = [I1, I2, QUEEN]
    mus = [np.mean(d).astype(d.dtype) for d in data]
    meds = [np.median(d).astype(d.dtype) for d in data]
    sigs = [np.std(d).astype(d.dtype) for d in data]
    errs = [s/np.sqrt(N) for s in sigs]
    fmts = ["$\\mu = {mu:,d}$\n$\\sigma = {sig:,d}$\n$N = {N:,d}$\n$\\mathrm{{med}} = {med:,d}$","$\\mu = {mu:,d}$\n$\\sigma = {sig:,d}$\n$N = {N:,d}$\n$\\mathrm{{med}} = {med:,d}$","$\\mu = {mu:.2f}$\n$\\sigma = {sig:.2f}$\n$N = {N:,d}$\n$\\mathrm{{med}} = {med:.2f}$"]

    fig = plt.figure(num=None, facecolor='w', figsize=(3*4,3))
    gs = mgs.GridSpec(1,3)

    ax0 = fig.add_subplot(gs[0,0])
    axes = [ax0]
    for i in range(1,3):
        ax = fig.add_subplot(gs[0,i],sharey=ax0)
        axes.append(ax)

    for i in range(3):
        ax = axes[i]

        # compute histogram
        hist,edges = np.histogram(data[i], bins=bins[i], density=False)

        # plot histogram
        color = colors[i]
        ax.bar(edges[:-1], hist, np.diff(edges), facecolor=color, lw=0)

        # add legends
        ax.set_title(titles[i], fontsize='large')
        ax.annotate(fmts[i].format(mu=mus[i],sig=sigs[i], N=len(data[i]), med=meds[i]), xy=(0.70,0.98), xycoords='axes fraction', ha='left', va='top')

        # adjust the axis
        if (i==0):
            ax.set_ylabel("count",fontsize="medium",labelpad=10)
            ax.tick_params(length=4)
            ax.tick_params(axis='both', labelsize='medium')
        else:
            ax.tick_params(axis='both', labelsize='medium', labelleft='off')

        if not (units_dx[i] is None):
            ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(base=units_dx[i]))
#        ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(base=0.1))
#        ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(base=0.5))
#        ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(base=0.1))

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

#        ax.set_xlim(xmin,xmax)
#        ax.set_ylim(xmin,xmax)
#        ax.set_aspect(aspect='equal', adjustable='box')

    gs.tight_layout(fig, w_pad=1.0)
    filename = 'analysis_queen'
    exts=['.pdf', '.svg', '.png']
    for ext in exts:
        fileout = os.path.join(outputdir,filename+ext)
        fig.savefig(fileout, bbox_inches='tight', pad_inches=0)
        print("Fileout: {:<s}".format(fileout))
    return

#################### main ####################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Analysis tool -- QUEEN indicator.")
    parser.add_argument('cellfile',  type=str, help='Path to a cell dictionary in json format.')
    parser.add_argument('-f', '--paramfile',  type=file, required=False, help='Yaml file containing parameters.')
    parser.add_argument('-d', '--outputdir',  type=str, required=False, help='Output directory')
    parser.add_argument('--debug',  action='store_true', required=False, help='Enable debug mode')

    # INITIALIZATION
    # load arguments
    namespace = parser.parse_args(sys.argv[1:])

    # input cell file
    cellfile = os.path.realpath(namespace.cellfile)
    if not os.path.isfile(cellfile):
        raise ValueError("Cell file does not exist! {:<s}".format(cellfile))

    cells = load_json2dict(cellfile)
    ncells = len(cells)
    print("ncells = {:d}".format(ncells))

    # output directory
    outputdir = namespace.outputdir
    if (outputdir is None):
        outputdir = os.path.dirname(cellfile)
    else:
        outputdir = os.path.relpath(outputdir, os.getcwd())
    rootdir = os.path.join(outputdir,'analysis')
    outputdir = os.path.join(rootdir,'queen')
    if not os.path.isdir(outputdir):
        os.makedirs(outputdir)
    print("{:<20s}{:<s}".format("outputdir", outputdir))

    # parameter file
    if namespace.paramfile is None:
        allparams = default_parameters()
        paramfile = "analysis_queen.yml"
        with open(paramfile,'w') as fout:
            yaml.dump(allparams,fout)
    else:
        paramfile = namespace.paramfile.name
        allparams = yaml.load(namespace.paramfile)

    dest = os.path.join(outputdir, os.path.basename(paramfile))
    if (os.path.realpath(dest) != os.path.realpath(paramfile)):
        shutil.copy(paramfile,dest)
    paramfile = dest

    # make queen analysis
    make_plot_queen(cells, outputdir=outputdir, **allparams['analysis_queen'])

