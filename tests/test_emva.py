__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


import numpy as np
import pandas as pd
from . import datasets
from . import image_generator
from characterization_ams.stats_engine import stats
from characterization_ams.emva import emva
import pathlib

# load synthetic dataset
data = pd.read_csv(pathlib.Path(datasets.__file__).parents[0]/'test_emva.csv')

# generate dsnu and prnu images
ped_start = 168
peds = np.linspace(168, 3800, 30)
# peds = [168, peds[peds.shape[0]//2]]
power = np.linspace(0, 10, 30)
rows = 100
cols = 100
pedestal = 168
n_images = 1000
images = []
temp = pd.DataFrame()
raw = pd.DataFrame()
for (idx, pp) in enumerate(peds):
    n_images = 1000
    rfpn = 105
    cfpn = 101
    ctn = 15
    rtn = 12
    ptn = 20 + np.sqrt(pp)
    pfpn = 95 + 0.08 * (pp - ped_start)

    tot_t = np.sqrt(ctn**2 + rtn**2 + ptn**2)
    tot_f = np.sqrt(rfpn**2 + pfpn**2 + cfpn**2)

    # fpn
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

    images.append(imgs)

# data structures
emva_summ = pd.DataFrame()
emva_data = pd.DataFrame()
emva_hist = pd.DataFrame()
global req_vals
req_vals = {}

# starting required metrics
wl = 550  # nm
texp = 16  # ms
power = data.Power
pixel_area = 0.95 * 0.95  # [um^2]
data.rename(columns={'tot_var_temp - dark_tot_var_temp':
                     'tot_var_temp-dark_tot_var_temp',
                     'mean - dark_mean':
                     'mean-dark_mean'}, inplace=True)
emva_data = data[['tot_var_temp',
                  'tot_var_temp-dark_tot_var_temp',
                  'mean-dark_mean']]

# get required parameters for all functions
req_vals['mean-dark_mean'] = emva_data['mean-dark_mean']
req_vals['tot_var_temp-dark_tot_var_temp'] = \
    emva_data['tot_var_temp-dark_tot_var_temp']
