import numpy as np
from scipy import stats as st
from characterization_ams.stats_engine import stats
from characterization_ams.utilities import utilities as ut
from characterization_ams.emva import routines as emva1288r
from typing import Mapping
np.seterr(divide='ignore')
np.seterr(invalid='ignore')


__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


def cycles(FFT: np.array) -> Mapping[str, np.array]:
    """
    calculate cycles [periods/pixel] and power spectrum
    based on FFT
    EMVA 4.0: Section 8.6

    Keyword Arguments:
        FFT (np.array): array of FFT data

    Returns:
        temp (dict): power_spectrum, cycles
    """

    temp = {}

    n = len(FFT)
    x = np.arange(n)

    cycles = x * 1 / (2 * n)
    data = np.sqrt(FFT)

    temp = {'cycles': cycles,
            'power_spectrum': data}

    return temp


def dark_current(d_mean: np.array,
                 d_var: np.array,
                 tint: np.array) -> Mapping[str, np.array]:
    """
    calculate dark current from mean and from variance
    EMVA 4.0: Section 7

    Keyword Arguments:
        d_mean (np.array): array of mean dark values
        d_var (np.array): array of dark variance values
        tint (np.array): array of integration time values

    Returns:
        temp (dict): u_ydark: dark current from mean
                     sig2_ydark: dark current from variance
                     u_ydark_off: offset from mean
                     sig2_ydark_off: offset from variance
                     u_ydark_fit: fit from mean
                     sig2_ydark_fit: fit from variance
    """

    temp = {}

    try:
        # get dark current from mean
        dark_mean = st.linregress(tint, d_mean)
        slope = dark_mean[0]
        offset = dark_mean[1]
        fit = slope * tint + offset

        # get dark current from var
        dark_var = st.linregress(tint, d_var)
        slope_var = dark_var[0]
        offset_var = dark_var[1]
        fit_var = slope_var * tint + offset_var

        # add DN results to dict
        temp = {'Dark Current [DN/s]': slope,
                'Dark Current [DN^2/s]': slope_var,
                'u_ydark [DN]': dark_mean,
                'sig2_ydark [DN^2]': dark_var,
                'u_ydark_off [DN]': offset,
                'sig2_ydark_off [DN^2]': offset_var,
                'u_ydark_fit [DN]': fit,
                'sig2_ydark_fit [DN^2]': fit_var}

    except Exception as e:
        print(f'Could not calculate dark current, Error: {e}')

    return temp


def dark_temporal_noise(sig2_ydark: float,
                        K: float,
                        s2_q: float = 1/12) -> Mapping[str, float]:
    """
    calculate dark temporal noise
    Emva 4.0: Eq. 53

    Keyword Arguments:
        sig2_ydark (float): total temporal noise at dark
        K (float): system gain [DN/e]
        s2_q (float, 1/12): quantization noise

    Returns:
        temp (dict): dark_temporal_noise_DN
                     dark_temporal_noise_e
    """

    temp = {}

    # remove quantization noise
    s_d = np.sqrt(sig2_ydark - s2_q)
    s_d_e = s_d / K

    temp = {'dark_temporal_noise_DN': s_d,
            'dark_temporal_noise_e': s_d_e}

    return temp


def dsnu1288(dark_img: np.array,
             ttn_var: float,
             L: int) -> Mapping[str, float]:
    """
    Calculate row, col, pix, and total DSNU1288
    EMVA 4.0: Eq. 66

    Keyword Arguments:
        dark_img (np.array): array of mean pixel values at black level
        ttn_var (float): temporal noise variance at dark
        L (int): size of image stack used to calculate dark_img
        hpf (bool): image is high pass filtered prior
                    to spatial variance calc if True

    Returns:
        temp (dict): total_dsnu
                     row_dsnu
                     col_dsnu
                     pix_dsnu
    """

    temp = {}

    vars = spatial_variance(img=dark_img,
                            ttn_var=ttn_var,
                            L=L,
                            hpf=True,
                            rmv_ttn=True)

    temp = {'total_dsnu': np.sqrt(vars['total_s2_y']),
            'row_dsnu': np.sqrt(vars['row_s2_y']),
            'col_dsnu': np.sqrt(vars['col_s2_y']),
            'pix_dsnu': np.sqrt(vars['pix_s2_y'])}

    return temp


