import functools
import numpy as np
import pandas as pd
from scipy import stats as ss


def aggfuns(aggs=None, data=None, fast_q=True, sort=True):
    """
    Lookup aggregation functions by alias string. Useful for defining a
    "nice" label for the stat initially and then looking up the appropriate
    statistic function

    Args:
        aggs (list of str or tuple): alias for aggregation function
            if agg is tuple then the first element is the alias while
            the second is a function of the form::

                    f(data) = float

            defined functions are::

                * %tile such as 0.1%, 0.5%, 50%, etc.
                * percentile in a "string" form defined by "PCT":

                    PCT0p1, PCT99p9, ...

                * normal quantile defined by "P|M" (+/-) and "S" (sigma):

                    M3P0S, 0p0S, P2.2S, ...

            and:

                n=len,
                count=len,
                sum=np.sum,
                std=np.std,
                var=np.var,
                min=min,
                med=np.median,
                median=np.median,
                mean=np.mean,
                max=max,
                pmax=max

            Defaults to: 'count', 'mean', 'std', 'min', '5%', '25%', '50%',
             '75%', '95%', 'max'

    Kewword Args:
        data (array like, None): optional array of values to apply
            aggregations functions
        fast_q (bool, True): if True use ``calc.percentile_fast`` else
            ``numpy.percentile``
        sort (bool, True): if True presort array for speed (also applied if
            ``fast_q=True``)

    Returns:
        mapped (pandas.Series): function if ``data`` is ``None`` else
            ``function(data)``

    """
    aggs = ['count', 'mean', 'std',
            'min', '25%', '50%',
            '75%', 'max'] if aggs is None else aggs

    if len(set(aggs)) != len(aggs):
        raise ValueError('aggs must be unique')

    mappings = dict(
                        n=len,
                        count=len,
                        sum=np.sum,
                        std=np.std,
                        var=np.var,
                        min=min,
                        med=np.median,
                        median=np.median,
                        mean=np.mean,
                        mn=np.mean,
                        max=max,
                        pmax=max,
                        nmax=n_max,
                        n_max=n_max,

                    )

    funs = pd.Series()

    if sort or fast_q:
        data = np.sort(data)

    if fast_q:
        percentile = percentile_fast
    else:
        percentile = np.percentile

    for iagg, agg0 in enumerate(aggs):
        if isinstance(agg0, tuple):
            funs[str(agg0[0])] = agg0[1]
            continue

        if not isinstance(agg0, str):
            funs[str(agg0)] = functools.partial(percentile, q=agg0 * 100)
            continue

        agg = agg0.lower()
        neg = True if agg[0] in ['m', '-'] else False
        if '%' in agg:
            qtile = float(agg.strip('%'))
            fun = functools.partial(percentile, q=qtile)
        elif 'pct' in agg:
            qtile = float(agg.strip('pct').replace('p', '.'))
            fun = functools.partial(percentile, q=qtile)
        elif agg.endswith('s') or 'sigma' in agg:
            sigma = float(agg.strip('-sigmap').replace('p', '.'))
            sigma = -sigma if neg else sigma
            qtile = ss.norm.cdf(sigma) * 100
            fun = functools.partial(percentile, q=qtile)
        elif agg.lower() in mappings:
            fun = mappings[agg.lower()]
        else:
            raise ValueError('aggfun not understood {}'.format(agg))

        funs[agg0] = fun

    if data is None:
        return funs

    return pd.Series(index=pd.Index(data=funs.index, name='stat'),
                     data=[f(data) for f in funs], name='value')


