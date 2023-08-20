'''This file contains code the user is recommended to modify for their purposes.
'''
import glob
import numpy as np
import os
import pandas as pd
import streamlit as st

################################################################################

def load_data( config ):
    '''Load the data.

    Args:
        config (dict): The config dictionary.

    Returns:
        df (pd.DataFrame): The dataframe containing the awards data.
    '''

    # Get possible files
    input_dir = os.path.join( config['data_dir'], config['input_dirname'] )
    pattern = os.path.join( input_dir, config['data_file_pattern'] )
    data_fps = glob.glob( pattern )

    # Select the most recent file
    ind_selected = np.argmax([ os.path.getctime( _ ) for _ in data_fps ])
    data_fp = data_fps[ind_selected]

    df = pd.read_csv( data_fp, sep='\t', encoding='UTF-16' )

    return df

################################################################################

def preprocess( df, config ):
    '''Preprocess the data. Anything too time-intensive should be offloaded
    to transform.ipynb.
    '''

    # Set ID
    df['id'] = df[config['primary_id_column']]

    # Convert dates to years.
    if 'date_columns' in config:
        for date_column in config['date_columns']:

            # Convert to datetime
            df[date_column] = pd.to_datetime( df[date_column] )

            # Get date bins
            start_year = df[date_column].min().year - 1
            end_year = df[date_column].max().year + 1
            date_bins = pd.date_range(
                '{} {}'.format( config['year_start'], start_year ),
                pd.Timestamp.now() + pd.offsets.DateOffset( years=1 ),
                freq = pd.offsets.DateOffset( years=1 ),
            )
            date_bin_labels = date_bins.year[:-1]

            # Column name
            year_column = date_column.replace( 'Date', 'Year' )
            if 'year_columns' not in config:
                config['year_columns'] = []
            # To avoid overwriting the year column, we append a label to the end
            if year_column in config['year_columns']:
                year_column += ' (Custom)'
            config['year_columns'].append( year_column )

            # Do the actual binning
            df[year_column] = pd.cut( df[date_column], date_bins, labels=date_bin_labels ) 

    # Drop bad data (years earlier than 2000)
    for year_column in config['year_columns']:
        zero_inds = df.index[df[year_column] < 2000]
        df = df.drop( zero_inds )

    return df, config