import os
import re
import struct
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from characterization_ams.utilities import calc
from characterization_ams.utilities import utilities as ut
from characterization_ams.stats_engine import stats as ams_stats
from PIL import Image
import imageio as iio
from pathlib import Path
from typing import Optional


def histogram(img: np.array,
              bin: int =1) -> pd.DataFrame:
    """
    Thin wrapper for numpy.histogram to return as pandas.DataFrame for
    plotting purposes
    """
    max_ = bin * np.ceil(img.max() / bin)
    #max_value = bin * np.ceil(float(im.stack().max()) / bin)

    count, divisions = np.histogram(img,
                                    range=(0, max_),
                                    bins=int(np.ceil(max_ / bin)))

    #return count, divisions
    #divisions += offset
    count = np.append(count, [0])
    #region, region_desc = roi_get(im)
    out = pd.DataFrame({'Value': divisions,
                        'Counts': count})

    # temp['1-CDF'] = calc.cdf(temp['Counts'])

    """
        im = im[dfutils.int_cols(im)]
        max_value = bin * np.ceil(float(im.stack().max()) / bin)
        count, divisions = np.histogram(im.stack(),
                                        range=(-offset, max_value + offset),
                                        bins=int(np.ceil(max_value / bin)+1))
        divisions += offset
        count = np.append(count, [0])
        region, region_desc = roi_get(im)
        temp = pd.DataFrame({'Color': color,
                             'DN': divisions,
                             'Region': region,
                             'RegionDesc': region_desc,
                             'Counts': count})
        temp['1-CDF'] = calc.cdf(temp['Counts'])
        data = pd.concat([data, temp])
    """

    return out