def dsnu1288_stack(img_stack: np.array) -> Mapping[str, float]:
    """
    Calculate DSNU1288 from a stack of images
    EMVA 4.0: Eq. 66

    Keyword Arguments:
        dark_img (np.array): stack of images
        hpf (bool): image is high pass filtered prior
                    to spatial variance calc if True

    Returns:
        temp (dict): total_dsnu
                     row_dsnu
                     col_dsnu
                     pix_dsnu
    """

    temp = {}

    # get number of images
    if isinstance(img_stack, type(np.array)):
        L = img_stack.shape[0]
    else:
        L = len(img_stack)

    # get avg image and ttn_var
    dark_img = stats.avg_img(img_stack)
    ttn_var = stats.total_var_temp(img_stack)

    # calculate dsnu1288
    temp = dsnu1288(dark_img=dark_img,
                    ttn_var=ttn_var,
                    L=L)

    return temp


def dynamic_range(u_p: np.array,
                  sig2_y: float,
                  sig2_ydark: float,
                  qe: float,
                  K: float,
                  s2_q: float = 1/12) -> Mapping[str, np.array]:
    """
    calculate dynamic range
    EMVA 4.0: Eq 28

    Keyword Arguments:
        u_p (np.array): array of photon values
        sig2_y (np.array): array of total temporal noise, sig2_y - sig2_ydark
        sig2_ydark (float): total temporal noise at dark
        qe (float): quantum efficiency at wavelength used for dataset
        K (float): system gain [DN/e]
        s2_q (float): quantization noise

    Returns:
        temp (dict): dynamic_range_ratio
                     dynamic_range_db
                     dynamic_range_bits
    """

    temp = {}

    u_p_min = sensitivity_threshold(sig2_ydark=sig2_ydark,
                                    qe=qe,
                                    K=K,
                                    s2_q=s2_q)

    u_p_max = saturation_capacity(u_p=u_p,
                                  sig2_y=sig2_y,
                                  qe=qe)

    dr = u_p_max['sat_capacity_e'] / \
        u_p_min['sensitivity_threshold_e']

    temp = {'dynamic_range_ratio': dr,
            'dynamic_range_db': 20 * np.log10(dr),
            'dynamic_range_bits': np.log2(dr)}

    return temp


def get_electrons(u_y: np.array, K: float) -> Mapping[str, np.array]:
    """
    calculate the number of electrons based on DN signal

    Keyword Arguments:
        u_y (np.array): mean signal in DN
        K (float): system gain [DN/e]

    Returns:
        temp (dict): u_e: number of electrons
    """

    temp = {'u_e': u_y / K}

    return temp


def get_photons(wl: float,
                texp: float,
                power: float,
                pixel_area: float,
                offset_factor: float) -> Mapping[str, np.array]:
    """
    calculate the number of photons, can sweep exposure
    or power

    Keyword Arguments:
        wl (float): wavelength of spectrum used in [nm]
        texp (float|np.array): integration time used in [ms]
        power (float:np.array): power used in [uW/cm^2]
        pixel_area (float): pixel active area in [um^2]

    Returns:
        temp (dict): u_p: number of photons
    """

    temp = {}

    # get constants
    h = 6.6260755e-34 # Planck's constant (Js)
    c = 2.99792458e8  # speed of light (m/s)

    # update units for calc
    wl_ = wl * 1e-9
    texp_ = texp * 1e-3
    pixel_area_ = pixel_area * 1e-12
    power_ = power * 1e-2

    # get photons
    u_p = power_ * offset_factor * pixel_area_ * texp_ * wl_ / (h * c)

    temp = {'u_p': u_p}

    return temp


