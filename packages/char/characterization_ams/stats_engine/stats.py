import numpy as np
import pandas as pd
from characterization_ams.utilities import utilities as ut
from typing import Union


__author__ = "Denver Lloyd, Dan Chianucci"
__copyright__ = "Copyright 2021, AMS Characterization"


@ut.ensure_img_or_stack
def avg_offset(img_or_stack):
    """
    compute the scalar average of a frame or stack of frames, returns a scalar

    keyword arguments:
        img (np.array): average image to compute mean on

    Returns:
        temp (float): mean of average frame
    """

    return np.mean(img_or_stack)


@ut.ensure_img_stack
def avg_img(img_stack):
    """
    take a stack of images and compute the per pixel average

    Keyword Arguments:
        img_stack (np.array): stack of images

    Returns:
        avg_img (np.array): 2D image of per pixel averages from img_stack
    """
    return np.mean(img_stack, axis=0)


@ut.ensure_img_or_stack
def col_avg(img_or_stack):
    """
    get column average

    average over the row dimension, axis=0 if 2D image,
    or axis=1 if 3D image

    Keyword Arguments:
        img_or_stack (np.array): img or stack of images to
                                 calcuate column average on

    Returns:
        avg (np.array): 1D array of column average values if ingle image
                        2D (NxM) array of column averages if givern a stack
    """

    return np.mean(img_or_stack, axis=-2)


@ut.ensure_img_or_stack
def col_var_cav(img_or_stack, L=1, ttn_var=0, ddof=0,
                rmv_ttn=True, hpf=False, hpf_constant=0.96):
    """
    compute column variance from image with residual temporal noise removed,
    not exact solution

    Keyword Arguments:
        img (np.array): input image (tyically average)
        L (int): number of images used for average
        ttn_var (float): temporal noise from image stack used to get img
        ddof (int, 0): degree of freedom for variance calc
        rmv_ttn (bool, True): if True remove residual temporal noise
        hpf (bool, False): if hpf was applied we correct for noise
                           reduction from hpf (factor of 0.96)
        hpf_constant (float, 0.96): Correction factor for noise reduction
                                    from hpf

    Returns:
        var (float): column variance of img
    """

    var = np.var(col_avg(img_or_stack), axis=0, ddof=ddof)

    if hpf:
        var /= hpf_constant**2

    if rmv_ttn:
        rows = img_or_stack.shape[-2]
        var -= ttn_var/(L*rows)

    return var


def _col_var(rav_var, cav_var, tot_var, img_shape):
    """
    column variance exact solution calculation

    Keyword Arguments:
        rav_var (float): row average variance
        cav_var (float): col average variance
        tot_var (float): total variance
        img_shape (tuple): shape of image var was calculated from

    Returns:
        col_var (float): column variance
    """

    M, N = img_shape
    col_var = ((M*N-M)/(M*N-M-N)*cav_var - (N)/(M*N-M-N)*(tot_var-rav_var))
    return col_var


@ut.ensure_img
def col_var(img, L=1, ttn_var=0, ddof=0):
    """
    compute exact solution of column variance from
    image with residual temporal noise removed,
    EMVA 4.0 definition

    Keyword Arguments:
        img (np.array): input image (tyically average)
        L (int): number of images used for average
        ttn_var (float): temporal noise from average
        ddof (int, 0): degree of freedom for variance calc

    Returns:
        col_var (float): column variance of img
    """

    # row variance
    rav_var = np.mean(row_var_rav(img, L, ttn_var, ddof))

    # column variance
    cav_var = np.mean(col_var_cav(img, L, ttn_var, ddof))

    # total variance
    tot_var = total_var(img, L, ttn_var, ddof)

    return _col_var(rav_var, cav_var, tot_var, img.shape)


@ut.ensure_img_stack
def col_var_temp(img_stack, ddof=1):
    """
    compute exact solution for column temporal
    variance from image stack

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 1): degree of freedom for variance calc

    Returns:
        var (float): column temporal noise variance of img_stack
    """

    cav_var_temp = np.mean(col_var_cav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))

    rav_var_temp = np.mean(row_var_rav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))

    tot_var_temp = np.mean(total_var_temp(img_stack, ddof=ddof))

    return _col_var(rav_var_temp, cav_var_temp,
                    tot_var_temp, img_stack.shape[1:])


