import unittest

import glob
import os
import shutil
import subprocess
import yaml

from press_dashboard_library import pipeline

###############################################################################

class TestPipeline( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.config_fp = os.path.join( test_dir, 'config_raw_only.yml' )
        self.root_dir = os.path.dirname( test_dir )
        self.test_data_dir = os.path.join( self.root_dir, 'test_data', 'test_data_raw_only' )

        # Set up temporary dirs
        self.temp_dirs = {
            'processed_data_dir': os.path.join( self.test_data_dir, 'processed_data' ),
            'figure_dir': os.path.join( self.test_data_dir, 'figures' ),
            'logs_dir': os.path.join( self.test_data_dir, 'logs' ),
        }
        for key, temp_dir in self.temp_dirs.items():
            if os.path.isdir( temp_dir ):
                shutil.rmtree( temp_dir )

        # Set up news data fp
        self.news_data_fp = os.path.join( self.test_data_dir, 'raw_data', 'News_Report_2023-07-25.csv' )
        self.dup_news_data_fp = self.news_data_fp.replace( '07-25', 'null-null' )

    ###############################################################################

    def tearDown( self ):

        # Remove dashboard and figures temp dirs
        for key in self.temp_dirs.keys():
            temp_dir = self.temp_dirs[key]
            if os.path.isdir( temp_dir ):
                shutil.rmtree( temp_dir )

        if os.path.exists( self.dup_news_data_fp ):
            os.remove( self.dup_news_data_fp )

    ###############################################################################

    def test_parse_config( self ):

        with open( self.config_fp, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        # Paths are relative to the config
        os.chdir( os.path.dirname( self.config_fp ) )
        assert config['data_dir'] == os.path.relpath( self.test_data_dir )
        assert config['figure_dir'] == os.path.relpath( self.temp_dirs['figure_dir'] )

    ###############################################################################

    def test_transform( self ):
        '''Test that transform works'''

        pipeline.transform( self.config_fp )

        # Check that there are output files
        output_files = [
            ( 'counts', 'counts.categories.csv', ),
            ( 'counts', 'counts.press_types.csv', ),
            ( 'counts', 'counts.research_topics.csv', ),
            ( 'press.csv', ),
            ( 'press.exploded.csv', ),
        ]
        for output_file in output_files:
            output_fp = os.path.join( self.temp_dirs['processed_data_dir'], *output_file )
            assert os.path.isfile( output_fp )

        # Check that there's an output NB in the logs
        transform_fps = glob.glob( os.path.join( self.temp_dirs['logs_dir'], 'transform_*.ipynb' ) )
        assert len( transform_fps ) > 0

    ###############################################################################

    def test_transform_extra_files( self ):
        '''Test that transform works when there are multiple options.'''

        # Make an extra copy
        shutil.copy( self.news_data_fp, self.dup_news_data_fp )

        pipeline.transform( self.config_fp )

        # Check that there are output files
        output_files = [
            ( 'counts', 'counts.categories.csv', ),
            ( 'counts', 'counts.press_types.csv', ),
            ( 'counts', 'counts.research_topics.csv', ),
            ( 'press.csv', ),
            ( 'press.exploded.csv', ),
        ]
        for output_file in output_files:
            output_fp = os.path.join( self.temp_dirs['processed_data_dir'], *output_file )
            assert os.path.isfile( output_fp )

        # Check that there's an output NB in the logs
        transform_fps = glob.glob( os.path.join( self.temp_dirs['logs_dir'], 'transform_*.ipynb' ) )
        assert len( transform_fps ) > 0

    ###############################################################################

    def test_pipeline( self ):
        '''Test that dashboard is generated works'''

        pipeline.transform( self.config_fp )
        pipeline.dashboard( self.config_fp )

        # Check that there's an output NB
        dashboard_fps = glob.glob( os.path.join( self.temp_dirs['dashboard'], 'dashboard_*.ipynb' ) )
        assert len( dashboard_fps ) > 0

    ###############################################################################

    def test_full( self ):

        # Move to the root directory
        os.chdir( self.root_dir )

        # Run the pipeline
        subprocess.run([ './press_dashboard_library/pipeline.py', './test_dashboard/config.yml' ])

        # Check that there are output NBs
        transform_fps = glob.glob( os.path.join( self.temp_dirs['dashboard'], 'transform_*.ipynb' ) )
        assert len( transform_fps ) > 0
        dashboard_fps = glob.glob( os.path.join( self.temp_dirs['dashboard'], 'dashboard_*.ipynb' ) )
        assert len( dashboard_fps ) > 0

    ###############################################################################

    def test_streamlit( self ):

        # Move to the root directory
        os.chdir( self.root_dir )

        subprocess.check_output([ 'streamlit', './test_dashboard/st_dashboard.py' ])


