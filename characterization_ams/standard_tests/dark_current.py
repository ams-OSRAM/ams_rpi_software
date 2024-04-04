import numpy as np
import pandas as pd
from typing import Mapping, Union, Optional
from characterization_ams.stats_engine import pixelwise_stats as ps
from characterization_ams.stats_engine import stats
from characterization_ams.utilities import utilities
from characterization_ams.utilities import image
from characterization_ams.kpi_calcs import calculations as kpi_calcs


__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2023, AMS Characterization"


def dark_current(images: list,
                 tint: list,
                 meta: pd.DataFrame = pd.DataFrame(),
                 cf: Optional[float] = None,
                 exp_col='exposure',
                 shading_dim=32) -> Mapping[str, pd.DataFrame]:
    """

    Standard Test for dark current, tint must be in ms

    Args:
        images (list | np.ndarray): list of images where element represents an different exposure time
                        or
                       3D array of average images where dim = (tint, rows, cols)
        tint (list | np.array): list of exposure values corresponding to images index
        meta (pd.DataFrame, optional): DataFrame of meta data. Defaults to pd.DataFrame()

    Returns:
        vals (dict): dictionary of results
    """

    print(cf)
    results = dict()
    dark_imgs = []
    summ = pd.DataFrame()
    summ_dsnu = pd.DataFrame()
    temp_dsnu = pd.DataFrame()
    temp_dsnu_list = []
    hist = pd.DataFrame()
    nq = pd.DataFrame()

    # check if we have a list or np.array and make sure images are average
    # TODO: more testing on this logic, seems overkill and a bit wonky
    if isinstance(images, list):
        if images[0].ndim == 3:
            for im in images:
                avg_im = stats.avg_img(im)
                dark_imgs.append(avg_im)
            dark_imgs = np.array(dark_imgs)
        else:
            dark_imgs = np.array(images)
    else:
        dark_imgs = images.copy()

    if isinstance(tint, list):
        tint = np.array(tint)

    # make sure tint and images are in ascending order
    arg_idx = tint.argsort()[::]
    tint = tint[arg_idx]
    dark_imgs = np.array(dark_imgs)[arg_idx]
    images = np.array(images)[arg_idx]

    for im in dark_imgs:
        print(im.mean())

    # get the dark current image, assumes tint is in ms
    dc_im = ps.dark_current(dark_imgs, tint*1e-3)

    # get hist, nq, and stats for dc
    hist = image.histogram(dc_im)
    hist.rename(columns={'Value': 'Value [DN/s]'}, inplace=True)
    nq = image.stats(dc_im)
    nq.rename(columns={'Value': 'Value [DN/s]'}, inplace=True)
    summ = stats.stat_percentiles(dc_im)
    summ.drop(columns=['count'], inplace=True)
    summ.rename(columns={'mean':'dc_mean_DN',
                         'median': 'dc_median_DN',
                         'std': 'dc_std_DN',
                         'min': 'dc_min_DN',
                         'max': 'dc_max_DN',
                         '25%': 'dc_25%_DN',
                         '50%': 'dc_50%_DN',
                         '75%': 'dc_75%_DN'}, inplace=True)

    # get table of dsnu
    for idx, im in enumerate(images):
        if im.ndim == 2:
            dsnu_metrics = stats.noise_metrics(im)
            shading_metrics = \
                kpi_calcs.shading_calc(im, dim=shading_dim)
        else:
            L = im.shape[0]
            ttn_var = stats.total_var_temp(im)
            avg_img = stats.avg_img(im)
            dsnu_metrics = stats.noise_metrics(avg_img, L=L, ttn_var=ttn_var)
            shading_metrics = \
                kpi_calcs.shading_calc(avg_img, dim=shading_dim)
        temp_dsnu = utilities.dict_to_frame(dsnu_metrics) ** 0.5
        temp_dsnu['mean'] = stats.avg_offset(im)
        temp_shading = utilities.dict_to_frame(shading_metrics)
        temp_dsnu = temp_dsnu.join(temp_shading).reset_index(drop=True)
        temp_dsnu[exp_col] = tint[idx]
        temp_dsnu_list.append(temp_dsnu)
    summ_dsnu = pd.concat(temp_dsnu_list).reset_index(drop=True)

    ## these say var but are actually stddev due to sqrt above
    summ_dsnu.rename(columns={'tot_var': 'total_dsnu_DN',
                              'row_var': 'row_dsnu_DN',
                              'col_var': 'col_dsnu_DN',
                              'pix_var': 'pix_dsnu_DN'}, inplace=True)
    summ_dsnu['exposure'] = pd.Series(tint)

    # convert to e- if cf was passed
    if cf is not None:
        hist['Value [e/s]'] = hist['Value [DN/s]'] * cf
        nq['Value [e/s]'] = nq['Value [DN/s]'] * cf

        keysd = utilities.stat_engine_col_rename()
        for val in keysd:
            if val == 'mean' or 'DN' not in val:
                continue
            if val in summ.columns:
                val2 = val.replace('DN', 'e')
                summ[val2] = summ[val] * cf
            if val in summ_dsnu.columns:
                val2 = val.replace('DN', 'e')
                summ_dsnu[val2] = summ_dsnu[val] * cf

    if not meta.empty:
        meta_sub = pd.DataFrame()
        # get meta data for agg results
        for mm in meta.columns:
            if len(meta[mm].unique()) == 1:
                meta_sub[mm] = pd.Series(meta[mm].unique()[0])
        meta_hist = pd.concat([meta_sub] * int(hist.shape[0])).reset_index(drop=True)
        nq_hist = pd.concat([meta_sub] * int(nq.shape[0])).reset_index(drop=True)
        # join to data
        hist = hist.join(meta_hist)
        nq = nq.join(nq_hist)
        #summ = utilities.rename(summ)
        #summ_dsnu = utilities.rename(summ_dsnu)
        #data = utilities.rename(meta)

    results['dc_hist'] = hist
    results['dc_nq'] = nq
    results['summ_dc'] = summ
    results['data'] = meta  # in this case we have all pixel metrics
    results['dc_imgs'] = dc_im
    results['summ_dsnu'] = summ_dsnu

    return results


