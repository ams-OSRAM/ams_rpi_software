import numpy as np
import pandas as pd
from characterization_ams.stats_engine import stats
from characterization_ams.emva import emva
from characterization_ams.utilities import utilities as ut
from characterization_ams.kpi_calcs import calculations as calcs
from typing import Optional, Mapping


__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


def get_stats(images: list,
              df: pd.DataFrame,
              rmv_ttn: bool = True,
              hpf: bool = False,
              rmv_black: bool = True,
              temp_imgs: Optional[list] = None,
              L: Optional[int] = None,
              rename: bool = True,
              shading_dim: int = 32) -> Mapping[str, pd.DataFrame]:
    """
    calculate all statistics per EMVA 4.0 definition

    Keyword Arguments:
        images (list): list of images where each element is array
                       with dim (num_images, width, height)
        df (pd.DataFrame): DataFrame of parameters associated with each image
                           in image stack, right now it is assumed DataFrame
                           index corresponds to indx of images
        rmv_ttn (bool): if True subtract off residual temporal noise
        hpf (bool): if true high pass filter image prior to spatial variance
                    calculation
        rmv_black (bool): if True creates black level subtracted columns +
                          originals
        temp_images (list|None): If 'images' is a list of frame averages then
                                 total temporal variance images must be passed
                                 here
        L (int|None): If average frames are passed to 'images' original stack
                      size must be passed.
    Returns:
        data (pd.DataFrame): DataFrame of all statistics with updated
                             column names and a column with black level
                             subtracted for each metric
    TODO: Add better error handling, try and anticipate different cases
    TODO: Remove the sys.exit with a custom exception
    """
    data = pd.DataFrame()
    results = dict()
    stack = True

    # check if we have an image stack, or avg and temp frame
    if not isinstance(temp_imgs, type(None)):
        stack = False

    if 'Mean Signal [DN]' in data.columns:
        data = ut.rename(data, revert=True)

    if 'Mean Signal [DN]' in df.columns:
        df = ut.rename(df, revert=True)

    # Make sure if average images are used L was also passed
    # TODO: Add better error handling here
    if not stack and isinstance(L, type(None)):
        msg = 'If passing average images L keyword must be provided!'
        raise ValueError(msg)

    # calculate all noise metrics using stats engine
    for idx, im in enumerate(images):

        # case when we have stack of images (all information)
        if stack:
            stat_vals = stats.noise_metrics_all(im,
                                                rmv_ttn=rmv_ttn,
                                                hpf=hpf)

            mean = stats.avg_offset(im)
            tot_var_temp = stat_vals['tot_var_temp']
            shading_vals = \
                calcs.shading_calc(stats.avg_img(im), shading_dim)

        # case where we just have an average frame and
        # temporal variance frame
        else:
            ttn_var = stats.avg_offset(temp_imgs[idx])
            stat_vals = stats.noise_metrics(im, L=L,
                                            ttn_var=ttn_var,
                                            rmv_ttn=rmv_ttn,
                                            hpf=hpf)
            mean = stats.avg_offset(images[idx])
            tot_var_temp = stats.avg_offset(temp_imgs[idx])
            stat_vals['tot_var_temp'] = tot_var_temp
            shading_vals = \
                calcs.shading_calc(images[idx], shading_dim)


        # convert to df
        stat_vals['mean'] = mean
        temp = \
            pd.DataFrame(dict([(k, pd.Series(v)) for
                         k, v in stat_vals.items()]))

        # add noise ratios
        ratios = stats.noise_ratios(stat_vals)
        ratio_cols = ratios.columns.tolist()

        # add shading
        shading = ut.dict_to_frame(shading_vals)
        shading_cols = shading.columns.tolist()

        temp = temp.join(ratios)
        temp = temp.join(shading)
        data = pd.concat([data, temp]).reset_index(drop=True)

    # get data columns
    data = data.sort_values(by='mean').reset_index(drop=True)

    data_cols = data.columns.tolist()
    data_cols = [c for c in data_cols if c not in ratio_cols
                 and c not in shading_cols]

    data_std = data[data_cols]
    data_std = data_std ** 0.5
    cols_std = [c.replace('var', 'std') for c in data_cols]
    cols_std = dict(zip(data_cols, cols_std))
    data_std.rename(columns=cols_std, inplace=True)
    data_std.drop(columns='mean', inplace=True)
    data = data.join(data_std)

    if rmv_black:
        data = ut.remove_black(data, data_cols)
        data_cols = [(c + '_black_subtracted') for c in data_cols]
        data_std = data[data_cols]
        data_std = data_std ** 0.5
        cols_std = [c.replace('var', 'std') for c in data_cols]
        cols_std = dict(zip(data_cols, cols_std))
        data_std.rename(columns=cols_std, inplace=True)
        data_std.drop(columns='mean_black_subtracted', inplace=True)
        data = data.join(data_std)

    # if df of conditions was passed join with data
    if not df.empty:
        overlap_cols = [c for c in data.columns if c in df.columns]
        if any(overlap_cols):
            print(f'overlapping column names exist: {overlap_cols}')
            print('passed overlapping columns will be renamed as:"<col>_pcol"')
            data = data.join(df.reset_index(drop=True),
                             rsuffix='_pcol')
        else:
            data = data.join(df.reset_index(drop=True))

    # get rid of inf values
    data = data.replace(np.inf, 0)

    # rename stats columns
    if rename:
        data = ut.rename(data)

    results['stats'] = data

    return results