def histogram1288(img: np.array,
                  Qmax: int,
                  L: int,
                  black_level: bool = False) -> Mapping[str, np.array]:
    """
    calculate histogram bins and values from a dark image
    EMVA 4.0: Section 8.8

    Keyword Arguments:
        img (np.array): array of pixel values
        Qmax (int): number of bins (Qmax <= 256)
        L (int): size of image stack
        black_level (bool): If true bins are shifted to be centered around 0
                            this should be True for DSNU1288 histogram where
                            our img != img - dark

    Returns:
        temp (dict): values: number of pixels/bin
                     bins: deviation from mean
                     accumulated values: percent of pixels/bin
                     accumulated bins: deviation from mean
    """

    temp = {}
    type_ = 'dsnu'

    # make sure Qmax is valid
    if Qmax > 256:
        print('Qmax must be less than or equal to 256, setting Qmax=256')
        Qmax = 256
    if not isinstance(Qmax, int):
        Qmax = int(Qmax)

    # hpf the image if prnu image
    if not black_level:
        img = ut.high_pass_filter(img, 5)
        type_ = 'prnu'

    # emva routine expects int type
    img = img.astype(int)

    # calculate accumulated data
    accumulated = np.abs(img - int(img.flatten().mean()))

    # calculate histograms
    temp = emva1288r.Histogram1288(img, Qmax)
    temp_acc = emva1288r.Histogram1288(accumulated, Qmax)

    # hpf case, we make sure to scale the bins based on hpf kern
    if not black_level:
        temp['bins'] /= (25.)
        temp_acc['bins'] /= (25.)
    else:
        # case where we DID NOT subtract off black level (img - dark)
        temp['bins'] -= (img.flatten().mean())

    # update values for accumulated histogram
    temp_acc['values'] = np.cumsum(temp_acc['values'][::-1])[::-1]
    temp_acc['values'] = 100 * temp_acc['values'] / accumulated.size

    # update key name for accumulated histogram
    temp_acc = {f'accumulated_{k}': v for k, v in temp_acc.items()}

    # combine result
    temp = {**temp, **temp_acc}
    temp = {f'{type_}_{k}': v for k, v in temp.items()}

    return temp


def histogram1288_stack(img_stack: np.array,
                        Qmax: int,
                        black_level: bool = False) -> Mapping[str, np.array]:
    """
    calculate histogram bins and values from a stack of images
    EMVA 4.0: Section 8.8

    Keyword Arguments:
        img_stack (np.array): stack of images
        Qmax (int): number of bins (Qmax <= 256)
        black_level (bool): If true bins are shifted to be centered around 0
                            this should be True for DSNU1288 histogram where
                            our img != img - dark
    Returns:
        temp (dict): values: number of pixels/bin
                     bins: deviation from mean
                     accumulated values: percent of pixels/bin
                     accumulated bins: deviation from mean
    """

    temp = {}

    # get number of images
    if isinstance(img_stack, type(np.array)):
        L = img_stack.shape[0]
    else:
        L = len(img_stack)

    # get avg image and ttn_var
    img = stats.avg_img(img_stack)

    # calculate histograms
    temp = histogram1288(img=img,
                         Qmax=Qmax,
                         L=L,
                         black_level=black_level)

    return temp


