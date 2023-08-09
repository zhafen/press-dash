import copy
import os
import pandas as pd
import re
import streamlit as st
import yaml

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

################################################################################

@st.cache_data
def load_config( dashboard_fp ):
    '''Get the config. Do this only once.
    '''

    # Check if we're in the directory the script is in,
    # which should also be the directory the config is in.
    # If not, move into that directory
    config_dir = os.path.dirname( dashboard_fp )
    if os.getcwd() != config_dir:
        os.chdir( config_dir )

    with open( './config.yml', "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

################################################################################

@st.cache_data
def load_original_data( config ):

    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    press_fp = os.path.join( output_dir, config['combined_filename'] )
    df = pd.read_csv( press_fp, index_col=0 )

    df.fillna( value='N/A', inplace=True )

    return df

################################################################################

@st.cache_data
def load_exploded_data( config, group_by ):

    remaining_groupings = copy.copy( config['groupings'] )
    remaining_groupings.remove( group_by )

    base, ext = os.path.splitext( config['combined_filename'] )
    exploded_filename = '{}.exploded{}'.format( base, ext )
    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    exploded_fp = os.path.join( output_dir, exploded_filename )
    exploded = pd.read_csv( exploded_fp )
    exploded.fillna( value='N/A', inplace=True )

    # DEBUG
    # exploded.set_index(remaining_groupings, inplace=True)

    # Colors for the categories
    color_palette = sns.color_palette( config['color_palette'] )
    category_colors = {}
    for i, category in enumerate( pd.unique( exploded[group_by] ) ):
        category_colors[category] = color_palette[i]

    return exploded, remaining_groupings, category_colors

################################################################################

def filter_data( exploded, selected_groups, search_str ):
    '''Filter the data shown.'''

    # Search filter
    is_included = exploded['Title'].str.extract( '(' + search_str + ')', flags=re.IGNORECASE ).notna().values[:,0]

    # Categories filter
    for group_by_i, groups in selected_groups.items():
        is_included = is_included & exploded[group_by_i].isin( groups )
    selected = exploded.loc[is_included]

    return selected

################################################################################

def count( selected, group_by, weighting ):
    '''Count up stats.'''

    # Nice simple case
    if weighting == 'Article Count':
        counts = selected.pivot_table( index='Year', columns=group_by, values='id', aggfunc='nunique' )

        return counts

    # Handle NaNs
    selected[weighting] = selected[weighting].replace( 'N/A', 0 )

    def aggfunc( df_agg ):
        df_agg = df_agg.drop_duplicates( 'id', keep='first' )
        return df_agg[weighting].sum()
    counts = selected.pivot_table(
        values=[weighting,'id'],
        index='Year',
        columns=group_by,
        aggfunc=aggfunc
    )

    return counts