def activation_energy(images: list,
                      temp_vals: list,
                      meta: pd.DataFrame = pd.DataFrame(),
                      ) -> Mapping[str, pd.DataFrame]:
    """Standard Test for activation energy

    Args:
        images (list): list of images where element represents
                                    a different dark current operating point
        temp_vals (list): list of temperature [K] values
                                corresponding to each element in images
        meta (pd.DataFrame, optional): DataFrame of meta data.
                                      Defaults to pd.DataFrame()

    Returns:
        Mapping[str, pd.DataFrame]: dictionary of results
    """

    results = dict()
    summ = pd.DataFrame()

    ae_im = ps.activation_energy(images, temp_vals)

    ae_im = ae_im[~np.isnan(ae_im)]
    hist = image.histogram(ae_im)
    hist.rename(columns={'Value': 'Activation Energy [eV]'}, inplace=True)
    nq = image.stats(ae_im)
    nq.rename(columns={'Value': 'Activation Energy [eV]'}, inplace=True)

    # doubling temperature
    dc_mean = []
    for im in images:
        dc_mean.append(im.mean())
    d_temp = \
        kpi_calcs.doubling_temp(dc_mean, temp_vals)

    summ['Doubling Temperature [C]'] = pd.Series(d_temp)
    summ['Mean Activation Energy [eV]'] = np.mean(ae_im)
    summ['Median Activation Energy [eV]'] = np.median(ae_im)

    if not meta.empty:
        meta_sub = pd.DataFrame()
        # get meta data for agg results
        for mm in meta.columns:
            if len(meta[mm].unique()) == 1:
                meta_sub[mm] = pd.Series(meta[mm].unique()[0])
        meta_hist = \
            pd.concat([meta_sub] * int(hist.shape[0])).reset_index(drop=True)
        nq_hist = \
            pd.concat([meta_sub] * int(nq.shape[0])).reset_index(drop=True)

        hist = hist.join(meta_hist)
        nq = nq.join(nq_hist)
        summ = summ.join(meta_sub)

    results['ae_hist'] = hist
    results['ae_nq'] = nq
    results['ae_summ'] = summ

    return results
