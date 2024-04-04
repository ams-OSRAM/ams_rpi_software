import numpy as np
import pandas as pd
from characterization_ams.stats_engine import stats
from characterization_ams.emva import emva
from characterization_ams.utilities import utilities as ut
from characterization_ams.kpi_calcs import calculations as calcs
from typing import Optional, Mapping


__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


def dummy(data: pd.DataFrame) -> Mapping[str, pd.DataFrame]:
    """
    dummy processor
    """

    vals = dict()
    vals['stats'] = data

    return vals


def vpt(data: pd.DataFrame,
        stat_cols: Optional[list] = None) -> Mapping[str, pd.DataFrame]:
    """
    processing function for VPT testing, currently just a
    place holder
    """

    vals = dict()
    vals['stats'] = data
    vals['vpt_stats'] = data.copy()

    return vals