@ut.ensure_img_stack_list
def ptc(img_stack_list: list,
        df: pd.DataFrame,
        exp_col: str = 'Exposure [uW/cm^2*s]',
        exp_col_units: str = 'uW/cm^2',
        rmv_ttn: bool = True,
        hpf: bool = False,
        image_idx_col: str = 'Image Index',
        pixel_area: float = None,
        offset_factor: float = 1.0,
        cf: Optional[float] = None,
        shading_dim=32) -> Mapping[str, pd.DataFrame]:
    """
    calculate all PTC metrics using emva functions, but does
    not require QE, pixel pitch, or wl, assumes that first image
    in list of images is dark image. This function takes a list
    of image stacks, calculates temporal noise stats, and wraps
    the ptc_avg function for remaining PTC metrics.

    Keyword Arguments:
        images (list): list of images where each element is array
                       with dim (num_images, width, height)
        df (pd.DataFrame): DataFrame of parameters associated with each image
                           in image stack, right now it is assumed DataFrame
                           index corresponds to indx of images
        exp_col (str): column within df to be used for exposure
                       calculations
        exp_col_units (str): exposure column units to be used
                             for responsivity label
        rmv_ttn (bool): if True subtract off residual temporal noise
        hpf (bool): if true high pass filter image prior to
                    spatial variance calc
        image_idx_col (str): column in df associated with
                             image index in list, if this does not exist in df,
                             it will be created as the frame index

    Returns:
        data (pd.DataFrame): DataFrame of all
                             EMVA response metrics + noise metrics
        hist (pd.DataFrame): DataFrame of all EMVA spatial metrics
        summ (pd.DataFrame): DataFrame of all EMVA summary metrics
    """
    # get statistics and join image data with params
    data = get_stats(images=img_stack_list.copy(),
                     df=df.copy(),
                     rmv_ttn=rmv_ttn,
                     hpf=hpf)['stats']

    # convert image stack to average image
    L = np.shape(img_stack_list[0])[0]
    temp_imgs = []
    avg_imgs = []
    for img_stack in img_stack_list.copy():
        ttn_var = stats.tot_var_img_stack(img_stack)
        avg = stats.avg_img(img_stack)
        temp_imgs.append(ttn_var)
        avg_imgs.append(avg)

    return ptc_avg(img_list=avg_imgs,
                   L=L,
                   df=data,
                   temp_imgs=temp_imgs,
                   exp_col=exp_col,
                   exp_col_units=exp_col_units,
                   rmv_ttn=rmv_ttn,
                   hpf=hpf,
                   image_idx_col=image_idx_col,
                   pixel_area=pixel_area,
                   offset_factor=offset_factor,
                   cf=cf,
                   shading_dim=shading_dim)


