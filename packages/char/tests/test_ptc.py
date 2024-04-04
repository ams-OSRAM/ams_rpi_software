__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


import pytest
import numpy as np
import pandas as pd
from . import image_generator
from characterization_ams.kpi_calcs import calculations as calcs
from characterization_ams.stats_engine import stats
from characterization_ams.utilities import utilities as ut
from characterization_ams.standard_tests import ptc
from characterization_ams.emva import emva


# generate images
ped_start = 168
peds = np.linspace(168, 3800, 30)
power = np.linspace(0, 10, 30)
rows = 100
cols = 100
tint = 16e-3
images = []
avg_images = []
temp_images = []
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

    ttn_var = stats.tot_var_img_stack(imgs, 1)
    avg = stats.avg_img(imgs)
    temp_images.append(ttn_var)
    avg_images.append(avg)


@pytest.fixture(scope='module')
def image_stats():
    return ptc.get_stats(images=images.copy(),
                         df=raw.copy(),
                         rename=False)['data']


@pytest.fixture(scope='module')
def image_stats_avg():
    return ptc.get_stats(images=avg_images.copy(),
                         df=raw.copy(),
                         temp_imgs=temp_images.copy(),
                         L=len(images[0]),
                         rename=False)['data']


@pytest.fixture(scope='module')
def image_stats_no_rmv_ttn():
    return ptc.get_stats(images=images.copy(),
                         df=raw.copy(),
                         rmv_ttn=False,
                         rename=False)['data']


@pytest.fixture(scope='module')
def emva_results(image_stats):
    # get required parameters for all functions
    req_vals = {}
    req_vals['mean'] = image_stats['mean']
    req_vals['mean-dark_mean'] = image_stats['mean_black_subtracted']
    req_vals['tot_var_temp-dark_tot_var_temp'] \
        = image_stats['tot_var_temp_black_subtracted']
    req_vals['tot_var_temp'] = image_stats['tot_var_temp']
    req_vals['ttn_var'] = image_stats['tot_var_temp'].iloc[0]
    req_vals['exp'] = image_stats['Exposure [uW/cm^2*s]']
    req_vals['dark_imgs'] = images[0]
    req_vals['dark_img'] = stats.avg_img(req_vals['dark_imgs'])
    req_vals['Qmax'] = 256
    req_vals['L'] = len(images[0])
    req_vals['qe'] = 1

    dark_avg_img, \
        half_sat_avg_img, \
        half_sat_idx = ut.get_half_sat_img(images=avg_images.copy(),
                                           data=image_stats.copy(),
                                           u_y=req_vals['mean-dark_mean'],
                                           image_idx_col='imageid')
    req_vals['dark_avg_img'] = dark_avg_img
    req_vals['half_sat_avg_img'] = half_sat_avg_img
    req_vals['dark_ttn_var'] = stats.avg_offset(temp_images[0])
    req_vals['half_sat_ttn_var'] = stats.avg_offset(temp_images[half_sat_idx])
    req_vals['prnu_img'] = \
        req_vals['half_sat_avg_img'] - req_vals['dark_avg_img']

    u_y = req_vals['mean'].values
    dark_idx = np.argmin(u_y)
    req_vals['tot_var_half'] = image_stats['tot_std'][half_sat_idx]**2
    req_vals['tot_var_half'] = image_stats['tot_std'][half_sat_idx]**2
    req_vals['pix_var_half'] = image_stats['pix_std'][half_sat_idx]**2
    req_vals['row_var_half'] = image_stats['row_std'][half_sat_idx]**2
    req_vals['col_var_half'] = image_stats['col_std'][half_sat_idx]**2
    req_vals['tot_var_dark'] = image_stats['tot_std'][dark_idx]**2
    req_vals['pix_var_dark'] = image_stats['pix_std'][dark_idx]**2
    req_vals['row_var_dark'] = image_stats['row_std'][dark_idx]**2
    req_vals['col_var_dark'] = image_stats['col_std'][dark_idx]**2

    # get emva function results
    emva_results = {}

    # system gain
    val_dict = \
        emva.system_gain(u_y=req_vals['mean-dark_mean'],
                         sig2_y=req_vals['tot_var_temp-dark_tot_var_temp'])
    emva_results['system_gain'] = val_dict['system_gain']
    req_vals['system_gain'] = emva_results['system_gain']

    # dark temporal noise
    val_dict = \
        emva.dark_temporal_noise(sig2_ydark=req_vals['ttn_var'],
                                 K=req_vals['system_gain'])
    emva_results['dark_temporal_noise_e'] = val_dict['dark_temporal_noise_e']

    # dsnu
    val_dict = emva.dsnu1288(dark_img=req_vals['dark_avg_img'],
                             ttn_var=req_vals['dark_ttn_var'],
                             L=req_vals['L'])
    emva_results['emva_dsnu1288'] = {'total_dsnu': val_dict['total_dsnu'],
                                     'row_dsnu': val_dict['row_dsnu'],
                                     'col_dsnu': val_dict['col_dsnu'],
                                     'pix_dsnu': val_dict['pix_dsnu']}

    dsnu_vals = {'total_dsnu': np.sqrt(req_vals['tot_var_dark']),
                 'pix_dsnu': np.sqrt(req_vals['pix_var_dark']),
                 'row_dsnu': np.sqrt(req_vals['row_var_dark']),
                 'col_dsnu': np.sqrt(req_vals['col_var_dark'])}
    emva_results['emva_dsnu1288_alt'] = dsnu_vals

    # electrons
    val_dict = emva.get_electrons(u_y=req_vals['mean-dark_mean'],
                                  K=req_vals['system_gain'])
    emva_results['u_e'] = val_dict['u_e']
    req_vals['u_e'] = emva_results['u_e']

    # dynamic range
    val_dict = emva.dynamic_range(u_p=req_vals['u_e'],
                                  sig2_y=req_vals[
                                    'tot_var_temp-dark_tot_var_temp'],
                                  sig2_ydark=req_vals['ttn_var'],
                                  qe=req_vals['qe'],
                                  K=req_vals['system_gain'])
    emva_results['dynamic_range_db'] = val_dict['dynamic_range_db']

    # histogram dsnu vals
    val_dict = emva.histogram1288(img=req_vals['dark_avg_img'],
                                  Qmax=req_vals['Qmax'],
                                  L=req_vals['L'],
                                  black_level=True)
    emva_results['dsnu_values'] = val_dict['dsnu_values']

    # dsnu prnu vals
    val_dict = emva.histogram1288(img=req_vals['prnu_img'],
                                  Qmax=req_vals['Qmax'],
                                  L=req_vals['L'],
                                  black_level=False)
    emva_results['prnu_values'] = val_dict['prnu_values']

    # linearity
    val_dict = emva.linearity(mean_arr=req_vals['mean-dark_mean'],
                              exp_arr=req_vals['exp'],
                              ttn_arr=req_vals[
                                'tot_var_temp-dark_tot_var_temp'])
    emva_results['linearity_error_DN'] = val_dict['linearity_error_DN']

    # prnu
    val_dict = emva.prnu1288(dark_img=req_vals['dark_avg_img'],
                             light_img=req_vals['half_sat_avg_img'],
                             dark_ttn_var=req_vals['dark_ttn_var'],
                             light_ttn_var=req_vals['half_sat_ttn_var'],
                             L=req_vals['L'])
    emva_results['emva_prnu1288'] = \
        {'tot_prnu1288_%': val_dict['tot_prnu1288_%'],
         'row_prnu1288_%': val_dict['row_prnu1288_%'],
         'col_prnu1288_%': val_dict['col_prnu1288_%'],
         'pix_prnu1288_%': val_dict['pix_prnu1288_%']}

    prnu_vals = {'tot_var_half': req_vals['tot_var_half'],
                 'pix_var_half': req_vals['pix_var_half'],
                 'row_var_half': req_vals['row_var_half'],
                 'col_var_half': req_vals['col_var_half'],
                 'tot_var_dark': req_vals['tot_var_dark'],
                 'pix_var_dark': req_vals['pix_var_dark'],
                 'row_var_dark': req_vals['row_var_dark'],
                 'col_var_dark': req_vals['col_var_dark'],
                 'u_y_dark': u_y[dark_idx],
                 'u_y_half': u_y[half_sat_idx]}
    emva_results['emva_prnu1288_alt'] = calcs.prnu1288(prnu_vals)

    # dsnu profiles
    val_dict = emva.profiles(img=req_vals['dark_avg_img'], dsnu=True)
    emva_results['dsnu_mean_horizontal'] = val_dict['dsnu_mean_horizontal']

    # prnu profiles
    val_dict = emva.profiles(img=req_vals['half_sat_avg_img'], dsnu=False)
    emva_results['prnu_mean_horizontal'] = val_dict['prnu_mean_horizontal']

    # responsivity
    val_dict = emva.responsivity(u_p=req_vals['exp'],
                                 u_y=req_vals['mean-dark_mean'],
                                 sig2_y=req_vals[
                                    'tot_var_temp-dark_tot_var_temp'])
    emva_results['responsivity'] = val_dict['responsivity']

    # sensitivity threshold
    val_dict = emva.sensitivity_threshold(sig2_ydark=req_vals['ttn_var'],
                                          qe=req_vals['qe'],
                                          K=req_vals['system_gain'])
    emva_results['sensitivity_threshold_e'] = \
        val_dict['sensitivity_threshold_e']

    # dsnu spectrogram
    val_dict = emva.spectrogram(img=req_vals['dark_avg_img'], prnu_spect=False)
    emva_results['dsnu_power_spectrum_horizontal'] = \
        val_dict['dsnu_power_spectrum_horizontal']

    # prnu spectrogram
    val_dict = emva.spectrogram(img=req_vals['prnu_img'], prnu_spect=True)
    emva_results['prnu_power_spectrum_horizontal'] = \
        val_dict['prnu_power_spectrum_horizontal']

    return emva_results


