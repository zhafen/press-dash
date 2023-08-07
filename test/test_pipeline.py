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
        self.root_dir = os.path.dirname( test_dir )

        # Set up temporary dirs
        self.temp_dirs = {
            'dashboard': os.path.join( self.root_dir, 'test_dashboard' ),
            'processed': os.path.join( self.root_dir, 'test_data', 'processed' ),
            'figures': os.path.join( self.root_dir, 'test_data', 'figures' ),
        }
        for key, temp_dir in self.temp_dirs.items():
            if os.path.isdir( temp_dir ):
                shutil.rmtree( temp_dir )
            os.makedirs( temp_dir )

        # Copy in config
        self.config_fp = os.path.join( self.temp_dirs['dashboard'], 'config.yml' )
        shutil.copy( os.path.join( self.root_dir, 'src', 'config.yml' ), self.config_fp  )

        # Set up news data fp
        self.news_data_fp = os.path.join( self.root_dir, 'test_data', 'input', 'News_Report_2023-07-25.csv' )
        self.dup_news_data_fp = self.news_data_fp.replace( '07-25', 'null-null' )

    ###############################################################################

    def tearDown( self ):

        # Remove dashboard and figures temp dirs
        for key in [ 'dashboard', 'figures' ]:
            temp_dir = self.temp_dirs[key]
            if os.path.isdir( temp_dir ):
                shutil.rmtree( temp_dir )

        if os.path.exists( self.dup_news_data_fp ):
            os.remove( self.dup_news_data_fp )

    ###############################################################################

    def test_parse_config( self ):

        with open( './src/config.yml', "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        assert config['data_dir'] == '../test_data'
        assert config['figure_dir'] == '../test_data/figures'

    ###############################################################################

    def test_transform( self ):
        '''Test that transform works'''

        pipeline.transform( self.config_fp )

        # Check that there's an output NB
        transform_fps = glob.glob( os.path.join( self.temp_dirs['dashboard'], 'transform_*.ipynb' ) )
        assert len( transform_fps ) > 0

    ###############################################################################

    def test_transform_extra_files( self ):
        '''Test that transform works'''

        # Make an extra copy
        shutil.copy( self.news_data_fp, self.dup_news_data_fp )

        pipeline.transform( self.config_fp )

        # Check that there's an output NB
        transform_fps = glob.glob( os.path.join( self.temp_dirs['dashboard'], 'transform_*.ipynb' ) )
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


