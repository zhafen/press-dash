#!/usr/bin/env python
'''Main executable for the press dashboard.'''
from datetime import datetime
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os
import sys
import yaml

PIPELINE_DIR = os.path.dirname( os.path.abspath( __file__ ) )

def transform( config_fp ):
    '''Transform the data into a better format
    '''

    # Load options
    with open( config_fp, 'r') as f:
        config = yaml.full_load( f )

    # Parse filetree options
    dashboard_dir = os.path.dirname( config_fp )
    os.chdir( dashboard_dir )
    # Default to the notebook stored in the library folder
    if config['transform_nb_fp'] == 'default':
        transform_nb_fp = os.path.join( PIPELINE_DIR, 'transform.ipynb' )
    else:
        transform_nb_fp = config['transform_nb_fp']

    # Read and execute notebook
    with open( transform_nb_fp ) as f:
        nb = nbformat.read( f, as_version=4 )
    ep = ExecutePreprocessor( timeout=500 )
    ep.preprocess( nb, {'metadata': {'path': os.getcwd() }} )

    # Get the current date and time
    current_datetime = datetime.now()
    datestamp = current_datetime.strftime("%Y-%m-%d")

    # Save executed notebook
    script_fn = os.path.basename( transform_nb_fp )
    script_fb, ext = os.path.splitext( script_fn )
    executed_fp = '{}_{}{}'.format( script_fb, datestamp, ext )
    with open( executed_fp, 'w', encoding='utf-8' ) as f:
        nbformat.write( nb, f )

if __name__ == '__main__':
    config_fp = sys.argv[-1]

    transform( config_fp )