def linearity(mean_arr: np.array,
              exp_arr: np.array,
              ttn_arr: np.array) -> Mapping[str, np.array]:
    """
    calculate weighted linearity error
    EMVA 4.0: Eq. 61 & 62

    Keyword Arguments:
         mean_arr (np.array): mean signal array used for fit
         exp_arr (np.array): exposure array used for fit
         ttn_arr (np.aray): total temporal noise array

    Returns: temp (dict): linearity_fit
                          linearity_error
                          Linearity Error [%]
                          Linearity Error max [%]
                          Linearity Error min [%]
                          Linearity Error max
                          Linearity Error min
    """

    # add to dict
    temp = {'linearity_fit_DN': np.nan,
            'linearity_error_DN': np.nan,
            'linearity_error_%': np.nan,
            'linearity_error_max_%': np.nan,
            'linearity_error_min_%': np.nan,
            'linearity_error_max_DN': np.nan,
            'linearity_error_min_DN': np.nan}

    # truncate to max temporal noise
    max_t = ut.filter_by_temporal(ttn_arr)
    mean_arr_sub = mean_arr[:max_t]
    exp_arr_sub = exp_arr[:max_t]

    # truncate from 5%-95% of max temp trun arrays
    lower_idx = ut.get_index(mean_arr, 0.05, upper=False)
    if lower_idx == 0:
        lower_idx = 1
    upper_idx = ut.get_index(mean_arr, 0.95, upper=True)
    mean_arr_sub = mean_arr_sub[lower_idx:upper_idx].astype(float)
    exp_arr_sub = exp_arr_sub[lower_idx:upper_idx].astype(float)

    # get weights remove inf/nan for fit
    # usually the first value since we take 1/0
    w = 1 / mean_arr_sub
    w[w == np.inf] = 0
    w[w == np.nan] = 0

    # make the fit
    try:
        offset, slope = np.polynomial.polynomial.polyfit(exp_arr_sub,
                                                         mean_arr_sub,
                                                         1,
                                                         w=w)

        # calculate key metrics
        fit = exp_arr_sub * slope + offset
        fit_dev = mean_arr_sub - fit
        fit_dev_perc = (mean_arr_sub - fit) / fit * 100
        fit_dev_max = fit_dev.max()
        fit_dev_min = fit_dev.min()
        fit_dev_perc_max = fit_dev_perc.max()
        fit_dev_perc_min = fit_dev_perc.min()

        # add to dict
        temp = {'linearity_fit_DN': fit,
                'linearity_error_DN': fit_dev,
                'linearity_error_%': fit_dev_perc,
                'linearity_error_max_%': fit_dev_perc_max,
                'linearity_error_min_%': fit_dev_perc_min,
                'linearity_error_max_DN': fit_dev_max,
                'linearity_error_min_DN': fit_dev_min}

    except Exception as e:
        print(f'Could not make linearity_fit, Error {e}')

    return temp


def prnu1288(dark_img: np.array,
             light_img: np.array,
             dark_ttn_var: float,
             light_ttn_var: float,
             L: int) -> Mapping[str, float]:
    """
    calculate total, row, col, and pix PRNU1288 from avg images
    EMVA 4.0: Eq. 67

    Keyword Arguments:
        dark_img (np.array): image of average black level values
        light_img (np.array): image of average signal values at 50% sat.
        light_ttn_var (float): total temporal noise from stack 50% sat.
                               average was taken from
        dark_ttn_var (float): total temporal noise from stack dark
                              average was taken from
        L (float): number of frames in stack average was taken from

    Returns:
        temp (dict): tot_prnu1288_%
                     row_prnu1288_%
                     col_prnu1288_%
                     pix_prnu1288_%
    """

    temp = {}

    # calculate mean
    light_mean = stats.avg_offset(light_img)
    dark_mean = stats.avg_offset(dark_img)

    # get spatial variances
    spatial = spatial_variance(light_img, light_ttn_var, L)
    dark_spatial = spatial_variance(dark_img, dark_ttn_var, L)

    # total prnu
    tot_prnu = np.sqrt(spatial['total_s2_y'] - dark_spatial['total_s2_y']) \
        / (light_mean - dark_mean) * 100

    # row prnu
    row_prnu = np.sqrt(spatial['row_s2_y'] - dark_spatial['row_s2_y']) \
        / (light_mean - dark_mean) * 100

    # col prnu
    col_prnu = np.sqrt(spatial['col_s2_y'] - dark_spatial['col_s2_y']) \
        / (light_mean - dark_mean) * 100

    # pix prnu
    pix_prnu = np.sqrt(spatial['pix_s2_y'] - dark_spatial['pix_s2_y']) \
        / (light_mean - dark_mean) * 100

    temp = {'tot_prnu1288_%': tot_prnu,
            'row_prnu1288_%': row_prnu,
            'col_prnu1288_%': col_prnu,
            'pix_prnu1288_%': pix_prnu}

    return temp