def aggsigma_to_float(x, minval=None, maxval=None, format_spec: str = None):
    """
    Converts aggregation sigma string to numeric representation as string or
    float (optional)

    Args:
        x (string): intput string to convert

    Keyword Args:
        minval (numeric, -3.2): value to cast min
        maxval (numeric, 3.2): value to cast max
        format_spec (str, None): format specifier passed to str.format method

    Returns:
        value (float|str): return float or formatted float string

    """
    x = str(x).lower()
    if x == 'med':
        y = 0.0
    elif x == 'min':
        y = float(minval) if minval is not None else np.nan
    elif x == 'max':
        y = float(maxval) if maxval is not None else np.nan
    else:
        #  this works with nice sigma string representation
        #  may need modifiers or exceptions if get a crappy version of a
        #  printed sigma
        y = x.replace('m', '-').strip('sp').replace('p', '.')
        try:
            y = float(y)
        except:
            np.nan

    return format_spec.format(y) if isinstance(format_spec, str) else y


def limits(lims, x):
    """
    Calculate axes limits - keeps float convertible numerics else passes to
    `calc.aggfuns`_

    Args:
        lims (tuple): numeric or valid argument to `calc.aggfuns`_
        x (array): data array
    """
    limso = []
    for lim in lims:
        if lim is None:
            limso += [None]
            continue
        try:
            limso += [float(lim)]
        except Exception:
            limso += [aggfuns([lim], x)[0]]

    return limso


def normal_quantile(x, inverse: bool = False, qrank=None):
    """
    Normal quantile and percentiles calculation for array of values

    Args:
        x (array_like): distribtion of values

    Keyword Args:
        inverse (bool, False): return 1-sigma rather than sigma
        qrank (str, Bernards): rank method in 'bernards'|'norm'

    Returns:
        df (pandas.DataFrame): data with the following columns:
                x: sorted x values
                sigma: normal quantile
                pct : percentile

    .. todo:: need some better error handling - e.g. remove nans, and add
                other rank methods

    qrank methods (rankits):
    https://en.wikipedia.org/wiki/Q%E2%80%93Q_plot
        (k − 0.3) / (n + 0.4).[10] (bernards)
        (k − 0.3175) / (n + 0.365).[11]
        (k − 0.326) / (n + 0.348).[12]
        (k − ⅓) / (n + ⅓).[13]
        (k − 0.375) / (n + 0.25).[14]
        (k − 0.4) / (n + 0.2).[15]
        (k − 0.44) / (n + 0.12).[16]
        (k − 0.5) / (n).[17]
        (k − 0.567) / (n − 0.134).[18]
        (k − 1) / (n − 1).[19]

    Fillibens:
        {\displaystyle m(i)={\begin{cases}1-0.5^{1/n}&i=1\\\\{\dfrac
        {i-0.3175}{n+0.365}}&i=2,3,\ldots ,n-1\\\\0.5^{1/n}&i=n.\end{cases}}}


    https://en.wikipedia.org/wiki/Normal_probability_plot


    qqnorm from R:
    z_{i}=\Phi ^{{-1}}\left({\frac  {i-a}{n+1-2a}}\right),
        for i = 1, 2, ..., n, where

        a = 3/8 if n ≤ 10 and
        0.5 for n > 10,
    """

    def bernards(x):
        return ((x - 0.3) / (x.max() + 0.4))

    if len(x) == 0:
        return pd.DataFrame(data={'X': [], 'Sigma': [], 'PCT': []})

    y = np.sort(x.copy())
    n = np.ones(len(y))
    cs = np.cumsum(n)
    if qrank == 'norm':  # just for completeness...
        pct = cs / max(cs)
    else:
        pct = bernards(cs)
    sigma = ss.norm.ppf(pct)
    sigma = -sigma if inverse else sigma

    return pd.DataFrame(data={'X': y, 'Sigma': sigma, 'PCT': pct})


def n_max(x):
    """
    Get number of maximum value elements

    Args:
        x (array): values

    Returns:
        n_max (int): number of occurences of maximum value

    """
    return len(x[x == max(x)])


def percentile_fast(N, q, key=lambda x: x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter q - a float value from 0.0 to 100.
    @parameter key - optional key function to compute value from each element
    of N.

    @return - the percentile of the values
    """

    k = (len(N)-1) * q / 100
    f = np.floor(k)
    c = np.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0 + d1