@pytest.fixture(scope='module')
def emva_results_avg(image_stats_avg):
    # get required parameters for all functions
    req_vals = {}
    req_vals['mean'] = image_stats_avg['mean']
    req_vals['mean-dark_mean'] = image_stats_avg['mean_black_subtracted']
    req_vals['tot_var_temp-dark_tot_var_temp'] \
        = image_stats_avg['tot_var_temp_black_subtracted']
    req_vals['tot_var_temp'] = image_stats_avg['tot_var_temp']
    req_vals['ttn_var'] = image_stats_avg['tot_var_temp'].iloc[0]
    req_vals['exp'] = image_stats_avg['Exposure [uW/cm^2*s]']
    req_vals['dark_imgs'] = images[0]
    req_vals['dark_img'] = stats.avg_img(req_vals['dark_imgs'])
    req_vals['Qmax'] = 256
    req_vals['L'] = len(images[0])
    req_vals['qe'] = 1

    dark_avg_img, \
        half_sat_avg_img, \
        half_sat_idx = ut.get_half_sat_img(images=avg_images.copy(),
                                           data=image_stats_avg.copy(),
                                           u_y=req_vals['mean-dark_mean'],
                                           image_idx_col='imageid')
    req_vals['dark_avg_img'] = dark_avg_img
    req_vals['half_sat_avg_img'] = half_sat_avg_img
    req_vals['dark_ttn_var'] = stats.avg_offset(temp_images[0])
    req_vals['half_sat_ttn_var'] = stats.avg_offset(temp_images[half_sat_idx])
    req_vals['prnu_img'] = \
        req_vals['half_sat_avg_img'] - req_vals['dark_avg_img']

    u_y = req_vals['mean'].values
    dark_idx = np.argmin(u_y)
    req_vals['tot_var_half'] = image_stats_avg['tot_std'][half_sat_idx]**2
    req_vals['tot_var_half'] = image_stats_avg['tot_std'][half_sat_idx]**2
    req_vals['pix_var_half'] = image_stats_avg['pix_std'][half_sat_idx]**2
    req_vals['row_var_half'] = image_stats_avg['row_std'][half_sat_idx]**2
    req_vals['col_var_half'] = image_stats_avg['col_std'][half_sat_idx]**2
    req_vals['tot_var_dark'] = image_stats_avg['tot_std'][dark_idx]**2
    req_vals['pix_var_dark'] = image_stats_avg['pix_std'][dark_idx]**2
    req_vals['row_var_dark'] = image_stats_avg['row_std'][dark_idx]**2
    req_vals['col_var_dark'] = image_stats_avg['col_std'][dark_idx]**2

    # get emva function results
    emva_results = {}

    # system gain
    val_dict = \
        emva.system_gain(u_y=req_vals['mean-dark_mean'],
                         sig2_y=req_vals['tot_var_temp-dark_tot_var_temp'])
    emva_results['system_gain'] = val_dict['system_gain']
    req_vals['system_gain'] = emva_results['system_gain']

    # dark temporal noise
    val_dict = \
        emva.dark_temporal_noise(sig2_ydark=req_vals['ttn_var'],
                                 K=req_vals['system_gain'])
    emva_results['dark_temporal_noise_e'] = val_dict['dark_temporal_noise_e']

    # dsnu
    val_dict = emva.dsnu1288(dark_img=req_vals['dark_avg_img'],
                             ttn_var=req_vals['dark_ttn_var'],
                             L=req_vals['L'])
    emva_results['emva_dsnu1288'] = {'total_dsnu': val_dict['total_dsnu'],
                                     'row_dsnu': val_dict['row_dsnu'],
                                     'col_dsnu': val_dict['col_dsnu'],
                                     'pix_dsnu': val_dict['pix_dsnu']}

    dsnu_vals = {'total_dsnu': np.sqrt(req_vals['tot_var_dark']),
                 'pix_dsnu': np.sqrt(req_vals['pix_var_dark']),
                 'row_dsnu': np.sqrt(req_vals['row_var_dark']),
                 'col_dsnu': np.sqrt(req_vals['col_var_dark'])}
    emva_results['emva_dsnu1288_alt'] = dsnu_vals

    # electrons
    val_dict = emva.get_electrons(u_y=req_vals['mean-dark_mean'],
                                  K=req_vals['system_gain'])
    emva_results['u_e'] = val_dict['u_e']
    req_vals['u_e'] = emva_results['u_e']

    # dynamic range
    val_dict = emva.dynamic_range(u_p=req_vals['u_e'],
                                  sig2_y=req_vals[
                                    'tot_var_temp-dark_tot_var_temp'],
                                  sig2_ydark=req_vals['ttn_var'],
                                  qe=req_vals['qe'],
                                  K=req_vals['system_gain'])
    emva_results['dynamic_range_db'] = val_dict['dynamic_range_db']

    # histogram dsnu vals
    val_dict = emva.histogram1288(img=req_vals['dark_avg_img'],
                                  Qmax=req_vals['Qmax'],
                                  L=req_vals['L'],
                                  black_level=True)
    emva_results['dsnu_values'] = val_dict['dsnu_values']

    # dsnu prnu vals
    val_dict = emva.histogram1288(img=req_vals['prnu_img'],
                                  Qmax=req_vals['Qmax'],
                                  L=req_vals['L'],
                                  black_level=False)
    emva_results['prnu_values'] = val_dict['prnu_values']

    # linearity
    val_dict = emva.linearity(mean_arr=req_vals['mean-dark_mean'],
                              exp_arr=req_vals['exp'],
                              ttn_arr=req_vals[
                                'tot_var_temp-dark_tot_var_temp'])
    emva_results['linearity_error_DN'] = val_dict['linearity_error_DN']

    # prnu
    val_dict = emva.prnu1288(dark_img=req_vals['dark_avg_img'],
                             light_img=req_vals['half_sat_avg_img'],
                             dark_ttn_var=req_vals['dark_ttn_var'],
                             light_ttn_var=req_vals['half_sat_ttn_var'],
                             L=req_vals['L'])
    emva_results['emva_prnu1288'] = \
        {'tot_prnu1288_%': val_dict['tot_prnu1288_%'],
         'row_prnu1288_%': val_dict['row_prnu1288_%'],
         'col_prnu1288_%': val_dict['col_prnu1288_%'],
         'pix_prnu1288_%': val_dict['pix_prnu1288_%']}

    prnu_vals = {'tot_var_half': req_vals['tot_var_half'],
                 'pix_var_half': req_vals['pix_var_half'],
                 'row_var_half': req_vals['row_var_half'],
                 'col_var_half': req_vals['col_var_half'],
                 'tot_var_dark': req_vals['tot_var_dark'],
                 'pix_var_dark': req_vals['pix_var_dark'],
                 'row_var_dark': req_vals['row_var_dark'],
                 'col_var_dark': req_vals['col_var_dark'],
                 'u_y_dark': u_y[dark_idx],
                 'u_y_half': u_y[half_sat_idx]}
    emva_results['emva_prnu1288_alt'] = calcs.prnu1288(prnu_vals)

    # dsnu profiles
    val_dict = emva.profiles(img=req_vals['dark_avg_img'], dsnu=True)
    emva_results['dsnu_mean_horizontal'] = val_dict['dsnu_mean_horizontal']

    # prnu profiles
    val_dict = emva.profiles(img=req_vals['half_sat_avg_img'], dsnu=False)
    emva_results['prnu_mean_horizontal'] = val_dict['prnu_mean_horizontal']

    # responsivity
    val_dict = emva.responsivity(u_p=req_vals['exp'],
                                 u_y=req_vals['mean-dark_mean'],
                                 sig2_y=req_vals[
                                    'tot_var_temp-dark_tot_var_temp'])
    emva_results['responsivity'] = val_dict['responsivity']

    # sensitivity threshold
    val_dict = emva.sensitivity_threshold(sig2_ydark=req_vals['ttn_var'],
                                          qe=req_vals['qe'],
                                          K=req_vals['system_gain'])
    emva_results['sensitivity_threshold_e'] = \
        val_dict['sensitivity_threshold_e']

    # dsnu spectrogram
    val_dict = emva.spectrogram(img=req_vals['dark_avg_img'], prnu_spect=False)
    emva_results['dsnu_power_spectrum_horizontal'] = \
        val_dict['dsnu_power_spectrum_horizontal']

    # prnu spectrogram
    val_dict = emva.spectrogram(img=req_vals['prnu_img'], prnu_spect=True)
    emva_results['prnu_power_spectrum_horizontal'] = \
        val_dict['prnu_power_spectrum_horizontal']

    return emva_results