def prnu1288_stack(dark_stack: np.ndarray,
                   light_stack: np.ndarray) -> Mapping[str, float]:
    """
    calculate total, row, col, and pix PRNU1288 from stack of images
    EMVA 4.0: Eq. 67

    Keyword Arguments:
        dark_stack (np.array): stack of black level images
        light_stack (np.array): stack of 50% sat. images

    Returns:
        temp (dict): tot_prnu1288_%
                     row_prnu1288_%
                     col_prnu1288_%
                     pix_prnu1288_%
    """

    temp = {}

    # get number of images
    if isinstance(dark_stack, type(np.array)):
        L = dark_stack.shape[0]
    else:
        L = len(dark_stack)

    # get mean image
    light_mean = stats.avg_img(light_stack)
    dark_mean = stats.avg_img(dark_stack)

    # get ttn_var
    light_ttn_var = stats.total_var_temp(light_stack)
    dark_ttn_var = stats.total_var_temp(dark_stack)

    # calculate prnu
    temp = prnu1288(dark_img=dark_mean,
                    light_img=light_mean,
                    dark_ttn_var=dark_ttn_var,
                    light_ttn_var=light_ttn_var,
                    L=L)

    return temp


def profiles(img: np.ndarray,
             dsnu: bool = True) -> Mapping[str, np.array]:
    """
    calculate profiles for an image

    Keyword Arguments:
        img (np.array): image to calculate profile from
        dsnu (bool): if True then dsnu is added to key name, else
                     prnu is added to key name

    Returns:
        temp (dict): Index Horizontal (np.array): index of columns
                     Middle Horizontal (np.array): center value of columns
                     Mean Horizontal (np.array): mean value of columns
                     Max Horizontal (np.array): max value of columns
                     Min Horizontal (np.array): min value of columns
                     Index Vertical (np.array): index of rows
                     Middle Vertical (np.array): center value of rows
                     Mean Vertical (np.array): mean value of rows
                     Max Vertical (np.array): max value of rows
                     Min Vertical (np.array): min value of rows
    """

    temp = {}

    if dsnu:
        type_ = 'dsnu'
    else:
        type_ = 'prnu'

    # calculate profiles
    hor = stats.profile(img, horizontal=True)
    vert = stats.profile(img, horizontal=False)

    # combine vertical and horizontal profiles
    temp = {**hor, **vert}

    # add key to denote profile type
    temp = {f'{type_}_{k}': v for k, v in temp.items()}

    return temp


def responsivity(u_p: np.array,
                 u_y: np.array,
                 sig2_y: float) -> Mapping[str, np.array]:
    """
    calculate responsivity, emva defines this in units DN/photons,
    but could u_p could be replaced with lux/uW/cm^2/etc.
    EMVA 4.0: Eq. 49

    Keyword Arguments:
        u_p (np.array): array of photons
        u_y (np.array): array of signal - dark, u_y should be u_y - u_ydark
        sig2_y (np.array): array of temporal noise values,
                         should be sig2_y - sig2_ydark
    Returns:
        temp (dict): responsivity (float): responsivity
                     responsivity_offset (float): offset of fit line
                     responsivity_fit [DN] (np.array): responsivity fit line
    """

    temp = {'responsivity': np.nan,
            'responsivity_offset': np.nan,
            'responsivity_fit': np.nan}

    # get max temporal noise index and truncate
    ttn_idx = ut.filter_by_temporal(sig2_y)
    u_p_sub = u_p[:ttn_idx+1]
    u_y_sub = u_y[:ttn_idx+1]

    # we fit to 70% of signal lfw signal, truncate to 70%
    upper_idx = ut.get_index(vals=u_y_sub, perc=0.7, upper=True)
    u_p_sub = u_p_sub[:upper_idx+1].astype(float)
    u_y_sub = u_y_sub[:upper_idx+1].astype(float)

    try:
        # get responsivity, offset, and fit
        response = st.linregress(u_p_sub, u_y_sub)
        slope = response[0]
        offset = response[1]
        fit = u_p_sub * slope + offset

        # add to dict
        temp = {'responsivity': slope,
                'responsivity_offset': offset,
                'responsivity_fit': fit}

    except Exception as e:
        print(f'could not make responsivity_fit, Error: {e}')

    return temp


