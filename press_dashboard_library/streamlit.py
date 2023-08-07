import os
import pandas as pd
import streamlit as st
import yaml

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
def load_original_data( press_fp ):

    df = pd.read_csv( press_fp, index_col=0 )

    df.fillna( value='N/A', inplace=True )

    return df