def il(img_stack_list: list,
        df: pd.DataFrame,
        exp_col: str = 'Exposure [uW/cm^2*s]',
        exp_col_units: str = 'uW/cm^2',
        rmv_ttn: bool = True,
        hpf: bool = False,
        image_idx_col: str = 'Image Index',
        cf: Optional[float] = None,
        shading_dim=32) -> Mapping[str, pd.DataFrame]:

    """
        TODO::
            - This can be used with only one dark image or using N dark images
                - Need to be defined in the yml?
            - Needs a light source
                - Set the lag inside the light source? [set_lag] [code is in the charmware [lightsource.py]
            - Current IL.py capture is first capturing the images with light and then the dark
            - Has two different capturing methods, using the NOS [Number of Sequences] iterations or using a "lightref"
            - Create a new tag in the LightSource "LAG" to be used to create a new sweep that calls a new "set lag" method, in the char_sweep parser.py file
            - Delay and duration need to be calculated. See method "determine_delayduration" on IL.py [charmware code]
    """