def implot(df,
           clim=['-3s', '3s'],
           oor=('-3.5s', '3.5s'),
           vlim=('min', 'max'),
           slim=(-5.5, 5.5),
           cmap='viridis',
           oormarks=False,
           layout='vertical',
           rectim=None,
           rectsig=None,
           vscale='linear',
           figkwargs: dict = None,
           sigkwargs: dict = None,
           imkwargs: dict = None,
           debug: bool = False,
           **kwargs
           ):
    """
    Render image and normal quantile (cdf) plot

    Args:
       df (pandas.DataFrame|str):  file path (passed to imread)
                                   or DataFrame containing pixel data

    Keyword Args:
        clim (tuple of aggfuns, ('-3s', '3s')): color limits (color scale)
        oor (tuple of aggfuns, ('-3.5s', '3.5s')): out of range limit
                                                  (outlier marking)
        vlim (tuple of aggfuns, ('min', 'max')): value limits (x-axis)
        slim (tuple of aggfuns, (-5.2, 5.2)): sigma limits (y-axis)
        cmap (str, viridis): matplotlib colormap
        oormarks (bool, False): render OOR pixels on image as embiggened marks
        layout (str, 'vertical'): axes vertically oriented else horizontal
        rectim (list of numeric): image rectangle args
        rectsig (list of numeric): sigma normal rectangle args
        figkwargs (dict, None): figure kwargs
        sigkwargs (dict, None): sigma axes kwargs
        imkwargs (dict, None): image axes kwargs

        other *kwargs* passed directly to ``imread``

    Returns
        fig (matplotlib.Figure): figure instance

    """

    figkwargs = {} if figkwargs is None else figkwargs
    sigkwargs = {} if sigkwargs is None else sigkwargs
    imkwargs = {} if imkwargs is None else imkwargs

    figkwargs.setdefault('facecolor', 'w')

    im = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    imflat = pd.Series(im.values.flatten())
    imflat = imflat[imflat.notnull()]
    nq = calc.normal_quantile(imflat)

    oor = calc.limits(oor, imflat)
    clim = calc.limits(clim, imflat)
    vlim = calc.limits(vlim, imflat)
    slim = calc.limits(slim, imflat)

    # oor can't overlap clim
    oor[0] == clim[0] if oor[0] > clim[0] else oor[0]
    oor[1] == clim[1] if oor[1] < clim[1] else oor[1]

    imth, xyl = threshold(im, thresh=oor[0], fun=np.less)
    imtl, xyh = threshold(im, thresh=oor[1], fun=np.greater)

    colors = np.linspace(0, 1, 256)
    colors = np.vstack((colors, colors))

    try:  # this stupidness likely fixed in mpl 2.0
        locol = plt.cm.get_cmap(cmap).colors[0]
        hicol = plt.cm.get_cmap(cmap).colors[-1]

    except Exception:
        hicol = plt.cm.get_cmap(cmap, 2)(1)[:3]
        locol = plt.cm.get_cmap(cmap, 2)(0)[:3]

    fig = plt.figure(**figkwargs)

    if layout == 'vertical':
        rectim = rectim or [0.05, 0.5, 0.9, 0.5]
        rectsig = rectsig or [0.2, 0.1, 0.6, 0.35]

    else:
        rectim = rectim or [0.5, 0.05, 0.4, 0.9]
        rectsig = rectsig or [0.05, 0.15, 0.4, 0.8]

    axs = [fig.add_axes(rectsig, **sigkwargs), fig.add_axes(rectim, **imkwargs)]

    if cmap == 'gray':
        oorcols = ((0., 0., 0.8), (0.8, 0.0, 0.0))
    else:
        oorcols = ((0., 0., 0.), (0.8, 0.0, 0.0))

    oorlkws = dict(marker='s', markersize=3,
                   color=oorcols[0], alpha=1, linestyle=''
                   )
    oorhkws = dict(marker='s', markersize=3, markeredgecolor=oorcols[1],
                   color=oorcols[1], alpha=1, linestyle='')

    if oormarks:
        axs[1].plot(xyl.col, xyl.row, **oorlkws)
        axs[1].plot(xyh.col, xyh.row, **oorhkws)

    axs[1].imshow(im, cmap=cmap, interpolation='none', aspect='equal', clim=clim)
    axs[1].grid(False, which='both', axis='both')
    axs[1].yaxis.tick_right()

    # set some colors and transparency of fills
    alphaim = 0.6
    alphaoor = alphaim

    # render main colorbar with continuous colormap
    axs[0].imshow(colors, aspect='auto', extent=(*clim, *slim),
                  cmap=cmap, alpha=alphaim)

    # render colorbar between bottom of colormap and the "oor" lo limit with the same
    # color as bottom of colormap
    axs[0].fill_between([oor[0], clim[0]], *slim, color=locol, alpha=alphaim, zorder=0)

    # render colorbar between top of colormap and the "oor" high limit with the same
    # color as top of colormap
    axs[0].fill_between([clim[1], oor[1]], *slim, color=hicol, alpha=alphaim, zorder=0)

    # render from the value (x-axis) low limit to the oor low point with the oorlo color
    axs[0].fill_between([vlim[0], oor[0]], *slim, color=oorcols[0], alpha=alphaoor, zorder=0)

    # render from the value (x-axis) high limit to the oor low point with the oorhi color
    axs[0].fill_between([oor[1], vlim[1]], *slim, color=oorcols[1], alpha=alphaoor, zorder=0)

    # sigma normal grid
    vlw = 1
    alphav = 0.8
    axs[0].vlines(oor[0], *slim, lw=vlw,  color='k', linestyle='--', alpha=alphav)
    axs[0].vlines(oor[1], *slim, lw=vlw,  color='k', linestyle='--', alpha=alphav)
    axs[0].vlines(clim[0], *slim, lw=vlw, color='k', linestyle='--',  alpha=alphav)
    axs[0].vlines(clim[1], *slim, lw=vlw, color='k', linestyle='--',  alpha=alphav)

    axs[0].set(xlim=vlim, yticks=np.linspace(-6.0, 6.0, 13),
               ylim=slim, ylabel='$\sigma_{normal}$', xlabel='$DN$',
               facecolor='w')

    #axs[0].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator())  # how to find maj/2?
    axs[0].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.5))

    mgcol = '#cccccc'
    axs[0].grid(True, 'major', axis='both', lw=2,
                color=mgcol, linestyle=':', alpha=1.0)
    #axs[0].grid(True, 'minor', axis='both', lw=0.50, color=np.ones(3), linestyle='-', alpha=0.7)

    axs[0].hlines(0, *vlim, mgcol, lw=5)
    axs[0].plot(nq.X, nq.Sigma, color=0.5 * np.ones(3), lw=4, zorder=1e6)

    axs[0].set_xscale(vscale)

    lims = (f'clim=({clim[0]:0.0f},{clim[1]:0.0f}) '
            f'oor=({oor[0]:0.0f},{oor[1]:0.0f}) '
            f'slim=({slim[0]:0.1f},{slim[1]:0.1f})')
            #f'vlim=({vlim[0]:0.0f},{vlim[1]:0.1f}) '


    fig.text(0.01, 0.00, lims)

    if not mpl.pyplot.isinteractive():
        return fig


