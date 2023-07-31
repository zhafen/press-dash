#!/usr/bin/env python
'''Main executable for the press dashboard.'''
from datetime import datetime
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
import os
import sys
import yaml

def execute_nb( config_fp, nb_fp_key, default_basename, include_date=True ):
    '''Execute a notebook that's part of the pipeline.
    '''

    # Load options
    with open( config_fp, 'r') as f:
        config = yaml.full_load( f )

    # Parse filetree options
    dashboard_dir = os.path.dirname( config_fp )
    os.chdir( dashboard_dir )
    # Default to the notebook stored in the src folder
    if config[nb_fp_key] == 'default':
        pipeline_dir = os.path.dirname( os.path.abspath( __file__ ) )
        src_dir = os.path.join( os.path.dirname( pipeline_dir ), 'src' )
        nb_fp = os.path.join( src_dir, default_basename )
    else:
        nb_fp = config[nb_fp_key]

    # Get the current date and time
    script_fn = os.path.basename( nb_fp )
    if include_date:
        current_datetime = datetime.now()
        datestamp = current_datetime.strftime("%Y-%m-%d")
        script_fb, ext = os.path.splitext( script_fn )
        executed_fp = '{}_{}{}'.format( script_fb, datestamp, ext )
    else:
        executed_fp = script_fn

    # Read and execute notebook
    with open( nb_fp ) as f:
        nb = nbformat.read( f, as_version=4 )
    ep = ExecutePreprocessor( timeout=500, store_widget_state=False )
    try:
        out = ep.preprocess( nb, {'metadata': {'path': os.getcwd() }} )
    except CellExecutionError:
        out = None
        msg = 'Error executing the notebook "%s".\n\n' % nb_fp
        msg += 'See notebook "%s" for the traceback.' % executed_fp
        print(msg)
        raise
    finally:
        with open(executed_fp, mode='w', encoding='utf-8') as f:
            nbformat.write(nb, f)

    # Save executed notebook
    with open( executed_fp, 'w', encoding='utf-8' ) as f:
        nbformat.write( nb, f )


def transform( config_fp ):
    '''Transform the data into a better format
    '''
    execute_nb( config_fp, 'transform_nb_fp', 'transform.ipynb' )

def dashboard( config_fp ):
    '''Make the dashboard
    '''
    execute_nb( config_fp, 'dashboard_nb_fp', 'dashboard.ipynb' )

if __name__ == '__main__':
    config_fp = os.path.abspath( sys.argv[-1] )

    transform( config_fp )
    dashboard( config_fp )