@ut.ensure_img_or_stack
def row_avg(img_or_stack):
    """
    get row average

    Keyword Arguments:
        img_or_stack (np.array): img or stack of images to
                                 calcuate row average on

    Returns:
        avg (np.array): 1D array of row average values if given a single image
                        2D (IxR) array of row averages if givern a stack
    """

    return np.mean(img_or_stack, axis=-1)


@ut.ensure_img_or_stack
def row_var_rav(img_or_stack, L=1, ttn_var=0, ddof=0,
                rmv_ttn=True, hpf=False, hpf_constant=0.96):
    """
    compute row variance from image with residual temporal noise removed,
    not exact solution

    Keyword Arguments:
        img (np.array): input image (tyically average)
        L (int): number of images used for average
        ttn_var (float): temporal noise from image stack used to get img
        ddof (int, 0): degree of freedom for variance calc
        rmv_ttn (bool, True): if True remove residual temporal noise
        hpf (bool, False): if hpf was applied we correct for noise
                           reduction from hpf (factor of 0.96)

    Returns:
        var (float): row variance of image
    """
    var = np.var(row_avg(img_or_stack), axis=0, ddof=ddof)

    if hpf:
        var /= hpf_constant**2

    if rmv_ttn:
        cols = img_or_stack.shape[-2]
        var -= ttn_var/(L*cols)

    return var


def _row_var(rav_var, cav_var, tot_var, img_shape):
    """
    row variance exact solution

    Keyword Arguments:
        rav_var (float): row average variance
        cav_var (float): col average variance
        tot_var (float): total variance
        img_shape (tuple): shape of image var was calculated from

    Returns:
        row_var (float): row variance
    """

    M, N = img_shape

    row_var = ((M*N-N)/(M*N-M-N)*rav_var -
               (M)/(M*N-M-N)*(tot_var-cav_var))

    return row_var


@ut.ensure_img
def row_var(img, L=1, ttn_var=0, ddof=0):
    """
    compute exact solution of row variance from
    image with residual temporal noise removed,
    EMVA 4.0 definition

    Keyword Arguments:
        img (np.array): input image (tyically average)
        L (int): number of images used for average
        ttn_var (float): temporal noise from average
        ddof (int, 0): degree of freedom for variance calc

    Returns:
        var (float): row variance of img
    """

    # column variance
    cav_var = np.mean(col_var_cav(img, L, ttn_var, ddof))

    # row variance
    rav_var = np.mean(row_var_rav(img, L, ttn_var, ddof))

    # total variance
    tot_var = total_var(img, L, ttn_var, ddof)

    return _row_var(rav_var, cav_var, tot_var, img.shape)


@ut.ensure_img_stack
def row_var_temp(img_stack, ddof=1):
    """
    compute exact solution for row temporal
    variance from image stack

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 0): degree of freedom for variance calc

    Returns:
        var (float): row temporal noise variance
    """

    # column temporal noise variance
    cav_var_temp = np.mean(col_var_cav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))

    # row temporal noise variance
    rav_var_temp = np.mean(row_var_rav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))

    # total temporal noise variance
    tot_var_temp = np.mean(total_var_temp(img_stack, ddof=ddof))

    return _row_var(rav_var_temp, cav_var_temp,
                    tot_var_temp, img_stack.shape[1:])


def _pix_var(rav_var, cav_var, tot_var, img_shape):
    """
    pixel variance exact solution

    Keyword Arguments:
        rav_var (float): row average variance
        cav_var (float): col average variance
        tot_var (float): total variance
        img_shape (tuple): shape of image var was calculated from

    Returns:
        row_var (float): row variance
    """

    M, N = img_shape

    pix_var = ((M*N)/(M*N-M-N))*(tot_var - cav_var - rav_var)

    return pix_var