@ut.ensure_img_list
def ptc_avg(img_list: list,
            temp_imgs: list,
            L: int,
            df: pd.DataFrame = pd.DataFrame(),
            exp_col: str = 'Exposure [uW/cm^2*s]',
            exp_col_units: str = 'uW/cm^2',
            rmv_ttn: bool = True,
            hpf: bool = False,
            image_idx_col: int = 'Image Index',
            dark_imgs: Optional[np.array] = None,
            pixel_area: float = None,
            offset_factor: float = 1.0,
            cf: Optional[float] = None,
            shading_dim=32) -> Mapping[str, pd.DataFrame]:
    """
    calculate all PTC metrics using emva functions, but does
    not require QE, pixel pitch, or wl. This function will handle
    2 cases:

    1.) all images in 'images' keyword are an average frame
        - L (size of original stack) must be passed
        - temp_imgs (total temporal noise images) must be passed

    2.) all images in 'images' keyword are an average frame AND a stack of
        dark images were passed with keyword 'dark_imgs' for dark temporal
        noise metrics
        - L (size of original stack) must be passed
        - temp_imgs (total temporal noise images) must be passed
        - do not pass average image or total temporal noise image
          for 'dark_img', they will be added in source

    Keyword Arguments:
        images (list): list of images where each element is average array
                       with dim (width, height)
        temp_imgs (list|None): If 'images' are average of image
                               stack then this variable must be used to
                               pass total temporal variance frames, indexes
                               of both lists must align
        L (int): size of original image stack
        df (pd.DataFrame): DataFrame of parameters associated with each image
                           in image stack, right now it is assumed DataFrame
                           index corresponds to indx of images
        exp_col (str): column within df to be used for exposure
                       calculations
        exp_col_units (str): exposure column units to be used
                             for responsivity label
        rmv_ttn (bool): if True subtract off residual temporal noise
        hpf (bool): if true high pass filter image prior to
                    spatial variance calc
        image_idx_col (str): column in df associated with
                             image index in list, if this does not exist in df,
                             it will be created as the frame index
        interp_exp (bool): Case where average images are passed
                           and 50% exposure point needs to be
                           calculated (charmware .h5 file output format)
        dark_imgs (np.array|None): if temp_imgs is used and dark_imgs
                                   are passed then component wise temporal
                                   noise components will be calculated
                                   in addition to normal calc
        cf (float|None): system gain to use instead of the gain calculated
                         from images

    Returns:
        data (pd.DataFrame): DataFrame of all
                             EMVA response metrics + noise metrics
        hist (pd.DataFrame): DataFrame of all EMVA spatial metrics
        summ (pd.DataFrame): DataFrame of all EMVA summary metrics
    """
    res = dict()
    res_temporal = dict()
    res_spatial = dict()

    res_spatial = emva_spatial(img_list=img_list.copy(),
                               temp_imgs=temp_imgs.copy(),
                               L=L,
                               df=df.copy(),
                               rmv_ttn=rmv_ttn,
                               hpf=hpf,
                               image_idx_col=image_idx_col,
                               dark_imgs=dark_imgs,
                               shading_dim=shading_dim)

    res_temporal = emva_temporal(data=res_spatial['stats'],
                                 exp_col=exp_col,
                                 exp_col_units=exp_col_units,
                                 pixel_area=pixel_area,
                                 offset_factor=offset_factor,
                                 cf=cf)

    res = {**res_temporal, **res_spatial}

    return res