@pytest.fixture(scope='module')
def ptc_image_stack_list():
    res = ptc.ptc(img_stack_list=images.copy(),
                  df=raw.copy())

    res['data'] = ut.rename(res['data'], revert=True)
    res['summ'] = ut.rename(res['summ'], revert=True)
    res['hist'] = ut.rename(res['hist'], revert=True)
    res['summ_hpf'] = ut.rename(res['summ_hpf'], revert=True)

    return res


@pytest.fixture(scope='module')
def ptc_image_stack_list_hpf():
    res = ptc.ptc(img_stack_list=images.copy(),
                  df=raw.copy(),
                  hpf=True)

    res['data'] = ut.rename(res['data'], revert=True)
    res['summ'] = ut.rename(res['summ'], revert=True)
    res['hist'] = ut.rename(res['hist'], revert=True)

    return res


@pytest.fixture(scope='module')
def ptc_image_stack_list_no_rmv_ttn():
    res = ptc.ptc(img_stack_list=images.copy(),
                  df=raw.copy(),
                  rmv_ttn=False)

    res['data'] = ut.rename(res['data'], revert=True)
    res['summ'] = ut.rename(res['summ'], revert=True)
    res['hist'] = ut.rename(res['hist'], revert=True)
    res['summ_hpf'] = ut.rename(res['summ_hpf'], revert=True)

    return res


