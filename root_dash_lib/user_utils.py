import copy
import glob
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

from root_dash_lib import data_utils

################################################################################

def load_data( config ):

    ################################################################################
    # Filepaths

    input_dir = os.path.join( config['data_dir'], config['input_dirname'] )

    def get_fp_of_most_recent_file( pattern ):
        fps = glob.glob( pattern )
        ind_selected = np.argmax([ os.path.getctime( _ ) for _ in fps ])
        return fps[ind_selected]

    data_fp = os.path.join( input_dir, config['website_data_file_pattern'] )
    data_fp = get_fp_of_most_recent_file( data_fp )

    press_office_data_fp = os.path.join( input_dir, config['press_office_data_file_pattern'] )
    press_office_data_fp = get_fp_of_most_recent_file( press_office_data_fp )

    ################################################################################
    # Load data

    # Website data
    df = pd.read_csv( data_fp, parse_dates=[ 'Date', ] )
    df.set_index( 'id', inplace=True )

    # Load press data
    press_df = pd.read_excel( press_office_data_fp )
    press_df.set_index( 'id', inplace=True )

    combined_df = df.join( press_df )

    return combined_df

def load_processed_data( config ):
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

def load_exploded_processed_data( config ):
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

    # Drop drafts
    df.drop( df.index[df['Date'].dt.year == 1970], axis='rows', inplace=True )

    # Drop weird articles---ancient ones w/o a title or press type
    df.dropna( axis='rows', how='any', subset=[ 'Title', 'Press Types', ], inplace=True )

    # Get rid of HTML ampersands
    for str_column in [ 'Title', 'Research Topics', 'Categories' ]:
        df[str_column] = df[str_column].str.replace( '&amp;', '&' )

    # Get the year, according to the config start date
    df['Year'] = data_utils.get_year( df['Date'], config['start_of_year'] )

    # Handle NaNs and such
    df[['Press Mentions', 'People Reached']] = df[['Press Mentions','People Reached']].fillna( value=0 )
    df.fillna( value='N/A', inplace=True )

    # Tweaks to the press data
    if 'Title (optional)' in df.columns:
        df.drop( 'Title (optional)', axis='columns', inplace=True )
    for column in [ 'Press Mentions', 'People Reached' ]:
        df[column] = df[column].astype( 'Int64' )

    # Now explode the data
    for group_by_i in config['groupings']:
        df[group_by_i] = df[group_by_i].str.split( '|' )
        df = df.explode( group_by_i )

    # Exploding the data results in duplicate IDs, so let's set up some new, unique IDs.
    df['id'] = df.index
    df.set_index( np.arange( len(df) ), inplace=True )

    return df, config