def emva_spatial(img_list: list,
                 temp_imgs: list,
                 L: int,
                 df: pd.DataFrame = pd.DataFrame(),
                 rmv_ttn: bool = False,
                 hpf: bool = False,
                 image_idx_col: str = 'Image Index',
                 dark_imgs: Optional[np.array] = None,
                 shading_dim=32) -> Mapping[str, pd.DataFrame]:

    """
    calculate all emva1288 spatial metrics
    keyword arguments:

    Returns:
        res (dict): res['hist'] (pd.DatFrame) EMVA1288 spatial metrics
                    res['stats'] (pd.DataFrame) All statistics
    """

    calc_vals = {}
    res = {}
    data = pd.DataFrame()
    hist = pd.DataFrame()
    shading = pd.DataFrame()

    # check if stats already exist in passed df, else get stats
    if 'Tot Var [DN^2]' in df.columns:
        data = pd.concat([data, df]).reset_index(drop=True)
    else:
        # case where dark images are available
        if not isinstance(dark_imgs, type(None)):
            dark_stats = get_stats(images=[dark_imgs],
                                   df=df.iloc[[0]],
                                   rmv_ttn=rmv_ttn,
                                   hpf=hpf,
                                   rmv_black=True,
                                   temp_imgs=None,
                                   L=None)['stats']

            # calculate avg and ttn_var frame from dark imgs
            dark_ttn_var = stats.tot_var_img_stack(dark_imgs, 1)
            dark_avg = stats.avg_img(dark_imgs)

            # insert into image lists for remaining processing
            img_list.insert(0, dark_avg)
            temp_imgs.insert(0, dark_ttn_var)

        # get statistics and join image data with params
        data = get_stats(images=img_list,
                         df=df,
                         rmv_ttn=rmv_ttn,
                         hpf=hpf,
                         temp_imgs=temp_imgs,
                         L=L)['stats']

        if not isinstance(dark_imgs, type(None)):
            data.drop(index=0, inplace=True)
            data = pd.concat([dark_stats, data]).reset_index(drop=True)

    if 'Mean Signal [DN]' in data.columns:
        data = ut.rename(data, revert=True)

    if image_idx_col not in data.columns:
        data[image_idx_col] = data.index

    calc_vals['u_y_black_subtracted'] = data['mean_black_subtracted'].values

    # get required images and averages
    dark_avg_img, \
        half_sat_avg_img, \
        half_sat_idx = ut.get_half_sat_img(img_list,
                                           data,
                                           calc_vals['u_y_black_subtracted'],
                                           image_idx_col)
    prnu_img = half_sat_avg_img - dark_avg_img

    calc_vals['dark_avg_img'] = dark_avg_img
    calc_vals['half_sat_avg_img'] = half_sat_avg_img
    calc_vals['dark_ttn_var'] = stats.avg_offset(temp_imgs[0])
    calc_vals['half_sat_ttn_var'] = stats.avg_offset(temp_imgs[half_sat_idx])
    calc_vals['L'] = L

    # add shading
    shading_vals = calcs.shading_calc(dark_avg_img, dim=shading_dim)
    shading = ut.dict_to_frame(shading_vals)

    # add prnu1288 histogram
    prnu_hist = emva.histogram1288(img=prnu_img,
                                   Qmax=256,
                                   L=calc_vals['L'],
                                   black_level=False)
    hist = ut.join_frame(hist, prnu_hist)

    # add dsnu1288 histogram
    dsnu_hist = emva.histogram1288(img=dark_avg_img,
                                   Qmax=256,
                                   L=calc_vals['L'],
                                   black_level=True)
    hist = ut.join_frame(hist, dsnu_hist)

    # add DSNU profiles
    prof = emva.profiles(dark_avg_img, dsnu=True)
    hist = ut.join_frame(hist, prof)

    # add PRNU profiles
    prof = emva.profiles(half_sat_avg_img, dsnu=False)
    hist = ut.join_frame(hist, prof)

    # calculate DSNU spectrogram
    spect = emva.spectrogram(img=dark_avg_img,
                             prnu_spect=False)
    hist = ut.join_frame(hist, spect)

    # calculate PRNU spectrogram
    spect = emva.spectrogram(prnu_img,
                             prnu_spect=True)
    hist = ut.join_frame(hist, spect)

    hist = ut.rename(hist)
    data = ut.rename(data)

    res['dark_shading'] = shading
    res['ptc_hist'] = hist
    res['stats'] = data

    summ_hpf = pd.DataFrame()
    if not hpf:
        emva_dsnu = emva.dsnu1288(dark_img=calc_vals['dark_avg_img'],
                                  ttn_var=calc_vals['dark_ttn_var'],
                                  L=calc_vals['L'])

        summ_hpf = ut.join_frame(summ_hpf, emva_dsnu)

        emva_prnu = emva.prnu1288(dark_img=calc_vals['dark_avg_img'],
                                  light_img=calc_vals['half_sat_avg_img'],
                                  dark_ttn_var=calc_vals['dark_ttn_var'],
                                  light_ttn_var=calc_vals['half_sat_ttn_var'],
                                  L=calc_vals['L'])

        summ_hpf = ut.join_frame(summ_hpf, emva_prnu)
        summ_hpf = ut.rename(summ_hpf)

    res['summ_hpf'] = summ_hpf

    return res