def saturation_capacity(u_p: np.array,
                        sig2_y: float,
                        qe: float) -> Mapping[str, float]:
    """
    calculate saturation capacity
    EMVA 4.0: Eq. 24

    Keyword Arguments:
        u_p (np.array): array of photon values
        sig2_y (np.array): array of temporal noise values,
                         should be sig2_y - sig2_ydark
        qe (float): quantum efficiency at wavelength used for dataset

    Returns:
        temp (dict): sat_capacity_p
                     sat_capacity_e
    """

    temp = {}

    # filter based on max temporal noise
    max_idx = ut.filter_by_temporal(sig2_y)
    u_p_sub = u_p[:max_idx]

    # get max p and e- value
    temp = {'sat_capacity_p': u_p_sub.max(),
            'sat_capacity_e': u_p_sub.max() * qe
            }

    return temp


def sensitivity_threshold(sig2_ydark: float,
                          qe: float,
                          K: float,
                          s2_q: float = 1/12) -> Mapping[str, float]:
    """
    calculate sensitivity threshold
    EMVA 4.0: Eq 26 & Eq 27

    Keyword Arguments:
        sig2_ydark (float): total temporal noise at dark
        qe (float): quantum efficiency at wavelength used for dataset
        K (float): system gain [DN/e]
        s2_q (float)" quantization noise

    Returns:
        temp (dict): sensitivity_threshold_p
                     sensitivity_threshold_e
    """

    temp = {}

    # get dark temporal noise
    s2_d = \
        dark_temporal_noise(sig2_ydark, K)['dark_temporal_noise_e']**2

    # calculate sensitivity threshold
    u_e_min = np.sqrt(s2_d + s2_q/K**2 + 0.25) + 0.5
    u_p_min = 1 / qe * u_e_min

    temp = {'sensitivity_threshold_e': u_e_min,
            'sensitivity_threshold_p': u_p_min}

    return temp


def snr(dsnu_tot: np.ndarray,
        prnu_tot: np.ndarray,
        u_p: np.ndarray,
        s2_d: float,
        K: float,
        qe: float,
        s2_q: float = 1/12) -> Mapping[str, np.array]:
    """
    Calculate SNR using temporal and spatial noise components
    EMVA 4.0: Eq. 69

    Keyword Arguments:
        dark_img (np.array): average dark image to be used for DSNU
        light_img (np.array): average 50% sat image to be used for PRNU
        dark_ttn_var (float): total temporal noise from dark_img stack
        light_ttn_var (float): total temporal noise from light_img stack
        L (int): size of dark_img and light_img stack used
        u_p (np.array): array of photons
        s2_d (float): dark temporal noise [e]
        K (float): system gain
        qe (float): quantum efficiency
        s2_q (float): quantization noise

    Returns:
        temp (dict): snr_dB
                     snr [ratio]
    """

    temp = {}

    prnu_tot *= 1e-2

    snr = (qe * u_p) / \
        np.sqrt(s2_d + dsnu_tot**2 + s2_q/K**2 +
                qe * u_p + prnu_tot**2 * (qe * u_p)**2)

    # force first point to be 0 (currently inf)
    snr[0] = 0

    temp = {'snr_dB': 20 * np.log10(snr),
            'snr_ratio': snr}

    # force first point to be np.nan (currently inf)
    temp['snr_dB'][0] = np.nan
    temp['snr_ratio'][0] = np.nan

    return temp


def snr_stack(dark_stack: np.ndarray,
              light_stack: np.ndarray,
              u_p: np.array,
              s2_d: float,
              K: float,
              qe: float,
              s2_q: float = 1/12) -> Mapping[str, np.array]:
    """
    Calculate SNR using temporal and spatial noise components from a stack
    of images
    EMVA 4.0: Eq. 69

    Keyword Arguments:
        dark_stack (np.array): stack of dark images for DSNU calc
        light_stack (np.array): stack of light images for PRNU calc
        u_p (np.array): array of photons
        s2_d (float): dark temporal noise [e]
        K (float): system gain
        qe (float): quantum efficiency
        s2_q (float): quantization noise

    Returns:
        temp (dict): snr_dB
                     snr [ratio]
    """

    temp = {}

    dsnu = dsnu1288_stack(dark_stack)
    prnu = prnu1288_stack(dark_stack=dark_stack,
                          light_stack=light_stack)

    dsnu_tot = dsnu['total_dsnu']
    prnu_tot = prnu['tot_prnu1288_%']

    temp = snr(dsnu_tot=dsnu_tot,
               prnu_tot=prnu_tot,
               u_p=u_p,
               s2_d=s2_d,
               K=K,
               qe=qe)

    return temp


