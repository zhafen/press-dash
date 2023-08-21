import copy
import numpy as np
import os
import pandas as pd
import re
import streamlit as st
import yaml

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import seaborn as sns

def load_original_data( config ):
    '''Load the merged-but-unprocessed data.

    Args:
        config (dict): The config dictionary.

    Returns:
        original_df (pd.DataFrame): The dataframe containing the original data.
    '''

    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    press_fp = os.path.join( output_dir, config['combined_filename'] )
    original_df = pd.read_csv( press_fp, index_col=0 )

    original_df[['Press Mentions', 'People Reached']] = original_df[['Press Mentions','People Reached']].fillna( value=0 )
    original_df.fillna( value='N/A', inplace=True )

    return original_df

################################################################################

def load_data( config ):
    '''Load the df data. (df means one row per category.)
    https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.explode.html

    Args:
        config (dict): The config dictionary.
        group_by (str): The category to group the data by, e.g. 'Research Topics'.

    Returns:
        df (pd.DataFrame): The dataframe containing the df data.
    '''

    base, ext = os.path.splitext( config['combined_filename'] )
    df_filename = '{}.exploded{}'.format( base, ext )
    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    df_fp = os.path.join( output_dir, df_filename )
    df = pd.read_csv( df_fp )

    return df

################################################################################

def preprocess_data( df, config ):

    # Handle NaNs and such
    df[['Press Mentions', 'People Reached']] = df[['Press Mentions','People Reached']].fillna( value=0 )
    df.fillna( value='N/A', inplace=True )

    return df, config