@ut.ensure_img
def pix_var(img, L=1, ttn_var=0, ddof=0):
    """
    compute exact solution of pixel variance from
    image with residual temporal noise removed,
    EMVA 4.0 definition

    Keyword Arguments:
        img (np.array): input image (tyically average)
        L (int): number of images used for average
        ttn_var (float): temporal noise from average
        ddof (int, 0): degree of freedom for variance calc

    Returns:
        var (float): pix variance of img
    """

    # row variance
    rav_var = row_var_rav(img, L, ttn_var, ddof)

    # col variance
    cav_var = np.mean(col_var_cav(img, L, ttn_var, ddof))

    # total variance
    tot_var = total_var(img, L, ttn_var, ddof)

    return _pix_var(rav_var, cav_var, tot_var, img.shape)


@ut.ensure_img_stack
def pix_var_temp(img_stack, ddof=1):
    """
    compute exact solution for pixel temporal
    variance from image stack

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 0): degree of freedom for variance calc

    Returns:
        var (float): pixel temporal noise variance
    """

    # column temporal variance
    cav_var_temp = np.mean(col_var_cav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))

    # row temporal variance
    rav_var_temp = np.mean(row_var_rav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))

    # total temporal variance
    tot_var_temp = total_var_temp(img_stack, ddof=ddof)

    return _pix_var(rav_var_temp, cav_var_temp,
                    tot_var_temp, img_stack.shape[1:])


@ut.ensure_img
def total_var(img, L=1, ttn_var=0, ddof=0, rmv_ttn=True,
              hpf=False, hpf_constant=0.96):
    """
    compute total variance from image with
    residual temporal noise removed

    Keyword Arguments:
        img (np.array): input image (tyically average)
        L (int): number of images used for average
        ttn_var (float): temporal noise from image stack used to get img
        ddof (int, 0): degree of freedom for variance calc
        rmv_ttn (bool, True): if True remove residual temporal noise
        hpf (bool, False): if hpf was applied we correct for noise
                           reduction from hpf (factor of 0.96)

    Returns:
        var (float): total variance of img
    """

    var = np.var(img,  ddof=ddof)

    if hpf:
        var /= hpf_constant**2

    # remove residual temporal noise
    if rmv_ttn:
        var -= ttn_var / L

    return var


@ut.ensure_img_stack
def total_var_temp(img_stack, ddof=1):
    """
    compute total temporal variance from a stack of images

    Keyword Arguments:
        img_stack (np.array): stack of images

        ddof (int, 1): degree of freedom for variance calc

    Returns:
        var (float): total temporal variance of img
    """

    return avg_offset(tot_var_img_stack(img_stack, ddof))


@ut.ensure_img_stack
def tot_var_img_stack(img_stack, ddof=1):
    """
    take a stack of images and compute
    the per pixel variance (total temporal noise)

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 1): degree of freedom for variance calc

    Returns:
        var_im -- 2D image of pix temporal noise values
    """

    return np.var(img_stack, axis=0, ddof=ddof)


@ut.ensure_img
def noise_metrics(img, L=1, ttn_var=0, ddof=0, dim=5, rmv_ttn=True, hpf=False):
    """
    compute spatial noise metrics from an average
    image with residual temporal noise removed

    Keyword Arguments:
        img (np.array): input image (tyically average)
        L (int): number of images used for average
        ttn_var (float): temporal noise from image stack used to get img
        ddof (int, 0): degree of freedom for variance calc
        rmv_ttn (bool, True): if True remove residual temporal noise
        hpf (bool, False): if hpf was applied we correct for noise
                           reduction from hpf (factor of 0.96)

    Returns:
        var (dict): row_var
                    col_var
                    pix_var
                    tot_var
    """
    if hpf:
        img = ut.high_pass_filter(img, dim) / dim**2

    cav_var = np.mean(col_var_cav(img, L, ttn_var, ddof, rmv_ttn, hpf))
    rav_var = np.mean(row_var_rav(img, L, ttn_var, ddof, rmv_ttn, hpf))
    tot_var = total_var(img, L, ttn_var, ddof, rmv_ttn, hpf)
    row_var = _row_var(rav_var, cav_var, tot_var, img.shape)
    col_var = _col_var(rav_var, cav_var, tot_var, img.shape)
    pix_var = _pix_var(rav_var, cav_var, tot_var, img.shape)

    var = {
        'tot_var': tot_var,
        'col_var': col_var,
        'row_var': row_var,
        'pix_var': pix_var
    }

    return var