@pytest.fixture(scope='module')
def ptc_avg_image_list():
    res = ptc.ptc_avg(img_list=avg_images.copy(),
                      temp_imgs=temp_images.copy(),
                      df=raw.copy(),
                      L=len(images[0]))

    res['data'] = ut.rename(res['data'], revert=True)
    res['summ'] = ut.rename(res['summ'], revert=True)
    res['hist'] = ut.rename(res['hist'], revert=True)
    res['summ_hpf'] = ut.rename(res['summ_hpf'], revert=True)

    return res


@pytest.fixture(scope='module')
def ptc_avg_dark_stack():
    avg_img_cp = avg_images.copy()
    avg_img_cp.pop(0)
    temp_img_cp = temp_images.copy()
    temp_img_cp.pop(0)

    res = ptc.ptc_avg(img_list=avg_img_cp,
                      temp_imgs=temp_img_cp,
                      df=raw.copy(),
                      L=len(images[0]),
                      dark_imgs=images.copy()[0])

    res['data'] = ut.rename(res['data'], revert=True)
    res['summ'] = ut.rename(res['summ'], revert=True)
    res['hist'] = ut.rename(res['hist'], revert=True)
    res['summ_hpf'] = ut.rename(res['summ_hpf'], revert=True)

    return res


def test_ptc_image_stack_list_system_gain(ptc_image_stack_list, emva_results):
    ptc_sys_gain = ptc_image_stack_list['summ'].system_gain[0]
    emva_sys_gain = emva_results['system_gain']

    assert round(ptc_sys_gain, 7) == round(emva_sys_gain, 7)


def test_ptc_image_stack_list_dark_temporal_noise(ptc_image_stack_list,
                                                  emva_results):
    emva_dtn = emva_results['dark_temporal_noise_e']
    ptc_dtn = ptc_image_stack_list['summ'].dark_temporal_noise_e[0]

    assert round(ptc_dtn, 7) == round(emva_dtn, 7)


def test_ptc_image_stack_list_dsnu1288(ptc_image_stack_list, emva_results):
    emva_dsnu = emva_results['emva_dsnu1288']
    emva_dsnu_no_hpf = emva_results['emva_dsnu1288_alt']
    summ = ptc_image_stack_list['summ']
    summ_hpf = ptc_image_stack_list['summ_hpf']

    assert round(summ.total_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['total_dsnu'], 4)
    assert round(summ.row_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['row_dsnu'], 4)
    assert round(summ.col_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['col_dsnu'], 4)
    assert round(summ.pix_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['pix_dsnu'], 4)

    assert round(summ_hpf.total_dsnu[0], 4) == \
        round(emva_dsnu['total_dsnu'], 4)
    assert round(summ_hpf.row_dsnu[0], 4) == round(emva_dsnu['row_dsnu'], 4)
    assert round(summ_hpf.col_dsnu[0], 4) == round(emva_dsnu['col_dsnu'], 4)
    assert round(summ_hpf.pix_dsnu[0], 4) == round(emva_dsnu['pix_dsnu'], 4)


def test_ptc_image_stack_list_get_electrons(ptc_image_stack_list,
                                            emva_results):
    emva_e = emva_results['u_e'].mean()
    ptc_e = ptc_image_stack_list['data'].mean_e.mean()

    assert round(ptc_e, 7) == round(emva_e, 7)


def test_ptc_image_stack_list_dynamic_range(ptc_image_stack_list,
                                            emva_results):
    emva_dr = emva_results['dynamic_range_db']
    ptc_dr = ptc_image_stack_list['summ'].dynamic_range_db[0]

    assert round(ptc_dr, 7) == round(emva_dr, 7)


def test_ptc_image_stack_list_histogram1288_dsnu(ptc_image_stack_list,
                                                 emva_results):
    emva_hist = emva_results['dsnu_values'].mean()
    ptc_hist = ptc_image_stack_list['hist'].dsnu_values.mean()

    assert ptc_hist == emva_hist


def test_ptc_image_stack_list_histogram1288_prnu(ptc_image_stack_list,
                                                 emva_results):
    emva_hist = emva_results['prnu_values'].mean()
    ptc_hist = ptc_image_stack_list['hist'].prnu_values.mean()

    assert ptc_hist == emva_hist


def test_ptc_image_stack_list_linearity(ptc_image_stack_list,
                                        emva_results):
    emva_lin_mean = emva_results['linearity_error_DN'].mean()
    ptc_lin_mean = ptc_image_stack_list['data'].linearity_error_DN.mean()

    assert round(ptc_lin_mean, 7) == round(emva_lin_mean, 7)


