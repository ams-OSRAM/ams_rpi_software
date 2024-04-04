import numpy as np
from characterization_ams.utilities import utilities as ut
from characterization_ams.utilities import utilities as ut

__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2022, AMS Characterization"


def calc_pixelwise(func, arr3d, **kwargs):
    """
    generic wrapper to calculate pixelwise stats using
    np.apply_along_axis().
    Note: this is very slow and should only be used if there is
          no other way.

    The function is always applied along axis 0

    Keyword Args:
        func (function): function to be applied to each pixel
        arr3d (np.array): 3D numpy array
        kwargs (): Any arguments required by func
    Retuns:
        arr2d (np.array): 2D array where each pixel value is the result
                          of the per pixel calculation
    """

    arr2d = np.apply_along_axis(func, 0, arr=arr3d, **kwargs)

    return arr2d

@ut.ensure_img_stack
def dark_current(ims, tint):
    """
    Calculate per pixel dark current. This function is
    is lightning fast and uses numpy C implementation via
    np.polyfit()

    Each image should be an average image, if you have stacks
    of images for each operating (tint) point, computer the
    average using stats.stats.avg_img_stack() prior to passing
    to this function

    Keyword Arguments:
        ims (np.array): 3D array of average images where dim = (tint, rows, cols)
        tint (np.array): 1D array where each element is tint
                        Note: ims[0].shape[0] must equal tint.shape[0]
    Returns:
        dark_im (np.array): 2D array where each element corresponds to
                            dark current for that element in the original
                            image stack
    """

    dark_im = np.array((0, 0))

    # make sure dims are correct
    if not tint.shape[0] == ims.shape[0]:
        print('ims[0].shape[0] must equal tint.shape[0].\
              Check input dim of arrays')
        print('\nreturning empty array!')
        return dark_im

    # reduce a dimension
    im = ims.reshape(ims.shape[0], -1)

    # make the fit
    slope, offset = np.polyfit(tint, im, deg=1)

    # reshape back to original image size
    dark_im = slope.reshape((ims.shape[1], ims.shape[2]))

    return dark_im


def activation_energy(ims, temp, upper_bound=250):
    """
    Calculate per pixel activation energy [eV]. This function is
    is lightning fast and uses numpy C implementation via
    np.polyfit() each image in the stack should be dark current
    where the first dim (temp, rows, cols) corresponds to the only
    dim of the temp array

    Keyword Arguments:
        ims (np.array): 3D array where dim=(temp, rows, cols)
        temp (np.array): 1D array where each element is temp
                        Note: ims[0].shape[0] must equal temp.shape[0]
        upper_bound (float): upper bound for AE in [eV]. Any values above
                             this will be converted to np.nan, this is primarly
                             for extreme outliers
    Returns:
        dark_im (np.array): 2D array where each element corresponds to
                            activation energy [eV] for that element in the
                            original image stack
    """

    # constants
    boltzman_constant = 1.38064852e-23
    ae_im = np.array((0, 0))

    # make sure dims are correct
    if not temp.shape[0] == ims.shape[0]:
        print('ims[0].shape[0] must equal temp.shape[0]. Check input dim of arrays')
        print('\nreturning empty array!')
        return ae_im

    # reshape im to work with np.polyfit
    im = ims.reshape(ims.shape[0], -1)

    # prepare data for ae calc
    im = np.log(im)

    # correct data type
    temp = temp.astype(np.float64)

    # get x-axis for fit
    xarray = 1 / (boltzman_constant * temp)

    # get correct x shape
    xarray = xarray.reshape((temp.shape[0]))

    # remove invalid values with an absurd number
    # np.nan values and infinite values will break polyfit
    # struggled to get the masked array to work
    im_fit = im.copy()
    im_fit[~np.isfinite(im_fit)] = 2e20

    # make the fit
    slope, offset = -1 * np.polyfit(xarray, im_fit, deg=1)

    # reshape array to (row, col) of passed images
    ae_im = slope.reshape((ims.shape[1], ims.shape[2]))

    # don't love this for filtering out bad values...
    # TODO: Find a better way to remove the bad values..
    ae_im[ae_im > (upper_bound * 1.6e-19)] = np.nan

    # remove negative values, these pixels are no good
    ae_im[ae_im < 0] = np.nan

    # convert to eV
    ae_im /= 1.6e-19

    return ae_im


def pixelwise_lag():
    """
    """
    pass