def emva_temporal(data: pd.DataFrame,
                  exp_col: str = 'Exposure [uW/cm^2*s]',
                  exp_col_units: str = 'uW/cm^2',
                  pixel_area: float = None,
                  offset_factor: float = 1.0,
                  cf: Optional[float] = None,
                  dark_frame=False) -> Mapping[str, pd.DataFrame]:
    """
    calculate ptc from a df of stats and no images
    """

    calc_vals = {}
    summ = pd.DataFrame()

    if 'Mean Signal [DN]' in data.columns:
        data = ut.rename(data, revert=True)

    # get values needed for all emva temporal funtions
    if 'mean_black_subtracted' not in data.columns:
        data_cols = ['tot_var', 'pix_var', 'col_var', 'row_var',
                     'tot_var_temp', 'pix_var_temp', 'col_var_temp',
                     'row_var_temp', 'mean']
        data = ut.remove_black(data, cols=data_cols)

    calc_vals['u_y'] = data['mean'].values
    calc_vals['u_y_black_subtracted'] = data['mean_black_subtracted'].values

    # find black level (assume first point..) TODO: make this more robust
    dark_idx = np.argmin(calc_vals['u_y'])
    calc_vals['u_y_dark'] = calc_vals['u_y'][dark_idx]
    calc_vals['tot_var_dark'] = data['tot_var'][dark_idx]
    calc_vals['pix_var_dark'] = data['pix_var'][dark_idx]
    calc_vals['row_var_dark'] = data['row_var'][dark_idx]
    calc_vals['col_var_dark'] = data['col_var'][dark_idx]
    calc_vals['dark_ttn_var'] = data['tot_var_temp'][dark_idx]

    # find half sat point
    if 'imageid' not in data.columns:
        data['imageid'] = data.index

    half_sat_idx = \
        data['imageid'].iloc[np.argmin(calc_vals['u_y_black_subtracted'])]
    half_sat_idx -= data['imageid'].min()
    half_sat = calc_vals['u_y_black_subtracted'].max() / 2
    half_sat_idx = \
        data['imageid'].iloc[ut.find_closest(calc_vals['u_y_black_subtracted'],
                                             half_sat)]
    half_sat_idx -= (data['imageid'].min() + 1)
    if half_sat_idx <= 0:
        print('could not calculate 50% point! Setting to half dataset size')
        half_sat_idx = data.shape[0] // 2
    calc_vals['u_y_half'] = calc_vals['u_y'][half_sat_idx]

    calc_vals['tot_var_half'] = data['tot_var'][half_sat_idx]
    calc_vals['pix_var_half'] = data['pix_var'][half_sat_idx]
    calc_vals['row_var_half'] = data['row_var'][half_sat_idx]
    calc_vals['col_var_half'] = data['col_var'][half_sat_idx]
    calc_vals['half_sat_ttn_var'] = data['tot_var_temp'][half_sat_idx]

    # additional calculation values..
    calc_vals['sig2_y'] = data['tot_var_temp_black_subtracted'].values
    calc_vals['sig2_ydark'] = data['tot_var_temp'].iloc[0]
    calc_vals['exp'] = data[exp_col]
    calc_vals['exp_vals'] = data[exp_col].values
    data['Tot Temp Var - Dark [DN^2]'] = data['tot_var_temp_black_subtracted']

    # case where we have an exposure sweep but also grabbed
    # a 0 power frame
    if dark_frame:
        calc_vals['exp'][0] = 0.0 # FIXME: Need to write 0.0 because the calculation of responsivity
        calc_vals['exp_vals'][0] = 0.0

    # get system gain, if we pass system gain use the passed
    # value for all future calculations
    # u_y_black_subtracted = calc_vals['u_y_black_subtracted'][1:] # TODO: Need to add this to delete the first value (dark value - 0)
    # sig2_y = calc_vals['sig2_y'][1:]
    if isinstance(cf, type(None)):
        sys_gain = emva.system_gain(u_y=calc_vals['u_y_black_subtracted'],
                                    sig2_y=calc_vals['sig2_y'])
    else:
        sys_gain = {}
        sys_gain['fit'] = np.nan
        sys_gain['system_gain'] = 1 / cf

    data['System Gain Fit [DN^2]'] = pd.Series(sys_gain['fit'])
    summ['System Gain [DN/e]'] = pd.Series(sys_gain['system_gain'])
    summ['Conversion Factor [e/DN]'] = 1 / sys_gain['system_gain']
    calc_vals['K'] = sys_gain['system_gain']

    # get all noise metrics in e
    # TODO:fix this....
    keysd = ut.stat_engine_col_rename()

    for val in keysd:
        if (val not in data.columns) or ('mean' in val) or \
           ('_e' in val) or ('_e^2' in val):
            continue
        if 'var' in val:
            val2 = val + '_e^2'
            data[val2] = data[val] / calc_vals['K']**2
        elif 'std' in val:
            val2 = val + '_e'
            data[val2] = data[val] / calc_vals['K']

    # get dark temporal noise
    dtn = emva.dark_temporal_noise(sig2_ydark=calc_vals['sig2_ydark'],
                                   K=calc_vals['K'])
    summ = ut.join_frame(summ, dtn)
    calc_vals['dark_noise_e'] = dtn['dark_temporal_noise_e']

    # get component wise temporal noise if we have the infomration available
    if 'pix_var_temp' in data.columns:
        sub = data[(data['mean'] ==
                   data['mean'].min())].reset_index(drop=True)
        sub = sub[['pix_std_temp_e',
                   'col_std_temp_e',
                   'row_std_temp_e']]
        summ = summ.join(sub)

    # add DSNU
    sub = pd.DataFrame()
    sub['total_dsnu'] = pd.Series(np.sqrt(calc_vals['tot_var_dark']))
    sub['pix_dsnu'] = np.sqrt(calc_vals['pix_var_dark'])
    sub['row_dsnu'] = np.sqrt(calc_vals['row_var_dark'])
    sub['col_dsnu'] = np.sqrt(calc_vals['col_var_dark'])
    summ = ut.join_frame(summ, sub, replace_DN=True, K=calc_vals['K'])

    ele = emva.get_electrons(u_y=calc_vals['u_y_black_subtracted'],
                             K=calc_vals['K'])

    # add PRNU
    prnu = calcs.prnu1288(calc_vals)
    summ = ut.join_frame(summ, prnu)

    # get electrons
    calc_vals['u_e'] = ele['u_e']
    data['Mean Signal [e]'] = pd.Series(ele['u_e'])

    # add linearity error
    lin = emva.linearity(mean_arr=calc_vals['u_y_black_subtracted'],
                         exp_arr=calc_vals['exp'],
                         ttn_arr=calc_vals['sig2_y'])

    data['linearity_fit_DN'] = pd.Series(lin['linearity_fit_DN'])
    data['linearity_error_%'] = pd.Series(lin['linearity_error_%'])
    data['linearity_error_DN'] = pd.Series(lin['linearity_error_DN'])
    summ['linearity_error_max_%'] = lin['linearity_error_max_%']
    summ['linearity_error_max_DN'] = lin['linearity_error_max_DN']
    summ['linearity_error_min_%'] = lin['linearity_error_min_%']
    summ['linearity_error_min_DN'] = lin['linearity_error_min_DN']

    # add get photons
    if pixel_area == None:
        msg = "\nKeyword 'pixel_area' must be provided!"
        raise ValueError(msg)

    if offset_factor == None:
        msg = "\nKeyword 'offset_factor' must be provided!"
        raise ValueError(msg)

    photons = emva.get_photons(wl=data['powermeter.wavelength'][0],
                               texp=calc_vals['exp'],
                               power=data['powermeter.measure'],
                               offset_factor = offset_factor,
                               pixel_area=pixel_area)

    # add responsivity
    resp = emva.responsivity(u_p=photons['u_p'],
                             u_y=calc_vals['u_y_black_subtracted'],
                             sig2_y=calc_vals['sig2_y'])

    data['photons'] = pd.Series(photons['u_p'])
    data['responsivity_fit'] = pd.Series(resp['responsivity_fit'])
    summ[f'Responsivity [DN/photons)]'] = resp['responsivity']

    # add quantum efficiency (QE)
    qe = (resp['responsivity']/calc_vals['K'])
    summ['Quantum Efficiency [%]'] = qe*100

    # add saturation capacity
    sat = emva.saturation_capacity(u_p=data['Mean Signal [e]'],
                                   sig2_y=calc_vals['sig2_y'],
                                   qe=qe)
    summ['sat_capacity_e'] = sat['sat_capacity_p']
    summ['sat_capacity_DN'] = summ['sat_capacity_e'] * calc_vals['K']

    # add sensitivity threshold
    sen = emva.sensitivity_threshold(sig2_ydark=calc_vals['sig2_ydark'],
                                     qe=qe,
                                     K=calc_vals['K'])

    summ['sensitivity_threshold_e'] = sen['sensitivity_threshold_e']
    summ['sensitivity_threshold_DN'] = \
        summ['sensitivity_threshold_e'] * calc_vals['K']

    # quick dynamic range calculation
    dr = emva.dynamic_range(u_p=calc_vals['u_e'],
                            sig2_y=calc_vals['sig2_y'],
                            sig2_ydark=calc_vals['sig2_ydark'],
                            qe=qe,
                            K=calc_vals['K'])

    summ = ut.join_frame(summ, dr)

    # calculate snr (temp + fpn), once again hack of emva func
    snr = emva.snr(dsnu_tot=summ['total_dsnu_DN'].iloc[0],
                   prnu_tot=summ['tot_prnu1288_%'].iloc[0],
                   u_p=data['Mean Signal [e]'].values,
                   s2_d=calc_vals['dark_noise_e'],
                   K=calc_vals['K'],
                   qe=qe)

    data = ut.join_frame(data, snr)

    # calculate snr ideal (sqrt(photons)), or in this case
    # sqrt(electrons)
    snr_ideal = emva.snr_ideal(u_p=data['Mean Signal [e]'])
    data = ut.join_frame(data, snr_ideal)

    snr_t = emva.snr_theoretical(u_p=data['Mean Signal [e]'].values,
                                 s2_d=calc_vals['dark_noise_e'],
                                 K=calc_vals['K'],
                                 qe=qe)
    data = ut.join_frame(data, snr_t)

    data = ut.rename(data)
    summ = ut.rename(summ)

    res = {}
    res['data'] = data
    res['summ'] = summ

    return res