def snr_ideal(u_p: np.array) -> Mapping[str, np.array]:
    """
    calculate ideal snr (shot noise)
    EMVA 4.0: Eq. 23

    Keyword Arguments:
        u_p (np.array): array of photons

    Returns:
        temp (dict): SNR Ideal [dB]
                     SNR Ideal [ratio]
    """

    temp = {'snr_ideal_dB': 20 * np.log10(np.sqrt(u_p)),
            'snr_ideal_ratio': np.sqrt(u_p)}

    # force first point to be np.nan (currently inf)
    temp['snr_ideal_dB'][0] = np.nan
    temp['snr_ideal_ratio'][0] = np.nan

    return temp


def snr_photons(snr_level: float,
                u_p: np.array,
                s2_d: float,
                K: float,
                qe: float,
                s2_q: float = 1/12) -> Mapping[str, np.array]:
    """
    Get number of photons required for a given SNR value
    EMVA 4.0: Eq. 25

    Keyword Arguments:
        snr_level (float): snr level to get number of photons for
        u_p (np.array): array of photons
        s2_d (float): dark temporal noise [e]
        K (float): system gain
        qe (float): quantum efficiency
        s2_q (float): quantization noise

    Returns:
        temp (dict): irradiance
    """

    temp = {}

    u_p_snr = \
        (snr_level**2 / (2 * qe)) * \
        (1 + np.sqrt(1 + (4 * (s2_d + s2_q/K**2)/snr_level**2)))

    temp = {'irradiance': u_p_snr}

    return temp


def snr_theoretical(u_p: np.array,
                    s2_d: float,
                    K: float,
                    qe: float,
                    s2_q: float = 1/12) -> Mapping[str, np.array]:
    """
    Calculate SNR based on linear camera model
    EMVA 4.0: Eq. 21

    Keyword Arguments:
        u_p (np.array): array of photons
        s2_d (float): dark temporal noise [e]
        K (float): system gain
        qe (float): quantum efficiency
        s2_q (float): quantization noise

    Returns:
        temp (dict): snr_theoretical_dB
                     snr_theoretical_ratio
    """

    temp = {}

    snr = (qe * u_p) / np.sqrt(s2_d + s2_q / K**2 + qe * u_p)

    temp = {'snr_theoretical_dB': 20 * np.log10(snr),
            'snr_theoretical_ratio': snr}

    # force first point to be np.nan (currently inf)
    temp['snr_theoretical_dB'][0] = np.nan
    temp['snr_theoretical_ratio'][0] = np.nan

    return temp


def snr_max():
    """
    """
    pass


def snr_inv():
    """
    """

    pass


def system_gain(u_y: np.array, sig2_y: np.array) -> Mapping[str, float]:
    """
    calculate system gain [DN/e]
    EMVA 4.0: Eq. 15

    Keyword Arguments:
        u_y (np.array): signal - dark values (u_y - u_ydark)
        sig2_y (np.array): total temp noise - total dark temp noise
                           (sig2_y - sig2_ydark)

    Returns:
        temp (dict): system_gain
                     offset
                     std_error
                     fit
    """

    temp = {}
    K = np.nan
    offset = np.nan
    std_err = np.nan
    fit = np.nan

    # filter by max temporal
    max_idx = ut.filter_by_temporal(sig2_y)
    u_y_sub = u_y[:max_idx]
    sig2_y_sub = sig2_y[:max_idx]

    # fit from 0 - 70% of lfw
    upper_idx = ut.get_index(u_y_sub, 0.70)
    u_y_sub = u_y_sub[:upper_idx+1]
    sig2_y_sub = sig2_y_sub[:upper_idx+1]

    # attempt to make the fit
    try:
        conv = st.linregress(u_y_sub, sig2_y_sub)

        # get values
        K = conv[0]
        offset = conv[1]
        std_err = conv[4]
        fit = u_y_sub * K + offset

    except Exception as e:
        print(f'could not make system gain fit, Error {e}')
    temp = {'system_gain': K,
            'offset': offset,
            'std_error': std_err,
            'fit': fit}

    return temp