def save_stack(img_stack: np.array, path: str, name: str, image_format: ['.npz']):
    """
    save an image stack

    Keyword Arguments:
        img_stack (np.array): image stack to be saved
        name (str): name of image to be saved
        path (str): base path of image
        image_format (dict): The formats to save the stack
    Returns:
        name (str): full path of saved image
    """

    file_name = ""
    name = sanitize_filename(name)
    path.mkdir(parents=True, exist_ok=True)

    if not isinstance(img_stack, type(np.array)):
        img_stack = np.array(img_stack)

    for extension in image_format:
        # To keep the saved file path

        match extension:
            case '.tiff':
                # TIFF does not support arrays, so we iterate
                # and save all images as independent TIFF
                for idx, img in enumerate(img_stack):
                    file_name = str(path) + f"\\{name}_{idx}" + ".tiff"

                    iio.imwrite(file_name, img.astype(np.uint16))
            case '.npz':
                file_name = str(path) + f'\\{name}.npz'

                np.savez(file_name, img_stack)
            case '.pgm':
                raise ValueError(f"PGM extension not supported "
                                 f"imageio does not support 16-bit images")
            case _:
                raise ValueError(f"{extension} image file extension not supported. "
                                 f"Please check Processing->image_format on the YAML.")

    return file_name

def read_stack(path: str):
    """
    load image stack from .npz file
    """

    path = Path(path)

    if not path.exists():
        msg = f'provided path: {path} does not exist!'
        raise FileNotFoundError(msg)

    if path.suffix not in ['.npz']:
        msg = 'filetype must be .npz file!'
        raise ValueError(msg)

    stack = np.load(path)['arr_0']

    return stack


def save_tiff(img: np.array, name: str, path: str, depth: str = 12):
    """
    Save an image as a tiff, this function will scale
    based on bit-depth provided. If you don't want scaling
    set depth to 16

    Keyword Arguments:
        img (np.array): single image to be saved
        name (str): name of image to be saved
        path (str): base path of image
    Returns:
        name (str): full path of saved image
    """
    # TODO:: Use this method on _utils.py
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    # scale for 16bit container
    im_ = img * 2**(16-depth)

    # update image name
    if '.tiff' not in name:
        name += '.tiff'

    path = Path(path / name)

    # save the image
    Image.fromarray(im_).save(path)

    return path


def read_tiff(path, depth=12):
    """
    """
    # read image from tiff
    img = iio.imread(path)

    # scale image
    img = img / 2**(16-depth)

    return img