def test_ptc_image_stack_list_prnu1288(ptc_image_stack_list, emva_results):
    summ = ptc_image_stack_list['summ']
    summ_hpf = ptc_image_stack_list['summ_hpf']
    emva_prnu1288 = emva_results['emva_prnu1288']
    emva_prnu1288_no_hpf = emva_results['emva_prnu1288_alt']

    assert round(summ['tot_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['tot_prnu1288_%'], 4)
    # assert round(summ['row_prnu1288_%'][0], 5) == \
    #     round(emva_prnu1288_no_hpf['row_prnu1288_%'], 5)
    assert round(summ['col_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['col_prnu1288_%'], 4)
    assert round(summ['pix_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['pix_prnu1288_%'], 4)

    assert round(summ_hpf['tot_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['tot_prnu1288_%'], 4)
    # assert round(summ_hpf['row_prnu1288_%'][0], 5) == \
    #     round(emva_prnu1288['row_prnu1288_%'], 5)
    assert round(summ_hpf['col_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['col_prnu1288_%'], 4)
    assert round(summ_hpf['pix_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['pix_prnu1288_%'], 4)


def test_ptc_image_stack_list_profiles_dsnu(ptc_image_stack_list,
                                            emva_results):
    emva_prof = emva_results['dsnu_mean_horizontal'].mean()
    ptc_prof = ptc_image_stack_list['hist'].dsnu_mean_horizontal.mean()

    assert round(ptc_prof, 7) == round(emva_prof, 7)


def test_ptc_image_stack_list_profiles_prnu(ptc_image_stack_list,
                                            emva_results):
    emva_prof = emva_results['prnu_mean_horizontal'].mean()
    ptc_prof = ptc_image_stack_list['hist'].prnu_mean_horizontal.mean()

    assert round(ptc_prof, 7) == round(emva_prof, 7)


def test_ptc_image_stack_list_responsivity(ptc_image_stack_list, emva_results):
    emva_resp = emva_results['responsivity']
    ptc_resp = ptc_image_stack_list['summ']['Responsivity [DN/(uW/cm^2)]'][0]

    assert ptc_resp == emva_resp


def test_ptc_image_stack_list_saturation_capacity(ptc_image_stack_list,
                                                  image_stats):
    u_p = ptc_image_stack_list['data'].mean_e
    sig2_y = image_stats['tot_var_temp_black_subtracted']

    val_dict = emva.saturation_capacity(u_p=u_p,
                                        sig2_y=sig2_y,
                                        qe=1)

    emva_sat = val_dict['sat_capacity_e']
    ptc_sat = ptc_image_stack_list['summ'].sat_capacity_e[0]

    assert ptc_sat == emva_sat


def test_ptc_image_stack_list_sensitivity_threshold(ptc_image_stack_list,
                                                    emva_results):
    emva_sen = emva_results['sensitivity_threshold_e']
    ptc_sen = ptc_image_stack_list['summ'].sensitivity_threshold_e[0]

    assert round(ptc_sen, 7) == round(emva_sen, 7)


def test_ptc_image_stack_list_snr(ptc_image_stack_list, emva_results):
    u_p = ptc_image_stack_list['data'].mean_e
    prnu_tot = emva_results['emva_prnu1288_alt']['tot_prnu1288_%']
    dsnu_tot = emva_results['emva_dsnu1288_alt']['total_dsnu']
    val_dict = emva.snr(dsnu_tot=dsnu_tot,
                        prnu_tot=prnu_tot,
                        u_p=u_p,
                        s2_d=emva_results['dark_temporal_noise_e'],
                        K=emva_results['system_gain'],
                        qe=1)

    emva_snr = val_dict['snr_ratio'].mean()
    ptc_snr = ptc_image_stack_list['data'].snr_ratio.mean()

    assert round(ptc_snr, 5) == round(emva_snr, 5)


def test_ptc_image_stack_list_snr_ideal(ptc_image_stack_list):
    u_p = ptc_image_stack_list['data'].mean_e
    val_dict = emva.snr_ideal(u_p=u_p)

    emva_snr = val_dict['snr_ideal_ratio'].mean()
    ptc_snr = ptc_image_stack_list['data'].snr_ideal_ratio.mean()

    assert ptc_snr == emva_snr


def test_ptc_image_stack_list_snr_theoretical(ptc_image_stack_list,
                                              emva_results):
    u_p = ptc_image_stack_list['data'].mean_e
    val_dict = emva.snr_theoretical(u_p=u_p,
                                    s2_d=emva_results['dark_temporal_noise_e'],
                                    K=emva_results['system_gain'],
                                    qe=1)

    emva_snr = val_dict['snr_theoretical_ratio'].mean()
    ptc_snr = ptc_image_stack_list['data'].snr_theoretical_ratio.mean()

    assert ptc_snr == emva_snr


def test_ptc_image_stack_list_spectrogram_dsnu(ptc_image_stack_list,
                                               emva_results):
    emva_spect = emva_results['dsnu_power_spectrum_horizontal'].mean()
    ptc_spect = \
        ptc_image_stack_list['hist'].dsnu_power_spectrum_horizontal.mean()

    assert round(ptc_spect, 7) == round(emva_spect, 7)


def test_ptc_image_stack_list_spectrogram_prnu(ptc_image_stack_list,
                                               emva_results):
    emva_spect = emva_results['prnu_power_spectrum_horizontal'].mean()
    ptc_spect = \
        ptc_image_stack_list['hist'].prnu_power_spectrum_horizontal.mean()

    assert round(ptc_spect, 7) == round(emva_spect, 7)


def test_ptc_image_stack_list_hpf(ptc_image_stack_list_hpf, emva_results):
    summ = ptc_image_stack_list_hpf['summ']
    emva_prnu1288 = emva_results['emva_prnu1288']
    emva_dsnu1288 = emva_results['emva_dsnu1288']

    assert round(summ.total_dsnu_DN[0], 7) == \
        round(emva_dsnu1288['total_dsnu'], 7)
    assert round(summ.row_dsnu_DN[0], 7) == \
        round(emva_dsnu1288['row_dsnu'], 7)
    assert round(summ.col_dsnu_DN[0], 7) == round(emva_dsnu1288['col_dsnu'], 7)
    assert round(summ.pix_dsnu_DN[0], 7) == round(emva_dsnu1288['pix_dsnu'], 7)

    assert round(summ['tot_prnu1288_%'][0], 7) == \
        round(emva_prnu1288['tot_prnu1288_%'], 7)
    # assert round(summ['row_prnu1288_%'][0], 7) == \
    #     round(emva_prnu1288['row_prnu1288_%'], 7)
    assert round(summ['col_prnu1288_%'][0], 7) == \
        round(emva_prnu1288['col_prnu1288_%'], 7)
    assert round(summ['pix_prnu1288_%'][0], 7) == \
        round(emva_prnu1288['pix_prnu1288_%'], 7)


def test_ptc_image_stack_list_no_rmv_ttn(ptc_image_stack_list_no_rmv_ttn,
                                         image_stats_no_rmv_ttn):
    data = ptc_image_stack_list_no_rmv_ttn['data']

    assert data.tot_var.mean() == image_stats_no_rmv_ttn.tot_var.mean()
    assert data.row_var.mean() == image_stats_no_rmv_ttn.row_var.mean()
    assert data.col_var.mean() == image_stats_no_rmv_ttn.col_var.mean()
    assert data.pix_var.mean() == image_stats_no_rmv_ttn.pix_var.mean()


def test_ptc_avg_image_list_system_gain(ptc_avg_image_list, emva_results_avg):
    emva_sys_gain = emva_results_avg['system_gain']
    ptc_sys_gain = ptc_avg_image_list['summ'].system_gain[0]

    assert round(ptc_sys_gain, 7) == round(emva_sys_gain, 7)


def test_ptc_avg_image_list_dark_temporal_noise(ptc_avg_image_list,
                                                emva_results_avg):
    emva_dtn = emva_results_avg['dark_temporal_noise_e']
    ptc_dtn = ptc_avg_image_list['summ'].dark_temporal_noise_e[0]

    assert round(ptc_dtn, 7) == round(emva_dtn, 7)


def test_ptc_avg_image_list_dsnu1288(ptc_avg_image_list, emva_results_avg):
    emva_dsnu = emva_results_avg['emva_dsnu1288']
    emva_dsnu_no_hpf = emva_results_avg['emva_dsnu1288_alt']
    summ = ptc_avg_image_list['summ']
    summ_hpf = ptc_avg_image_list['summ_hpf']

    assert round(summ.total_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['total_dsnu'], 4)
    assert round(summ.row_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['row_dsnu'], 4)
    assert round(summ.col_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['col_dsnu'], 4)
    assert round(summ.pix_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['pix_dsnu'], 4)

    assert round(summ_hpf.total_dsnu[0], 4) == \
        round(emva_dsnu['total_dsnu'], 4)
    assert round(summ_hpf.row_dsnu[0], 4) == round(emva_dsnu['row_dsnu'], 4)
    assert round(summ_hpf.col_dsnu[0], 4) == round(emva_dsnu['col_dsnu'], 4)
    assert round(summ_hpf.pix_dsnu[0], 4) == round(emva_dsnu['pix_dsnu'], 4)


def test_ptc_avg_image_list_get_electrons(ptc_avg_image_list,
                                          emva_results_avg):
    emva_e = emva_results_avg['u_e'].iloc[-1]
    ptc_e = ptc_avg_image_list['data'].mean_e.iloc[-1]

    assert round(ptc_e, 7) == round(emva_e, 7)


def test_ptc_avg_image_list_dynamic_range(ptc_avg_image_list,
                                          emva_results_avg):
    emva_dr = emva_results_avg['dynamic_range_db']
    ptc_dr = ptc_avg_image_list['summ'].dynamic_range_db[0]

    assert round(ptc_dr, 7) == round(emva_dr, 7)


def test_ptc_avg_image_list_histogram1288_dsnu(ptc_avg_image_list,
                                               emva_results_avg):
    emva_hist = emva_results_avg['dsnu_values'].mean()
    ptc_hist = ptc_avg_image_list['hist'].dsnu_values.mean()

    assert ptc_hist == emva_hist


def test_ptc_avg_image_list_histogram1288_prnu(ptc_avg_image_list,
                                               emva_results_avg):
    emva_hist = emva_results_avg['prnu_values'].mean()
    ptc_hist = ptc_avg_image_list['hist'].prnu_values.mean()

    assert ptc_hist == emva_hist


def test_ptc_avg_image_list_linearity(ptc_avg_image_list,
                                      emva_results_avg):
    emva_lin_mean = emva_results_avg['linearity_error_DN'].mean()
    ptc_lin_mean = ptc_avg_image_list['data'].linearity_error_DN.mean()

    assert round(ptc_lin_mean, 7) == round(emva_lin_mean, 7)


def test_ptc_avg_image_list_prnu1288(ptc_avg_image_list, emva_results_avg):
    summ = ptc_avg_image_list['summ']
    summ_hpf = ptc_avg_image_list['summ_hpf']
    emva_prnu1288 = emva_results_avg['emva_prnu1288']
    emva_prnu1288_no_hpf = emva_results_avg['emva_prnu1288_alt']

    assert round(summ['tot_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['tot_prnu1288_%'], 4)
    # assert round(summ['row_prnu1288_%'][0], 5) == \
    #     round(emva_prnu1288_no_hpf['row_prnu1288_%'], 5)
    assert round(summ['col_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['col_prnu1288_%'], 4)
    assert round(summ['pix_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['pix_prnu1288_%'], 4)

    assert round(summ_hpf['tot_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['tot_prnu1288_%'], 4)
    # assert round(summ_hpf['row_prnu1288_%'][0], 5) == \
    #     round(emva_prnu1288['row_prnu1288_%'], 5)
    assert round(summ_hpf['col_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['col_prnu1288_%'], 4)
    assert round(summ_hpf['pix_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['pix_prnu1288_%'], 4)


def test_ptc_avg_image_list_profiles_dsnu(ptc_avg_image_list,
                                          emva_results_avg):
    emva_prof = emva_results_avg['dsnu_mean_horizontal'].mean()
    ptc_prof = ptc_avg_image_list['hist'].dsnu_mean_horizontal.mean()

    assert round(ptc_prof, 7) == round(emva_prof, 7)


def test_ptc_avg_image_list_profiles_prnu(ptc_avg_image_list,
                                          emva_results_avg):
    emva_prof = emva_results_avg['prnu_mean_horizontal'].mean()
    ptc_prof = ptc_avg_image_list['hist'].prnu_mean_horizontal.mean()

    assert round(ptc_prof, 7) == round(emva_prof, 7)


def test_ptc_avg_image_list_responsivity(ptc_avg_image_list, emva_results_avg):
    emva_resp = emva_results_avg['responsivity']
    ptc_resp = ptc_avg_image_list['summ']['Responsivity [DN/(uW/cm^2)]'][0]

    assert round(ptc_resp, 7) == round(emva_resp, 7)


def test_ptc_avg_image_list_saturation_capacity(ptc_avg_image_list,
                                                image_stats_avg):
    u_p = ptc_avg_image_list['data'].mean_e
    sig2_y = image_stats_avg['tot_var_temp_black_subtracted']

    val_dict = emva.saturation_capacity(u_p=u_p,
                                        sig2_y=sig2_y,
                                        qe=1)

    emva_sat = val_dict['sat_capacity_e']
    ptc_sat = ptc_avg_image_list['summ'].sat_capacity_e[0]

    assert ptc_sat == emva_sat


def test_ptc_avg_image_list_sensitivity_threshold(ptc_avg_image_list,
                                                  emva_results_avg):
    emva_sen = emva_results_avg['sensitivity_threshold_e']
    ptc_sen = ptc_avg_image_list['summ'].sensitivity_threshold_e[0]

    assert round(ptc_sen, 7) == round(emva_sen, 7)


def test_ptc_avg_image_list_snr(ptc_avg_image_list, emva_results_avg):
    u_p = ptc_avg_image_list['data'].mean_e
    prnu_tot = emva_results_avg['emva_prnu1288_alt']['tot_prnu1288_%']
    dsnu_tot = emva_results_avg['emva_dsnu1288_alt']['total_dsnu']
    val_dict = emva.snr(dsnu_tot=dsnu_tot,
                        prnu_tot=prnu_tot,
                        u_p=u_p,
                        s2_d=emva_results_avg['dark_temporal_noise_e'],
                        K=emva_results_avg['system_gain'],
                        qe=1)

    emva_snr = val_dict['snr_ratio'].mean()
    ptc_snr = ptc_avg_image_list['data'].snr_ratio.mean()

    assert round(ptc_snr, 7) == round(emva_snr, 7)


def test_ptc_avg_image_list_snr_ideal(ptc_avg_image_list):
    val_dict = emva.snr_ideal(u_p=ptc_avg_image_list['data'].mean_e)

    emva_snr = val_dict['snr_ideal_ratio'].mean()
    ptc_snr = ptc_avg_image_list['data'].snr_ideal_ratio.mean()

    assert ptc_snr == emva_snr


def test_ptc_avg_image_list_snr_theoretical(ptc_avg_image_list,
                                            emva_results_avg):
    u_p = ptc_avg_image_list['data'].mean_e
    val_dict = \
        emva.snr_theoretical(u_p=u_p,
                             s2_d=emva_results_avg['dark_temporal_noise_e'],
                             K=emva_results_avg['system_gain'],
                             qe=1)

    emva_snr = val_dict['snr_theoretical_ratio'].mean()
    ptc_snr = ptc_avg_image_list['data'].snr_theoretical_ratio.mean()

    assert round(ptc_snr, 7) == round(emva_snr, 7)


def test_ptc_avg_image_list_spectrogram_dsnu(ptc_avg_image_list,
                                             emva_results_avg):
    emva_spect = emva_results_avg['dsnu_power_spectrum_horizontal'].mean()
    ptc_spect = \
        ptc_avg_image_list['hist'].dsnu_power_spectrum_horizontal.mean()

    assert round(ptc_spect, 7) == round(emva_spect, 7)


def test_ptc_avg_image_list_spectrogram_prnu(ptc_avg_image_list,
                                             emva_results_avg):
    emva_spect = emva_results_avg['prnu_power_spectrum_horizontal'].mean()
    ptc_spect = \
        ptc_avg_image_list['hist'].prnu_power_spectrum_horizontal.mean()

    assert round(ptc_spect, 7) == round(emva_spect, 7)


def test_ptc_avg_dark_stack_system_gain(ptc_avg_dark_stack, emva_results_avg):
    emva_sys_gain = emva_results_avg['system_gain']
    ptc_sys_gain = ptc_avg_dark_stack['summ'].system_gain[0]

    assert round(ptc_sys_gain, 7) == round(emva_sys_gain, 7)


def test_ptc_avg_dark_stack_dark_temporal_noise(ptc_avg_dark_stack,
                                                emva_results_avg):
    emva_dtn = emva_results_avg['dark_temporal_noise_e']
    ptc_dtn = ptc_avg_dark_stack['summ'].dark_temporal_noise_e[0]

    assert round(ptc_dtn, 7) == round(emva_dtn, 7)


def test_ptc_avg_dark_stack_dsnu1288(ptc_avg_dark_stack, emva_results_avg):
    emva_dsnu = emva_results_avg['emva_dsnu1288']
    emva_dsnu_no_hpf = emva_results_avg['emva_dsnu1288_alt']
    summ = ptc_avg_dark_stack['summ']
    summ_hpf = ptc_avg_dark_stack['summ_hpf']

    assert round(summ.total_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['total_dsnu'], 4)
    assert round(summ.row_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['row_dsnu'], 4)
    assert round(summ.col_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['col_dsnu'], 4)
    assert round(summ.pix_dsnu_DN[0], 4) == \
        round(emva_dsnu_no_hpf['pix_dsnu'], 4)

    assert round(summ_hpf.total_dsnu[0], 4) == \
        round(emva_dsnu['total_dsnu'], 4)
    assert round(summ_hpf.row_dsnu[0], 4) == round(emva_dsnu['row_dsnu'], 4)
    assert round(summ_hpf.col_dsnu[0], 4) == round(emva_dsnu['col_dsnu'], 4)
    assert round(summ_hpf.pix_dsnu[0], 4) == round(emva_dsnu['pix_dsnu'], 4)


def test_ptc_avg_dark_stack_get_electrons(ptc_avg_dark_stack,
                                          emva_results_avg):
    emva_e = emva_results_avg['u_e'].iloc[-1]
    ptc_e = ptc_avg_dark_stack['data'].mean_e.iloc[-1]

    assert round(ptc_e, 7) == round(emva_e, 7)


def test_ptc_avg_dark_stack_dynamic_range(ptc_avg_dark_stack,
                                          emva_results_avg):
    emva_dr = emva_results_avg['dynamic_range_db']
    ptc_dr = ptc_avg_dark_stack['summ'].dynamic_range_db[0]

    assert round(ptc_dr, 7) == round(emva_dr, 7)


def test_ptc_avg_dark_stack_histogram1288_dsnu(ptc_avg_dark_stack,
                                               emva_results_avg):
    emva_hist = emva_results_avg['dsnu_values'].mean()
    ptc_hist = ptc_avg_dark_stack['hist'].dsnu_values.mean()

    assert ptc_hist == emva_hist


def test_ptc_avg_dark_stack_histogram1288_prnu(ptc_avg_dark_stack,
                                               emva_results_avg):
    emva_hist = emva_results_avg['prnu_values'].mean()
    ptc_hist = ptc_avg_dark_stack['hist'].prnu_values.mean()

    assert ptc_hist == emva_hist


def test_ptc_avg_dark_stack_linearity(ptc_avg_dark_stack,
                                      emva_results_avg):
    emva_lin_mean = emva_results_avg['linearity_error_DN'].mean()
    ptc_lin_mean = ptc_avg_dark_stack['data'].linearity_error_DN.mean()

    assert round(ptc_lin_mean, 7) == round(emva_lin_mean, 7)


def test_ptc_avg_dark_stack_prnu1288(ptc_avg_dark_stack,
                                     emva_results_avg):
    summ = ptc_avg_dark_stack['summ']
    summ_hpf = ptc_avg_dark_stack['summ_hpf']
    emva_prnu1288 = emva_results_avg['emva_prnu1288']
    emva_prnu1288_no_hpf = emva_results_avg['emva_prnu1288_alt']

    assert round(summ['tot_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['tot_prnu1288_%'], 4)
    # assert round(summ['row_prnu1288_%'][0], 5) == \
    #     round(emva_prnu1288_no_hpf['row_prnu1288_%'], 5)
    assert round(summ['col_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['col_prnu1288_%'], 4)
    assert round(summ['pix_prnu1288_%'][0], 4) == \
        round(emva_prnu1288_no_hpf['pix_prnu1288_%'], 4)

    assert round(summ_hpf['tot_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['tot_prnu1288_%'], 4)
    # assert round(summ_hpf['row_prnu1288_%'][0], 5) == \
    #     round(emva_prnu1288['row_prnu1288_%'], 5)
    assert round(summ_hpf['col_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['col_prnu1288_%'], 4)
    assert round(summ_hpf['pix_prnu1288_%'][0], 4) == \
        round(emva_prnu1288['pix_prnu1288_%'], 4)


def test_ptc_avg_dark_stack_profiles_dsnu(ptc_avg_dark_stack,
                                          emva_results_avg):
    emva_prof = emva_results_avg['dsnu_mean_horizontal'].mean()
    ptc_prof = ptc_avg_dark_stack['hist'].dsnu_mean_horizontal.mean()

    assert round(ptc_prof, 7) == round(emva_prof, 7)


def test_ptc_avg_dark_stack_profiles_prnu(ptc_avg_dark_stack,
                                          emva_results_avg):
    emva_prof = emva_results_avg['prnu_mean_horizontal'].mean()
    ptc_prof = ptc_avg_dark_stack['hist'].prnu_mean_horizontal.mean()

    assert round(ptc_prof, 7) == round(emva_prof, 7)


def test_ptc_avg_dark_stack_responsivity(ptc_avg_dark_stack, emva_results_avg):
    emva_resp = emva_results_avg['responsivity']
    ptc_resp = \
        ptc_avg_dark_stack['summ']['Responsivity [DN/(uW/cm^2)]'][0]

    assert round(ptc_resp, 7) == round(emva_resp, 7)


def test_ptc_avg_dark_stack_saturation_capacity(ptc_avg_dark_stack,
                                                image_stats_avg):
    u_p = ptc_avg_dark_stack['data'].mean_e
    sig2_y = image_stats_avg['tot_var_temp_black_subtracted']
    val_dict = emva.saturation_capacity(u_p=u_p,
                                        sig2_y=sig2_y,
                                        qe=1)

    emva_sat = val_dict['sat_capacity_e']
    ptc_sat = ptc_avg_dark_stack['summ'].sat_capacity_e[0]

    assert ptc_sat == emva_sat


def test_ptc_avg_dark_stack_sensitivity_threshold(ptc_avg_dark_stack,
                                                  emva_results_avg):
    emva_sen = emva_results_avg['sensitivity_threshold_e']
    ptc_sen = ptc_avg_dark_stack['summ'].sensitivity_threshold_e[0]

    assert round(ptc_sen, 7) == round(emva_sen, 7)


def test_ptc_avg_dark_stack_snr(ptc_avg_dark_stack, emva_results_avg):
    u_p = ptc_avg_dark_stack['data'].mean_e
    prnu_tot = emva_results_avg['emva_prnu1288_alt']['tot_prnu1288_%']
    dsnu_tot = emva_results_avg['emva_dsnu1288_alt']['total_dsnu']
    val_dict = emva.snr(dsnu_tot=dsnu_tot,
                        prnu_tot=prnu_tot,
                        u_p=u_p,
                        s2_d=emva_results_avg['dark_temporal_noise_e'],
                        K=emva_results_avg['system_gain'],
                        qe=1)

    emva_snr = val_dict['snr_ratio'].mean()
    ptc_snr = ptc_avg_dark_stack['data'].snr_ratio.mean()

    assert round(ptc_snr, 7) == round(emva_snr, 7)


def test_ptc_avg_dark_stack_snr_ideal(ptc_avg_dark_stack):
    val_dict = emva.snr_ideal(u_p=ptc_avg_dark_stack['data'].mean_e)

    emva_snr = val_dict['snr_ideal_ratio'].mean()
    ptc_snr = ptc_avg_dark_stack['data'].snr_ideal_ratio.mean()

    assert ptc_snr == emva_snr


def test_ptc_avg_dark_stack_snr_theoretical(ptc_avg_dark_stack,
                                            emva_results_avg):
    u_p = ptc_avg_dark_stack['data'].mean_e
    val_dict = \
        emva.snr_theoretical(u_p=u_p,
                             s2_d=emva_results_avg['dark_temporal_noise_e'],
                             K=emva_results_avg['system_gain'],
                             qe=1)

    emva_snr = val_dict['snr_theoretical_ratio'].mean()
    ptc_snr = ptc_avg_dark_stack['data'].snr_theoretical_ratio.mean()

    assert round(ptc_snr, 7) == round(emva_snr, 7)


def test_ptc_avg_dark_stack_spectrogram_dsnu(ptc_avg_dark_stack,
                                             emva_results_avg):
    emva_spect = emva_results_avg['dsnu_power_spectrum_horizontal'].mean()
    ptc_spect = \
        ptc_avg_dark_stack['hist'].dsnu_power_spectrum_horizontal.mean()

    assert round(ptc_spect, 7) == round(emva_spect, 7)


def test_ptc_avg_dark_stack_spectrogram_prnu(ptc_avg_dark_stack,
                                             emva_results_avg):
    emva_spect = emva_results_avg['prnu_power_spectrum_horizontal'].mean()
    ptc_spect = \
        ptc_avg_dark_stack['hist'].prnu_power_spectrum_horizontal.mean()

    assert round(ptc_spect, 7) == round(emva_spect, 7)
