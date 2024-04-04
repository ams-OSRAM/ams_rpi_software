import numpy as np


__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


def gen_image(rows=100,
              cols=200,
              fpn=None,
              pedestal=None,
              col_scale=None,
              row_scale=None,
              pix_scale=None,
              seed=10,
              noise_func=np.random.normal,
              ):
    """
    Generate image with noise components plus offset

    Keyword Arguments:
        rows (int, 100): number of rows
        cols (int, 200): number of columns
        fpn (array, None): fpn frame of shape=(rows, cols)
        pedestal (int, None): pedestal offset value
        col_scale (numeric, None): column noise amplitude
        row_scale (numeric, None): column noise amplitude
        pix_scale (numeric, None): column noise amplitude
        seed (int, 10): random seed passed to numpy.random.seed
        noise_func (callable, numpy.random.normal): noise function

    Returns:
        image (numpy.array): generated image array with noise

    """
    # create fixed seed
    np.random.seed(seed)

    img = np.zeros((rows, cols))
    img += pedestal if pedestal is not None else 0
    img += fpn if fpn is not None else 0

    if row_scale is not None:
        amp = noise_func(loc=0, scale=row_scale, size=(rows, 1))
        img += np.tile(amp, (1, cols))

    if col_scale is not None:
        amp = noise_func(loc=0, scale=col_scale, size=(1, cols))
        img += np.tile(amp, (rows, 1))

    if pix_scale is not None:
        img += noise_func(loc=0, scale=pix_scale, size=(rows, cols))

    return img


def gen_images(
               rows=100,
               cols=200,
               pedestal=0,
               cfpn=0,
               rfpn=0,
               pfpn=0,
               ctn=0,
               rtn=0,
               ptn=0,
               seed_fpn=10,
               seeds_temporal=None,
               n_images=4,
               noise_func=np.random.normal,
              ):
    """
    Generate sequnce of images

    Keyword Arguments:
        rows (int, 100): number of rows
        cols (int, 200): number of columns
        pedestal (int, None): pedestal offset value
        cfpn (numeric, None): column fixed pattern noise amplitude
        rfpn (numeric, None): row fixed pattern noise amplitude
        pfpn (numeric, None): pixel fixed pattern noise amplitude
        ctn (numeric, None): column temporal noise amplitude
        rtn (numeric, None): row temporal noise amplitude
        ptn (numeric, None): pixel temporal noise amplitude
        seed_fpn (int, 10): random seed passed to np.random.seed for fixed pattern noise components
        seeds_temporal (list, None): list of random seeds passed to np.random.seed for fixed pattern noise components
        n_images (int, 4): number of images to generate if and only if seeds_temporal is not specified
        noise_func (callable, np.random.normal): noise function

    Returns:
        images (list of numpy.array): array of images with added noise components

    """
    seeds_temporal = [np.random.seed(e) for e in range(n_images)] \
        if seeds_temporal is None else seeds_temporal

    # generate FPN image
    fpn = gen_image(
        rows=rows,
        cols=cols,
        pedestal=pedestal,
        col_scale=cfpn,
        row_scale=rfpn,
        pix_scale=pfpn,
        seed=seed_fpn,
        noise_func=noise_func,
    )

    # generature temporal noise
    ims = [
        gen_image(rows=rows,
                  cols=cols,
                  fpn=fpn,
                  col_scale=ctn,
                  row_scale=rtn,
                  pix_scale=ptn,
                  seed=seed,
                  noise_func=noise_func)
        for seed in seeds_temporal]

    return ims