def float_format(x):
    """
    Preferred default formatting for html display

    Args:
        x (numeric | list of numeric): number or iterable of numbers
            to format as HTML string

    Returns:
        formatted (str | list of str): formatted numeric string or list same
                                       if input is iterable

    """
    def _item(x):
        if isinstance(x, str):
            try:
                float(x)
            except Exception:
                return x
            if re.search('\dE-\d\d$', x, re.IGNORECASE):
                return x

        x = float(x)  # lazy way to handle int, etc ...
        if not np.isfinite(x):
            return ''

        ax = abs(x)
        if x == 0.0:
            return '0'
        if ax < 1e-2 or ax >= 1e6:
            fstr = re.sub('e\+0', 'e', '{:0.2e}'.format(x))
            return re.sub('e\-0', 'e-', fstr)
        if ax < 0.1:
            return '{:0.3f}'.format(x)
        if ax < 1:
            return '{:0.2f}'.format(x)
        if ax < 10:
            if np.mod(ax, 1):
                return '{:0.2f}'.format(x)
            return '{:0.0f}'.format(x)
        if ax < 100:
            if np.mod(ax, 1):
                return '{:0.1f}'.format(x)
            return '{:0.0f}'.format(x)

        return '{:0.0f}'.format(x)

    if hasattr(x, '__iter__') and not isinstance(x, str):
        return [_item(e) for e in x]
    else:
        return _item(x)


def img_stretch(img, depth=12):
    """
    stretch an image to a desired bit depth,
    this is a form of normalization, 2**depth
    is scale factor after normalizing image
    to a range of 0-1

    keyword Arguments:
        img (2D np.array): img to be stretched
        depth (int): bit depth to be stretched to

    Returns:
        stetched (2D np.array): 2D stretched array
    """

    stretched = np.ones((img.shape[0], img.shape[1]))

    stretched = ((img - img.min()) / (img.max() - img.min()))*(2**depth - 1)

    return stretched


def stats(img: np.ndarray,
          meta: Optional[pd.Series] = None,
          aggs: Optional[list] = None,
          sigma: Optional[float] = None,
          tail: float = 3,
          step_tail: float = 0.1,
          step_inner: float = 0.5,
          **kwargs
          ) -> pd.DataFrame:
    """
    Calculate image statistics

    Args:
        img (pandas.Dataframe or np.array): array or DataFrame of image data

    Keyword Args:
        meta (pandas.Series, None): metadata to merge with calculated stats
        aggs (list of aggs|"normal_quantile"): alias for aggregation function
        sigma (numeric, None): min|max sigma value
        tail (numeric, 3): point at which to use the step_tail spacing
        step_tail (numeric, 0.2): tail sigma spacing
        step_inner (numberic, 0.5): intermediate sigma spacing

    Returns:
        data (pandas.DataFrame): calculated quantile data

    .. note:: aggs is passed directly to `calc.aggfuns`_ (see for more details)

    .. note:: need to decompose planes prior to calling if desired

    """

    values = img.flatten()

    if aggs == 'normal_quantile':
        stats = calc.normal_quantile(values).rename(columns={'X': 'Value'})

    else:
        if aggs is None:
            if sigma is None:
                n = len(values)
                sig = abs(calc.ss.norm.ppf(1/n))
                # sigma = np.round(np.trunc(sig * 10) / 10)
                sigma = np.ceil(sig * 1 / step_tail) / (1 / step_tail)

            aggs = np.arange(-sigma, -tail, step_tail).tolist() + \
                   np.arange(-tail, tail, step_inner).tolist() + \
                   np.arange(tail, sigma+1e-9, step_tail).tolist()
            n_decimals = ut.num_decimals(step_tail)
            if n_decimals is not None:
                aggs = np.around(aggs, n_decimals)
            aggs = sorted(list(set(aggs)))

            # get the minimum precision required for nice printing
            n_decimals = 1 if not n_decimals else n_decimals # use at least one
            prec_tail = len(str(step_tail-int(step_tail))[1:].strip('.'))
            prec_inner = len(str(step_inner-int(step_inner))[1:].strip('.'))
            prec_max = prec_tail if prec_tail > prec_inner else prec_inner
            n_decimals = prec_max if prec_max > n_decimals else n_decimals

            fmt_ = '{:0.%df}S' % n_decimals
            aggs = [fmt_.format(s) for s in aggs]
            aggs = [aggs[0]] + \
                   [x for i, x in enumerate(aggs[1:])
                    if x != aggs[i-1]]

        stats = pd.DataFrame(calc.aggfuns(aggs, values,
                             fast_q=True)).reset_index()
        stats.columns = ['Stat', 'Value']

        stats['Sigma'] = stats.Stat.map(calc.aggsigma_to_float)
        try:
            stats.loc[stats.Sigma > 0, 'Stat'] = \
                '+' + stats.loc[stats.Sigma > 0, 'Stat'].map(str)

            stats = stats.sort_values('Sigma')
        except Exception:  # doesn't work with mean, std, etc
            pass

    if meta is not None:
        stats = stats.join(pd.DataFrame(data=[meta] * len(stats),
                                        index=stats.index))

    return stats