@ut.ensure_img_stack
def noise_metrics_temp(img_stack, ddof=1):
    """
    compute temporal noise metrics from a stack of images

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 0): degree of freedom for variance calc

    Returns:
        var (dict): row_var_temp
                    col_var_temp
                    pix_var_temp
                    tot_var_temp
    """

    cav_var_temp = np.mean(col_var_cav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))
    rav_var_temp = np.mean(row_var_rav(img_stack, ddof=ddof, rmv_ttn=0, hpf=0))
    tot_var_temp = total_var_temp(img_stack, ddof=ddof)
    row_var_temp = _row_var(rav_var_temp, cav_var_temp,
                            tot_var_temp, img_stack.shape[1:])
    col_var_temp = _col_var(rav_var_temp, cav_var_temp,
                            tot_var_temp, img_stack.shape[1:])
    pix_var_temp = _pix_var(rav_var_temp, cav_var_temp,
                            tot_var_temp, img_stack.shape[1:])

    var = {
        'tot_var_temp': tot_var_temp,
        'col_var_temp': col_var_temp,
        'row_var_temp': row_var_temp,
        'pix_var_temp': pix_var_temp
    }

    return var


@ut.ensure_img_stack
def noise_metrics_all(img_stack, ddof=0, ddof_temp=1,
                      dim=5, rmv_ttn=True, hpf=False):
    """
    compute spatial and temporal noise metrics from a stack
    of images

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 0): degree of freedom for variance calc
        ddof_temp (int, 0): degree of freedom for temporal variance calc
        rmv_ttn (bool, True): if True remove residual temporal noise
        hpf (bool, False): if hpf was applied we correct for noise
                           reduction from hpf (factor of 0.96)

    Returns:
        all_var (dict): row_var
                        col_var
                        pix_var
                        tot_var
                        row_temp_var
                        col_temp_var
                        pix_temp_var
                        tot_temp_var
                        mean
    """

    metrics_temp = noise_metrics_temp(img_stack, ddof_temp)

    mean_image = avg_img(img_stack)

    ttn_var = metrics_temp['tot_var_temp']

    L = img_stack.shape[0]

    metrics_mean = noise_metrics(
        mean_image, L, ttn_var, ddof, dim, rmv_ttn, hpf)

    metrics = {**metrics_temp, **metrics_mean}
    metrics["mean"] = avg_offset(mean_image)

    return metrics


