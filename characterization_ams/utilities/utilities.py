import numpy as np
import pandas as pd
from scipy.ndimage import convolve
import yaml
from characterization_ams import utilities
import pathlib
import decimal
import functools
from warnings import warn


__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


def high_pass_filter(img, dim):
    """
    Computes the high pass filtering on
    an image as defined by the EMVA Standard

    Keyword Arguments:
        img (df): DataFrame of raw image data to be filtered
        dim (int): Size of the high pass filter

    Returns:
        img (np.array): hpf image
    """

    # check that kernel for convolution is odd
    if not dim % 2:
        raise ValueError('The size of the highpass filter must be odd!')

    # create the Kernel
    kernel = np.ones((dim, dim))
    sl = dim//2
    kernel *= -1
    kernel[sl, sl] = dim**2 - 1

    # convolve
    img = convolve(img, kernel)[sl:-sl, sl:-sl]

    return img


def high_pass_filter_stack(imgs, dim):
    """
    TODO: check if this works
    """
    if not dim % 3:
        raise ValueError('The size of the highpass filter must be odd!')

    # create the Kernel
    kernel = np.ones((dim, dim, dim))
    sl = dim//2
    kernel *= -1
    kernel[:, sl, sl] = dim**2 - 1

    # convolve
    img = convolve(imgs, kernel)[:, sl:-sl, sl:-sl]

    return img


def filter_by_temporal(s2_y):
    """
    Filters data based on the maximum
    temporal noise (Taken directly from EMVA1288 Source Code)
    TODO: this may need to be more robust

    Keyword Arguments:
        noise_vals (np.array): array to find index of maximum for
    Returns:
        idx (int): index location of max value
    """

    max_ = 0
    max_i = 0

    for i in range((len(s2_y) - 1), -1, -1):
        if (s2_y[i] >= max_) or \
                (s2_y[abs(i-1)] >= max_):
            max_ = s2_y[i]
            max_i = i
        elif (s2_y[i] < max_) and \
                (s2_y[abs(i - 1)] < max_):
            break

    idx = max_i

    if idx < 5:
        idx = np.argmax(s2_y)

    return idx


def get_index(vals, perc, upper=True):
    """
    Returns the upperindex location of a specified percent (70% input as 0.7)
    Example: if I wanted 20% to 70% of array I would input perc=0.7 and
    upper=True for upper index and perc=0.2 and upper=False for lower index

    Keyword Arguments:
        vals (np.array): array of numerical values
        perc (np.array): percent of max index is to be returned for
        upper (bool): if True then index returned will be max index if
                      False then index returned will be min index

    Returns:
        idx (int): index location closest to the perc within vals
    """

    # get value based on input percentage
    val = perc * vals.max()

    # case where we want max index after filtering
    if upper:
        vals_sub = vals[vals <= val]
        idx = np.argmax(vals_sub)

    # case where we want min index after filtering
    else:
        vals_sub = vals[vals >= vals]
        idx = np.argmin(vals_sub)

    return idx


def find_closest(arr, val):
    """
    return the index of the closest value to request
    val in arr

    Keyword Arguments:
        arr (np.array): array of values
        val (float): value to find closest value in array for

    Returns:
        idx (int): index of closest value
    """

    arr = np.asarray(arr)
    idx = (np.abs(arr-val)).argmin()
    # idx = np.nanargmin(np.abs(arr-val)) # TODO: Add this in the future because the dark value (np.nan)
    return idx


def remove_black(df, cols=[]):
    """
    remove black level from df columns, ex. mean -->
    mean - dark mean, assumes index 0 is black level
    value

    Keyword Arguments:
        df (pd.DataFrame): DataFrame of data to subtract black
                           level from
        cols (list): list of cols to create new columns for,
                     if non specified all will be done

    Returns:
        df (pd.DataFrame): DataFrame with new black level columns
                           added in the following format:
                           'col' --> '{col} - Dark {col}'
    """

    temp = pd.DataFrame()

    # get columns we should use
    if len(cols) == 0:
        cols = list(df.columns)

    # remove black level
    temp = df[cols] - df[cols].iloc[0]

    # rename columns
    for cc in temp.columns:
        temp.rename(columns={cc: f'{cc}_black_subtracted'}, inplace=True)

    # add to original df
    df = df.join(temp)
    # df = df.join(temp.iloc[1:]) # TODO: Change this in the future because the dark value

    return df