req_vals['tot_var_temp'] = emva_data['tot_var_temp']
req_vals['ttn_var'] = emva_data['tot_var_temp'].iloc[0]
req_vals['exp'] = data['Exposure [uW/cm^2*s]']
req_vals['dark_imgs'] = images[0]
req_vals['light_imgs'] = images[len(images)//2]
req_vals['dark_img'] = stats.avg_img(req_vals['dark_imgs'])
req_vals['light_img'] = stats.avg_img(req_vals['light_imgs'])
req_vals['img'] = req_vals['light_img'] - req_vals['dark_img']
req_vals['Qmax'] = 256
req_vals['L'] = len(images[0])
req_vals['light_ttn_var'] = \
    np.mean(stats.tot_var_img_stack(req_vals['light_imgs']))
req_vals['qe'] = 0.9


# system gain
def test_system_gain():
    """
    """
    global req_vals

    val_dict =\
        emva.system_gain(u_y=req_vals['mean-dark_mean'],
                         sig2_y=req_vals['tot_var_temp-dark_tot_var_temp'])

    sys_gain = val_dict['system_gain']
    emva_summ['system_gain'] = pd.Series(sys_gain)
    req_vals = {**req_vals, **val_dict}

    assert round(sys_gain, 1) == 1.6


# get photons
def test_get_photons():
    """
    """
    global req_vals

    val_dict = emva.get_photons(wl=wl,
                                texp=texp,
                                power=power,
                                pixel_area=pixel_area)

    photons = val_dict['u_p']
    req_vals = {**req_vals, **val_dict}

    assert round(photons.iloc[-1], 0) == 4006


def test_dark_temporal_noise():
    """
    """
    global req_vals

    val_dict = \
        emva.dark_temporal_noise(sig2_ydark=req_vals['ttn_var'],
                                 K=req_vals['system_gain'])

    dtn = val_dict['dark_temporal_noise_e']
    req_vals = {**req_vals, **val_dict}
    assert round(dtn, 1) == 23.7


def test_dsnu1288():
    """
    """
    global req_vals

    dsnu = emva.dsnu1288(dark_img=req_vals['dark_img'],
                         ttn_var=req_vals['ttn_var'],
                         L=req_vals['L'])

    req_vals['dsnu_tot'] = dsnu['total_dsnu']

    assert round(dsnu['total_dsnu'], 0) == 162
    assert round(dsnu['row_dsnu'], 0) == 94
    assert round(dsnu['col_dsnu'], 0) == 91
    assert round(dsnu['pix_dsnu'], 0) == 96


def test_dsnu1288_stack():
    """
    """
    # calculate dsnu1288
    dsnu = emva.dsnu1288_stack(img_stack=req_vals['dark_imgs'])

    assert round(dsnu['total_dsnu'], 0) == 162
    assert round(dsnu['row_dsnu'], 0) == 94
    assert round(dsnu['col_dsnu'], 0) == 91
    assert round(dsnu['pix_dsnu'], 0) == 96


def test_dynamic_range():
    """
    """
    global req_vals

    val_dict = \
        emva.dynamic_range(u_p=req_vals['u_p'],
                           sig2_y=req_vals['tot_var_temp-dark_tot_var_temp'],
                           sig2_ydark=req_vals['ttn_var'],
                           qe=req_vals['qe'],
                           K=req_vals['system_gain'])

    req_vals = {**req_vals, **val_dict}

    assert round(val_dict['dynamic_range_ratio'], 0) == 144


def test_get_electrons():
    """
    """
    global req_vals

    val_dict = emva.get_electrons(u_y=req_vals['mean-dark_mean'],
                                  K=req_vals['system_gain'])

    req_vals = {**req_vals, **val_dict}
    assert round(val_dict['u_e'].iloc[-1], 0) == 2261


def test_histogram1288():
    """
    """
    global req_vals
    black_level = False

    val_dict = emva.histogram1288(img=req_vals['img'],
                                  Qmax=req_vals['Qmax'],
                                  L=req_vals['L'],
                                  black_level=black_level)

    assert round(val_dict['prnu_values'].mean(), 0) == 36


def test_histogram1288_stack():
    """
    """
    black_level = True

    val_dict = emva.histogram1288_stack(img_stack=req_vals['dark_imgs'],
                                        Qmax=req_vals['Qmax'],
                                        black_level=black_level)

    assert round(val_dict['dsnu_values'].mean(), 0) >= 44\
        and round(val_dict['dsnu_values'].mean(), 0) <= 46


def test_linearity():
    """
    """
    global req_vals

    val_dict = \
        emva.linearity(mean_arr=req_vals['mean-dark_mean'],
                       exp_arr=req_vals['exp'],
                       ttn_arr=req_vals['tot_var_temp-dark_tot_var_temp'])

    assert round(val_dict['linearity_error_DN'].mean(), 0) == 0


def test_prnu1288():
    """
    """
    global req_vals

    val_dict = emva.prnu1288(dark_img=req_vals['dark_img'],
                             light_img=req_vals['light_img'],
                             dark_ttn_var=req_vals['ttn_var'],
                             light_ttn_var=req_vals['light_ttn_var'],
                             L=req_vals['L'])

    req_vals['prnu_tot'] = val_dict['tot_prnu1288_%']

    assert round(val_dict['tot_prnu1288_%'], 0) == 12


def test_prnu1288_stack():
    """
    """
    global req_vals

    val_dict = emva.prnu1288_stack(dark_stack=req_vals['dark_imgs'],
                                   light_stack=req_vals['light_imgs'])

    assert round(val_dict['tot_prnu1288_%'], 0) == 12


def test_profiles():
    """
    """
    global req_vals

    val_dict = emva.profiles(req_vals['dark_img'])

    assert round(val_dict['dsnu_mean_horizontal'].mean(), 0) == 184


def test_responsivity():
    """
    """
    global req_vals

    val_dict = \
        emva.responsivity(u_p=req_vals['u_p'],
                          u_y=req_vals['mean-dark_mean'],
                          sig2_y=req_vals['tot_var_temp-dark_tot_var_temp'])

    assert round(val_dict['responsivity'], 0) == 1


def test_saturation_capacity():
    """
    """
    global req_vals

    val_dict = \
        emva.saturation_capacity(u_p=req_vals['u_p'],
                                 sig2_y=req_vals[
                                    'tot_var_temp-dark_tot_var_temp'],
                                 qe=req_vals['qe'])

    assert round(val_dict['sat_capacity_e'], 0) == 3481


def test_sensitivity_threshold():
    """
    """
    global req_vals

    val_dict = emva.sensitivity_threshold(sig2_ydark=req_vals['ttn_var'],
                                          qe=req_vals['qe'],
                                          K=req_vals['system_gain'])

    assert round(val_dict['sensitivity_threshold_e'], 0) == 24


def test_snr():
    """
    """
    global req_vals

    val_dict = emva.snr(dsnu_tot=req_vals['dsnu_tot'],
                        prnu_tot=req_vals['prnu_tot'],
                        u_p=req_vals['u_p'],
                        s2_d=req_vals['dark_temporal_noise_e'],
                        K=req_vals['system_gain'],
                        qe=req_vals['qe'])

    assert round(val_dict['snr_ratio'].mean(), 0) >= 6\
        and round(val_dict['snr_ratio'].mean(), 0) <= 8


def test_snr_stack():
    """
    """
    global req_vals

    val_dict = emva.snr_stack(dark_stack=req_vals['dark_imgs'],
                              light_stack=req_vals['light_imgs'],
                              u_p=req_vals['u_p'],
                              s2_d=req_vals['dark_temporal_noise_e'],
                              K=req_vals['system_gain'],
                              qe=req_vals['qe'])

    assert round(val_dict['snr_ratio'].mean(), 0) >= 6\
        and round(val_dict['snr_ratio'].mean(), 0) <= 8


def test_snr_ideal():
    """
    """
    global req_vals

    val_dict = emva.snr_ideal(u_p=req_vals['u_p'])

    assert round(val_dict['snr_ideal_ratio'].mean(), 0) == 43


def test_snr_photons():
    """
    """
    global req_vals

    val_dict = emva.snr_photons(snr_level=10,
                                u_p=req_vals['u_p'],
                                s2_d=req_vals['dark_temporal_noise_e'],
                                K=req_vals['system_gain'],
                                qe=req_vals['qe'])

    assert round(val_dict['irradiance'], 0) == 133


def test_snr_theoretical():
    """
    """
    global req_vals

    val_dict = emva.snr_theoretical(u_p=req_vals['u_p'],
                                    s2_d=req_vals['dark_temporal_noise_e'],
                                    K=req_vals['system_gain'],
                                    qe=req_vals['qe'])

    assert round(val_dict['snr_theoretical_ratio'].mean(), 0) == 41


def test_spatial_variance():
    """
    """
    global req_vals

    val_dict = emva.spatial_variance(img=req_vals['dark_img'],
                                     ttn_var=req_vals['ttn_var'],
                                     L=req_vals['L'])

    assert round(np.sqrt(val_dict['total_s2_y']), 0) == 162


def test_spectrogram():
    """
    """
    global req_vals

    val_dict = emva.spectrogram(img=req_vals['dark_img'])

    assert round(val_dict['dsnu_power_spectrum_horizontal'].mean(), 0) == 150


def test_spectogram_stack():
    """
    """
    global req_vals

    val_dict = emva.spectrogram_stack(img_stack=req_vals['dark_imgs'])

    assert round(val_dict['dsnu_power_spectrum_horizontal'].mean(), 0) == 150