@ut.ensure_img
def profile(img, horizontal=True):
    """
    calculate profiles for an image

    Keyword Arguments:
        img (np.array): image to calculate profiles from
        horizontal (bool): if True horizontal profile is takem, else vertical

    Returns:
        temp (dict): index: index of columns
                     middle: center value of columns
                     mean: mean value of columns
                     max: max value of columns
                     min: min value of columns
    """

    temp = {}

    # if vertical data then transpose image
    if not horizontal:
        img = img.T
        key = 'vertical'
    else:
        key = 'horizontal'

    # calculate profiles
    temp = {f'index_{key}': pd.DataFrame(img).columns,
            f'middle_{key}': img[np.shape(img)[0] // 2, :],
            f'mean_{key}': np.mean(img, axis=0),
            f'max_{key}': np.max(img, axis=0),
            f'min_{key}': np.min(img, axis=0)}

    return temp


@ut.ensure_img_stack
def noise_profile(img_stack, axis='row'):
    """
    take a stack of images and compute the row/column noise profile

    Keyword Arguments:
        img_stack (np.array): stack of images
        axis (str): row or column

    Returns:
        noise_profile (np.array): 1D array of row/column noise values
    """

    ax = 2 if axis == 'row' else 1

    noise_profile = np.std(np.mean(img_stack, axis=ax), axis=0, ddof=1)

    return noise_profile


@ut.ensure_img_stack
def fpn_profile(img_stack, axis='row'):
    """
    take a stack of images and compute the row/column fpn profile

    Keyword Arguments:
        img_stack (np.array): stack of images
        axis (str): row or column

    Returns:
        fpn_profile (np.array): 1D array of row/column fpn values
    """

    ax = 1 if axis == "row" else 0

    fpn_profile = np.std(avg_img(img_stack), axis=ax, ddof=1)

    return fpn_profile


def noise_ratios_raw(metrics):
    """
    calculate noise ratios from 'metrics' returned by stats.noise_metrics_all
    Arguments:
        metrics (dict): dictionary with the following keys and values:
                          mean
                          tot_var
                          pix_var
                          col_var
                          row_var
                          tot_var_temp
                          pix_var_temp
                          col_var_temp
                          row_var_temp
    Returns:
        ratios(dict): DataFrame of the following noise ratios:
                              CFPN Ratio
                              CTN Ratio
                              RFPN Ratio
                              RTN Ratio
                              STN Ratio
                              Pix FPN [%]
                              Tot FPN [%]
                              Col FPN [%]
                              Row FPN [%]
    """

    # add spatial noise ratios, only calc if variance isn't 0 (saturated)
    ratios = {"cfpn_ratio": np.nan,
              "rfpn_ratio": np.nan,
              "stn_ratio": np.nan,
              "ctn_ratio": np.nan,
              "rtn_ratio": np.nan,
              "tot_fpn_%": np.nan,
              "pix_fpn_%": np.nan,
              "col_fpn_%": np.nan,
              "row_fpn_%": np.nan}

    if metrics['tot_var'] and metrics['tot_var_temp']:
        ratios['cfpn_ratio'] = np.sqrt(metrics['tot_var_temp'] /
                                       metrics['col_var'])
        ratios['rfpn_ratio'] = np.sqrt(metrics['tot_var_temp'] /
                                       metrics['row_var'])
        ratios['stn_ratio'] = np.sqrt(metrics['tot_var'] /
                                      metrics['tot_var_temp'])

    # check that we have component wise temporal noise
    if 'col_var_temp' in metrics:
        ratios['ctn_ratio'] = np.sqrt(metrics['tot_var_temp'] /
                                      metrics['col_var_temp'])
    if 'row_var_temp' in metrics:
        ratios['rtn_ratio'] = np.sqrt(metrics['tot_var_temp'] /
                                      metrics['row_var_temp'])

    ratios['tot_fpn_%'] = np.sqrt(metrics['tot_var'])/metrics['mean']*100
    ratios['pix_fpn_%'] = np.sqrt(metrics['pix_var'])/metrics['mean']*100
    ratios['col_fpn_%'] = np.sqrt(metrics['col_var'])/metrics['mean']*100
    ratios['row_fpn_%'] = np.sqrt(metrics['row_var'])/metrics['mean']*100

    return ratios


def noise_ratios(metrics):
    """
    wrapper for noise_ratios_raw to return in df
    format

    Arguments:
        metrics (dict): dictionary with the following keys and values:
                          mean
                          tot_var
                          pix_var
                          col_var
                          row_var
                          tot_var_temp
                          pix_var_temp
                          col_var_temp
                          row_var_temp
    Returns:
        ratios(dict): DataFrame of the following noise ratios:
                              CFPN Ratio
                              CTN Ratio
                              RFPN Ratio
                              RTN Ratio
                              STN Ratio
                              Pix FPN [%]
                              Tot FPN [%]
                              Col FPN [%]
                              Row FPN [%]

    """

    df = pd.DataFrame()

    ratios = noise_ratios_raw(metrics)

    df = ut.dict_to_frame(ratios)

    # renmae columns
    df = ut.rename(df)

    return round(df, 3)


@ut.ensure_img_stack
def agg_results_raw(img_stack, ddof=0):
    """
    get standard deviation for all fpn and temporal noise components

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 0) degree of freedom for variance calc
    Returns:
        stats (dict) dataframe of summary stats
    """

    # get mean row, col, pix, and total standard deviation
    var_noise = noise_metrics_all(img_stack, ddof=ddof)
    ratios = noise_ratios_raw(var_noise)

    # add result to df and compute std
    data = {}
    data['tot_std'] = np.sqrt(var_noise['tot_var'])
    data['pix_std'] = np.sqrt(var_noise['pix_var'])
    data['col_std'] = np.sqrt(var_noise['col_var'])
    data['row_std'] = np.sqrt(var_noise['row_var'])
    data['tot_std_temp'] = np.sqrt(var_noise['tot_var_temp'])
    data['pix_std_temp'] = np.sqrt(var_noise['pix_var_temp'])
    data['col_std_temp'] = np.sqrt(var_noise['col_var_temp'])
    data['row_std_temp'] = np.sqrt(var_noise['row_var_temp'])

    data.update(ratios)
    data.update(var_noise)

    return data

@ut.ensure_img_or_stack
def stat_percentiles(img: Union[np.array, np.ndarray]):
    """Calculate percentiles and mean, min, max, mode, median

    Args:
        img (np.array | np.ndarray): image to calcualte stats on

    Returns:
        data (pd.DataFrame): dataframe of results
    """

    data = pd.DataFrame()
    data = pd.DataFrame(np.array(img).flatten()).describe().T
    data['median'] = np.median(img)

    return data

@ut.ensure_img
def agg_results_spatial_raw(img, ddof=0, L=1, ttn_var=0):
    """
    get standard deviation for all fpn noise sources

    Keyword Arguments:
        img (np.array): single average image
        ddof (int, 0) degree of freedom for variance calc
        L (int, 1): size of image stack
        ttn_var (float, 0): total temporal variance from image stack
                            default is 0 so if not passed no residual
                            temporal noise is removed
    Returns:
        stats (dict) dataframe of summary metrics
    """

    # get mean row, col, pix, and total standard deviation
    var_noise = noise_metrics(img, ddof=ddof)
    var_noise['mean'] = avg_offset(img)
    var_noise['tot_var_temp'] = np.nan
    ratios = noise_ratios_raw(var_noise)

    # add result to df and compute std
    data = {}
    data['tot_std'] = np.sqrt(var_noise['tot_var'])
    data['pix_std'] = np.sqrt(var_noise['pix_var'])
    data['col_std'] = np.sqrt(var_noise['col_var'])
    data['row_std'] = np.sqrt(var_noise['row_var'])
    if ttn_var:
        data['tot_std_temp'] = np.sqrt(var_noise['tot_var_temp'])

    data['pix_std_temp'] = np.nan
    data['col_std_temp'] = np.nan
    data['row_std_temp'] = np.nan

    data.update(ratios)
    data.update(var_noise)

    return data


@ut.ensure_img_stack
def agg_results(img_stack, ddof=0, rename=False, include_var=True):
    """
    get standard deviation and variancefor all
    fpn and temporal noise components

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 0) degree of freedom for variance calc
        rename (bool, False): rename the column names for plotting

    Returns:
        stats (df) dataframe of summary stats
    """

    df = pd.DataFrame()

    # get dictionary of all values
    raw = agg_results_raw(img_stack, ddof)

    # convert to DataFrame
    df = ut.dict_to_frame(raw)

    # rename columns
    if rename:
        df = ut.rename(df)

    if not include_var:
        df = df[[c for c in df.columns if 'Var' not in c]]

    return round(df, 3)


@ut.ensure_img
def agg_results_spatial(img, ddof=0, rmv_black=True,
                        rename=True, L=1, ttn_var=0,
                        include_var=True):
    """
    get standard deviation and variance for all
    fpn and temporal noise components

    Keyword Arguments:
        img_stack (np.array): stack of images
        ddof (int, 0) degree of freedom for variance calc
        rename (bool, False): rename the column names for plotting
        L (int, 1): size of image stack
        ttn_var (float, 0): total temporal variance from image stack
                            default is 0 so if not passed no residual
                            temporal noise is removed

    Returns:
        stats (df) dataframe of summary stats
    """

    df = pd.DataFrame()

    # get dictionary of all values
    raw = agg_results_spatial_raw(img, ddof, L=L, ttn_var=ttn_var)

    # convert to DataFrame
    df = ut.dict_to_frame(raw)

    # rename columns
    if rename:
        df = ut.rename(df)

    if not include_var:
        df = df[[c for c in df.columns if 'Var' not in c]]

    return round(df, 3)