def join_frame(df, dict_, replace_DN=False, K=1):
    """
    performe a merge operation on df and dictionary always
    preserving the largest axis

    Keyword Arguments:
        df (pd.DataFrame): DataFrame to perform join operation on
        dict_ (dictionary): dictionary of values to be added to df
    Returns:
        temp: (pd.DataFrame): DataFrame of joined values with all
                              data preserved
    """

    temp = pd.DataFrame()

    dict_df = dict_to_frame(dict_)

    if replace_DN:
        for cc in dict_df.columns:
            col_name = cc + '_DN'
            dict_df.rename(columns={cc: col_name}, inplace=True)
            col_name_e = cc + '_e'
            dict_df[col_name_e] = dict_df[col_name] / K

    if df.shape[0] > dict_df.shape[0]:
        how = 'left'
    else:
        how = 'right'

    temp = df.join(dict_df, how=how)

    return temp


def dict_to_frame(cdict):
    """
    convert Dict to DataFrame

    Keyword Arguments:
        cdict (dict): dictionary to be converted

    Returns:
        df (pd.DataFrame): DataFrame of converted values where each
                           key is a column name and each value is a
                           column
    """

    df = pd.DataFrame()

    if 'set_mult_channels' in cdict.keys():
        for kk, val in cdict.items():
            if kk == 'set_mult_channels':
                df[kk] = pd.Series(str(val))
            else:
                df[kk] = pd.Series(val)
    else:
        df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in cdict.items()]))

    return df


def get_half_sat_img(images, data, u_y, image_idx_col):
    """
    get half saturation image
    TODO: Make this more robust, currently assuming signal
          reaches the bit-depth
    """

    idx = data[image_idx_col].iloc[np.argmin(u_y)]
    idx -= data[image_idx_col].min()
    dark_avg_img = images[np.argmin(u_y)]
    half_sat = u_y.max() / 2
    idx = data[image_idx_col].iloc[find_closest(u_y, half_sat)]
    idx -= (data[image_idx_col].min() + 1)
    half_sat_avg_img = images[idx]

    return dark_avg_img, half_sat_avg_img, idx


def halfsat_interp(exp_arr, sig_arr):
    """
    Charmware output saves 50% frame as 50 instead of exposure point,
    this function can be used to fill in the missing exposure point
    to get back to a completely linear response

    Keyword Arguments:
        exp_arr (pd.Series|np.array): array of exposure values to have 50%
                                      exposure filled
        sig_arr (pd.Series|np.array): array of corresponding signal values
    Returns:
        exp_arr (pd.Series|np.array): updated exposure array
    """

    # get halfsat interp
    m = np.argmax(exp_arr)
    m_ = m - 1
    ma_ = m + 2
    if ma_ > sig_arr.values.shape[0] - 1:
        ma_ = sig_arr.values.shape[0] - 1
    u_ys = [sig_arr.values[m_], sig_arr.values[ma_]]
    exps = [exp_arr[m_], exp_arr[ma_]]
    val = np.interp(sig_arr[m], u_ys, exps)
    exp_arr.replace(exp_arr[m], val, inplace=True)

    return exp_arr


def rename(df,
           rename_file='default-renames.yaml',
           renames=None,
           revert=False,
           is_print=False):
    """
    Rename columns in df based on yaml rename file

    Keyword Args:
        df (pandas.DataFrame, None): data to rename (columns)
        renames (dict, None): if None reads rename key:value pairs
                              from the `rename_file' field
        revert (bool, None): if True renames back to original
        is_print (bool, False): Print rename key:value pairs and return

    Returns:
        renamed (pandas.DataFrame): renamed data columns
    """

    renames_from_yaml = get_col_renames(rename_file)

    renames = renames or renames_from_yaml

    if is_print:
        return pd.DataFrame(renames, index=['renamed']).T

    if revert:
        renames = {v: k for k, v in renames.items()}

    return df.rename(columns=renames)


