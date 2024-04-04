__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


import numpy as np
import sys
import os
import inspect
import pytest
import pdb
# currentdir = \
#     os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# parentdir = os.path.dirname(currentdir)
# sys.path.insert(0, parentdir)
from . import image_generator as ig
from characterization_ams.stats_engine import stats

# create synthetic image stack
gen_images = ig.gen_images

rows = 100
cols = 100
pedestal = 168
n_images = 1000

rfpn = 3
pfpn = 2
cfpn = 1
ctn = 15
rtn = 12
ptn = 20

tot_t = np.sqrt(ctn**2 + rtn**2 + ptn**2)
tot_f = np.sqrt(rfpn**2 + pfpn**2 + cfpn**2)

# generate images
imgs = gen_images(cfpn=cfpn,
                  ptn=ptn,
                  rtn=rtn,
                  ctn=ctn,
                  rfpn=rfpn,
                  pfpn=pfpn,
                  rows=rows,
                  cols=cols,
                  pedestal=pedestal,
                  n_images=n_images)

# get values required for testing
avg_img = stats.avg_img(imgs)
L = len(imgs)
ttn_var = stats.noise_metrics_temp(imgs)['tot_var_temp']

# averages #


def test_avg_offset():
    """
    """

    avg_img = stats.avg_img(imgs)
    avg = stats.avg_offset(avg_img)
    assert round(avg, 0) == pedestal


def test_avg_img():
    """
    """

    avg = stats.avg_img(imgs)
    assert round(np.mean(avg), 0) == pedestal


def test_col_avg():
    """
    """

    avgc = stats.col_avg(avg_img)
    avgc = np.mean(avgc)
    assert round(avgc, 0) == pedestal


def test_row_avg():
    """
    """

    avgr = stats.row_avg(avg_img)
    avgr = np.mean(avgr)
    assert round(avgr, 0) == pedestal

# spatial variance #


def test_tot_var():
    """
    """

    tot_var = stats.total_var(avg_img, L, ttn_var)
    assert round(np.sqrt(tot_var), 0) == round(tot_f, 0)


def test_row_var():
    """
    """

    row_var = stats.row_var(avg_img, L, ttn_var)
    assert round(np.sqrt(row_var), 0) == rfpn


def test_col_var():
    """
    """

    col_var = stats.col_var(avg_img, L, ttn_var)
    assert round(np.sqrt(col_var), 0) == cfpn


def test_pix_var():
    """
    """

    pix_var = stats.pix_var(avg_img, L, ttn_var)
    assert round(np.sqrt(pix_var), 0) == pfpn


# temporal variance #
def test_row_var_temp():
    """
    """

    row_var = stats.row_var_temp(imgs)
    assert round(np.sqrt(row_var), 0) == rtn


def test_col_var_temp():
    """
    """

    col_var = stats.col_var_temp(imgs)
    assert round(np.sqrt(col_var), 0) == ctn


def test_pix_var_temp():
    """
    """

    pix_var = stats.pix_var_temp(imgs)
    assert round(np.sqrt(pix_var), 0) == ptn


def test_tot_var_temp():
    """
    """

    tot_var = stats.total_var_temp(imgs)
    assert round(np.sqrt(tot_var), 0) == round(tot_t, 0)


def test_tot_var_image_stack():
    """
    """

    tot_var = stats.tot_var_img_stack(imgs)
    assert round(np.mean(np.sqrt(tot_var)), 0) == round(tot_t, 0)
