import numpy as np
import pandas as pd
from . import image_generator as ig
from characterization_ams.utilities import utilities as ut
from characterization_ams.stats_engine import stats

# generate set of images
ped_start = 168
peds = np.linspace(168, 3800, 5)
power = np.linspace(0, 10, 5)
rows = 25
cols = 25
tint = 16e-3
images = []
temp = pd.DataFrame()
raw = pd.DataFrame()
for (idx, pp) in enumerate(peds):
    n_images = 5
    rfpn = 105
    cfpn = 101
    ctn = 15
    rtn = 12
    ptn = 20 + np.sqrt(pp)
    pfpn = 95 + 0.08 * (pp - ped_start)

    # fpn
    imgs = ig.gen_images(cfpn=cfpn,
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
for img in images:
    avg = stats.avg_img(img)
    avg_images.append(avg)

list_images = []
for im in images:
    list_images.append(im.tolist())

list_avg_images = []
for im in avg_images:
    list_avg_images.append(im.tolist())


def test_ensure_img():
    """
    """
    @ut.ensure_img
    def func(img):
        pass

    # pass image to func
    try:
        func(img=avg_images[0])
        assert True
    except Exception:
        assert False

    # pass image as list
    try:
        func(img=list_avg_images[0])
        assert True
    except Exception:
        assert False

    # pass image stack
    try:
        func(img=images[0])
        assert False
    except ValueError:
        assert True


def test_ensure_img_stack():
    """
    """
    @ut.ensure_img_stack
    def func(stack):
        pass

    # pass image stack to func
    try:
        func(stack=images[0])
        assert True
    except Exception:
        assert False

    # pass image stack as list
    try:
        func(stack=list_images[0])
        assert True
    except Exception:
        assert False

    # pass image
    try:
        func(stack=avg_images[0])
        assert False
    except ValueError:
        assert True


def test_ensure_img_or_stack():
    """
    """
    @ut.ensure_img_or_stack
    def func(data):
        pass

    # pass image to func
    try:
        func(data=avg_images[0])
        assert True
    except Exception:
        assert False

    # pass image as list
    try:
        func(data=list_avg_images[0])
        assert True
    except Exception:
        assert False

    # pass image stack to func
    try:
        func(data=images[0])
        assert True
    except Exception:
        assert False

    # pass image stack as list
    try:
        func(data=list_images[0])
        assert True
    except Exception:
        assert False

    # pass array
    try:
        func(data=avg_images[0][0])
        assert False
    except Exception:
        assert True


def test_ensure_img_list():
    """
    """
    @ut.ensure_img_list
    def func(img_list):
        pass

    # pass image list
    try:
        func(img_list=avg_images)
        assert True
    except Exception:
        assert False

    # images as lists
    try:
        func(img_list=list_avg_images)
        assert True
    except Exception:
        assert False

    # pass image stacks
    try:
        func(img_list=images)
        assert False
    except ValueError:
        assert True


def test_ensur_img_stack_list():
    """
    """
    @ut.ensure_img_stack_list
    def func(img_stack_list):
        pass

    # pass image stack list
    try:
        func(img_stack_list=images)
        assert True
    except Exception:
        assert False

    # image stacks in list form
    try:
        func(img_stack_list=list_images)
        assert True
    except Exception:
        assert False

    # pass images
    try:
        func(img_stack_list=avg_images)
        assert False
    except ValueError:
        assert True
