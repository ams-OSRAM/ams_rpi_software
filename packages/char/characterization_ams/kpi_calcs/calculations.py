import numpy as np


__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2023, AMS Characterization"


def prnu1288(spatial_metrics):
    """
    calculate total, row, col, and pix PRNU1288 from avg images
    EMVA 4.0: Eq. 67

    Keyword Arguments:
        spatial_metrics (dict):
            tot_var_half
            pix_var_half
            row_var_half
            col_var_half
            tot_var_dark
            pix_var_dark
            row_var_dark
            col_var_dark
            u_y_dark
            u_y_half

    Returns:
        temp (dict): tot_prnu1288_%
                     row_prnu1288_%
                     col_prnu1288_%
                     pix_prnu1288_%
    """
    tot_prnu = np.sqrt(spatial_metrics['tot_var_half'] - spatial_metrics['tot_var_dark']) \
        / (spatial_metrics['u_y_half'] - spatial_metrics['u_y_dark']) * 100

    row_prnu = np.sqrt(spatial_metrics['row_var_half'] - spatial_metrics['row_var_dark']) \
        / (spatial_metrics['u_y_half'] - spatial_metrics['u_y_dark']) * 100

    col_prnu = np.sqrt(spatial_metrics['col_var_half'] - spatial_metrics['col_var_dark']) \
        / (spatial_metrics['u_y_half'] - spatial_metrics['u_y_dark']) * 100

    pix_prnu = np.sqrt(spatial_metrics['pix_var_half'] - spatial_metrics['pix_var_dark']) \
        / (spatial_metrics['u_y_half'] - spatial_metrics['u_y_dark']) * 100

    temp = {'tot_prnu1288_%': tot_prnu,
            'row_prnu1288_%': row_prnu,
            'col_prnu1288_%': col_prnu,
            'pix_prnu1288_%': pix_prnu}

    return temp


def doubling_temp(mean: np.array, tint: np.array) -> float:
    """
    Calculate Doubling Temperature
    """

    offset, slope = np.polynomial.polynomial.polyfit(tint,
                                                     np.log10(mean),
                                                     1)
    return 2/slope


def shading_calc(img: np.array, dim: int = 32) -> dict:
    """

    Calculate median and mean point to point shading. The image is broken
    into n dim x dim regions. If extra rows are present they are removed from
    the array prior to the calculation as rows and cols must be
    divsible by the 'dim' keyword.

    Shading is calculated by performing the following step:
    1.) breaking the array into dim x dim tiles
    2.) calculating the mean/median of each tile
    3.) shading is the max of the mean/median tiles subtracted
        from the min of the mean/median tiles

    Args:
        img (np.array): 2D image to calculate shading on
        dim (int, optional): dim of requested tiles. Defaults to 32.

    Returns:
        dict: mean and median shading value
    """

    res = dict()
    roi = []

    # make sure we can perform the tile
    extra_rows = img.shape[0] % dim
    extra_cols = img.shape[1] % dim

    if extra_rows:
        if extra_rows == img.shape[0]:
            msg = 'Could not calculate shading! image size equals dim'
            print(msg)
            return res
        else:
            img = img[:(-1 * extra_rows), :]
    if extra_cols:
        if extra_cols == img.shape[1]:
            msg = 'Could not calculate shading! image size equals dim'
            print(msg)
            return res
        else:
            img = img[:, :(-1*extra_cols)]

    # split the array
    for v in np.vsplit(img, img.shape[0] // dim):
        roi.extend([*np.hsplit(v, img.shape[1] // dim)])
    roi = np.array(roi)

    # reshape
    roi = roi.reshape(roi.shape[0], roi.shape[1]*roi.shape[2])

    # get values
    mean_shading_min = roi.mean(axis=1).min()
    mean_shading_max = roi.mean(axis=1).max()
    median_shading_min = np.median(roi, axis=1).min()
    median_shading_max = np.median(roi, axis=1).max()

    res['mean_shading_pp'] = mean_shading_max - mean_shading_min
    res['median_shading_pp'] = median_shading_max - median_shading_min
    res['mean_shading_min'] = mean_shading_min
    res['mean_shading_max'] = mean_shading_max
    res['median_shading_min'] = median_shading_min
    res['median_shading_max'] = median_shading_max

    return res