def _gen_test_imgs():
    """
    """
    from characterization_ams.utilities import image_generator

    res = dict()

    # generate images
    ped_start = 168
    peds = np.linspace(168, 3800, 30)
    power = np.linspace(0, 10, 30)
    rows = 100
    cols = 100
    tint = 16e-3
    images = []
    temp = pd.DataFrame()
    raw = pd.DataFrame()
    for (idx, pp) in enumerate(peds):
        n_images = 100
        rfpn = 105
        cfpn = 101
        ctn = 15
        rtn = 12
        ptn = 20 + np.sqrt(pp)
        pfpn = 95 + 0.08 * (pp - ped_start)

        imgs = image_generator.gen_images(cfpn=cfpn,
                                          rfpn=rfpn,
                                          pfpn=pfpn,
                                          rtn=rtn,
                                          ptn=ptn,
                                          ctn=ctn,
                                          rows=rows,
                                          cols=cols,
                                          pedestal=pp,
                                          n_images=n_images)

        images.append(np.array(imgs))
        temp['Power'] = pd.Series(power[idx])
        temp['imageid'] = idx
        temp['stack size'] = n_images
        temp['rows'] = rows
        temp['cols'] = cols
        temp['Exposure [uW/cm^2*s]'] = tint * pd.Series(power[idx])
        raw = pd.concat([raw, temp]).reset_index(drop=True)

    avg_images = []
    temp_images = []
    for img in images:
        ttn_var = stats.tot_var_img_stack(img)
        avg = stats.avg_img(img)
        temp_images.append(ttn_var)
        avg_images.append(avg)

    res['images'] = images
    res['avg_images'] = avg_images
    res['temp_images'] = temp_images
    res['df'] = raw

    return res


if __name__ == '__main__':
    sim_vals = _gen_test_imgs()
    res = ptc(sim_vals['images'],
              df=sim_vals['df'])