def get_col_renames(rename_file='default-renames.yaml'):
    """
    """

    base_path = str(pathlib.Path(utilities.__file__).parents[0])

    rename_file = pathlib.Path(base_path, rename_file)

    renames = yaml.full_load(open(rename_file))

    return renames


def ensure_img_stack(func):
    """
    Ensures the first argument to the function is a 3D numpy array.
    LxMxN.
    """
    @functools.wraps(func)
    def _wrapper(stack, *args, **kwargs):
        if isinstance(stack, list):
            stack = np.array(stack)

        if stack.ndim == 3:
            return func(stack, *args, **kwargs)
        else:
            msg = 'input image/images must be one of the following:\n\n'\
                  '- list where each element is a frame from a stack'\
                  ' where each frame has dims=(rows,cols)\n'\
                  '- numpy array with dims=(frames, cols, rows)\n'
            raise ValueError(msg)

    return _wrapper


def ensure_img(func):
    @functools.wraps(func)
    def _wrapper(img, *args, **kwargs):
        if isinstance(img, list):
            img = np.array(img)

        if img.ndim == 3 and img.shape[0] == 1:
            img = np.squeeze(img, axis=0)

        if img.ndim == 2:
            return func(img, *args, **kwargs)
        else:
            raise ValueError('img must be numpy array with dims=(rows,cols)')

    return _wrapper


def ensure_img_or_stack(func):
    @functools.wraps(func)
    def _wrapper(data, *args, **kwargs):
        if isinstance(data, list):
            data = np.array(data)

        if data.ndim in [3, 2]:
            return func(data, *args, **kwargs)
        else:
            msg = 'input image/images must be one of the following:\n\n'\
                  '- list where each element is a frame from '\
                  'a stack with dims=(rows,cols)\n'\
                  '- numpy array with dims=(frames, cols, rows)\n'\
                  '- numpy array with dims = (rows, cols)'
            raise ValueError(msg)

    return _wrapper


def ensure_img_list(func):
    @functools.wraps(func)
    def _wrapper(img_list, *args, **kwargs):
        if isinstance(img_list[0], list):
            for idx, im in enumerate(img_list):
                img_list[idx] = np.array(im)

        if img_list[0].ndim == 3 and img_list[0].shape[0] == 1:
            for idx, im in enumerate(img_list):
                img_list[idx] = np.squeeze(im, axis=0)

        if img_list[0].ndim == 2:
            return func(img_list, *args, **kwargs)
        else:
            msg = ('images must be a list or numpy array '
                   'containing numpy arrays with dims=(rows,cols)')
            raise ValueError(msg)

    return _wrapper


def ensure_img_stack_list(func):
    @functools.wraps(func)
    def _wrapper(img_stack_list, *args, **kwargs):
        if isinstance(img_stack_list[0], list):
            for idx, stack in enumerate(img_stack_list):
                img_stack_list[idx] = np.array(stack)

        if img_stack_list[0].ndim == 3:
            return func(img_stack_list, *args, **kwargs)
        else:
            msg = ('input images must be one of the following:\n\n'
                   '- list or numpy array where each element is a stack '
                   'of images with dims=(rows,cols)\n'
                   '- list or numpy array of numpy arrays each with '
                   'dims=(frames, cols, rows)\n')
            raise ValueError(msg)

    return _wrapper


def stat_engine_col_rename():
    """
    Returns dict for renaming stat engine column
    """

    return get_col_renames('default-renames.yaml')


def num_decimals(val):
    """
    Get the number of decimals in a value

    ..note: there is danger here because floating point precision can do
    weird things

    Args:
        val (float|int|str): value to check

    Returns:
        num (int | None): None if exception else estimated number of decimals
    """

    try:
        return abs(decimal.Decimal(str(val)).as_tuple().exponent)
    except Exception:
        return None

def config_from_yaml(path):
    """
    load and return a dict from a yaml input file

    Keyword Arguments:
        path (str): full path

    Returns:
        config (dict): dictionary of loaded yaml file
    """

    with open(path, 'r') as stream:
        try:
            gen = yaml.safe_load_all(stream)
            config = next(gen)
            [config.update(d) for d in gen]
        except yaml.YAMLError as exc:
            warn(exc)

    return config