def spatial_variance(img: np.ndarray, ttn_var: float,
                     L: int, dim: int = 5, ddof: int = 0,
                     hpf: bool = True, rmv_ttn: bool = True) -> Mapping[str, np.array]:
    """
    Calculate spatial variance, this function applies hpf
    EMVA 4.0: Eq 36

    Keyword Arguments:
        img (np.array): 2D array of pixel values
        ttn_var (float): total temporal noise from
                         image stack used to generate img
        L (int): size of image stack used to generate img
        dim (int): dim of hpf, must be odd
        ddof (int, 0): degree of freedom for variance calc

    Returns:
        temp (dict): total s2_y
                     row s2_y
                     col s2_y
                     pix s2_y
    """

    temp = {}

    # get spatial variance components
    vars = stats.noise_metrics(img=img,
                               L=L,
                               ttn_var=ttn_var,
                               ddof=ddof,
                               dim=dim,
                               rmv_ttn=rmv_ttn,
                               hpf=hpf)

    # calculate spatial variances and correct for hpf
    # and remove residual temp noise
    tot = vars['tot_var']
    col = vars['col_var']
    row = vars['row_var']
    pix = vars['pix_var']

    temp = {'total_s2_y': tot,
            'row_s2_y': row,
            'col_s2_y': col,
            'pix_s2_y': pix}

    return temp


def spectrogram(img: np.ndarray,
                prnu_spect: bool = False) -> Mapping[str, np.array]:
    """
    calcualte horizontal and vertical spectrogram from average image
    EMVA 4.0: Eq. 8.6

    Keyword Arguments:
        img (np.array): avgerage image to compute spectrogram on
        rotate (bool): if True then vertical spectrogram is returned
        prnu_spect (bool): if True then values are returned as percentage

    Returns:
        temp (dict): horizontal data
                     vertical data
                     cycles [periods/pixels]
    """

    temp_vert = {}
    temp_hor = {}
    temp = {}
    type_ = 'dsnu'

    # compute fft
    fft_hor = emva1288r.FFT1288(img, rotate=False, n=1)
    fft_vert = emva1288r.FFT1288(img, rotate=True, n=1)

    # compute power series and periods/pixel
    temp_hor = cycles(fft_hor)
    temp_vert = cycles(fft_vert)

    # case where we want power series in percentage
    if prnu_spect:
        type_ = 'prnu'
        mean = img.flatten().mean()
        temp_hor['power_spectrum'] = \
            (temp_hor['power_spectrum'] / mean) * 100
        temp_vert['power_spectrum'] = \
            (temp_vert['power_spectrum'] / mean) * 100

    # update key name for accumulated histogram
    temp_hor = {f'{type_}_{k}_horizontal': v for k, v in temp_hor.items()}
    temp_vert = {f'{type_}_{k}_vertical': v for k, v in temp_vert.items()}

    # combine result
    temp = {**temp_hor, **temp_vert}

    return temp


def spectrogram_stack(img_stack: np.ndarray,
                      prnu_spect: bool = False) -> Mapping[str, np.array]:
    """
    calcualte horizontal and vertical spectrogram from stack of images
    EMVA 4.0: Eq. 8.6

    Keyword Arguments:
        img_stack (np.array): stack of images
        prnu_spect (bool): if True then values are returned as percentage

    Returns:
        temp (dict): horizontal data
                     vertical data
                     horizontal cycles [periods/pixels]
                     vertical cycles [periods/pixels]
    """

    temp = {}

    # get average image
    img = stats.avg_img(img_stack)

    # calculate spectrogram
    temp = spectrogram(img, prnu_spect)

    return temp