def threshold(df, thresh=7000, fun=np.greater):
    """
    Threshold image DataFrame returning only rows/columns with OOR values
    as well as a list of (row, col)

    Args:
       df (pandas.DataFrame):  DataFrame containing pixel data

    Keyword args:
        thresh (numeric): threshold value
        fun (callable): function that accepts a DataFrame, thresh
                        as the first and second parameters

    Returns:
        df (pandas.DataFrame): DataFrame with only OOR values
        rowcol (pandas.DataFrame): DataFrame with row, col columns of
                                   OOR values

    """
    # gt or lt ...
    imt = df[fun(df, thresh)].dropna(how='all').dropna(how='all', axis=1)

    # nice pandas way to get this?
    rc = []
    for irow, row in imt.iterrows():
        rn = row.name
        for k, v in row.items():
            if pd.isnull(v):
                continue
            rc += [(rn, k)]

    rc = list(zip(*rc))

    if len(rc) == 0:
        row_, col_ = [], []
    else:
        row_, col_ = rc[0], rc[1]

    return imt, pd.DataFrame(data={'row': row_, 'col': col_})

def calc_nq(img, meta):

    temp = pd.DataFrame()
    nq = pd.DataFrame()
    # calculate normal quantiles
    if img.ndim == 3:
        avg_ = ams_stats.avg_img(img)
        ttn_ = np.sqrt(ams_stats.tot_var_img_stack(img))
    else:
        avg_ = img
        ttn_ = None
    for idx, im in enumerate([avg_, ttn_]):
        if im is None:
            continue
        temp = stats(im)
        temp['Metric'] = \
            'Mean Signal [DN]' if not idx else 'Total Temp Noise [DN]'
        if temp.shape[0] != meta.shape[0]:
            meta = pd.concat([meta] *
                             int(temp.shape[0])).reset_index(drop=True)
        temp = temp.join(meta)
        nq = pd.concat([nq, temp]).reset_index(drop=True)

    return nq


def calc_hist(img, meta, bin=1):

    temp = pd.DataFrame()
    hist = pd.DataFrame()

    # calculate hist
    if img.ndim == 3:
        avg_ = ams_stats.avg_img(img)
        ttn_ = np.sqrt(ams_stats.tot_var_img_stack(img))
    else:
        avg_ = img
        ttn_ = None
    for idx, im in enumerate([avg_, ttn_]):
        if im is None:
            continue
        temp = histogram(img, bin=bin)

        # TODO: Add the cumulative percentage values
        cumulative = (np.cumsum(temp['Counts'])/img.size)*100
        cumulative = 100 -cumulative
        temp['Cumulative'] = cumulative

        temp['Metric'] = \
            'Mean Signal [DN]' if not idx else 'Total Temp Noise [DN]'
        if temp.shape[0] != meta.shape[0]:
            meta = pd.concat([meta] *
                             int(temp.shape[0])).reset_index(drop=True)
        temp = temp.join(meta)
        hist = pd.concat([hist, temp]).reset_index(drop=True)

    return hist


def sanitize_filename(filename):
    # Remove characters not allowed in filenames
    filename = re.sub(r'[^\w\-\. ]', '_', filename)
    # Remove leading and trailing whitespace
    filename = filename.strip()
    # Replace multiple spaces with a single space
    filename = re.sub(r'\s+', ' ', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename
