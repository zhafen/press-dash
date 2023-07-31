import unittest

import glob
import os
import shutil
from press_dashboard_library import pipeline


###############################################################################

class TestPipeline( unittest.TestCase ):

    def setUp( self ):

        # Set up dashboard dir, located at ../test_dashboard
        test_dir = os.path.dirname( __file__ )
        self.root_dir = os.path.dirname( test_dir )
        self.dashboard_dir = os.path.join( self.root_dir, 'test_dashboard' )
        os.makedirs( self.dashboard_dir, exist_ok=True )

        # Test data output location
        self.output_data_dir = os.path.abspath( os.path.join( self.root_dir, 'test_data', 'processed' ) )
        if os.path.isdir( self.output_data_dir ):
            shutil.rmtree( self.output_data_dir )

        # Copy in config
        self.config_fp = os.path.join( self.dashboard_dir, 'config.yml' )
        shutil.copy( os.path.join( self.root_dir, 'src', 'config.yml' ), self.config_fp  )

    ###############################################################################

    def tearDown( self ):

        # Remove the test dashboard dir
        if os.path.isdir( self.dashboard_dir ):
            shutil.rmtree( self.dashboard_dir )

        # Remove the output data dir
        if os.path.isdir( self.output_data_dir ):
            shutil.rmtree( self.output_data_dir )

    ###############################################################################

    def test_transform( self ):
        '''Test that transform works'''

        pipeline.transform( self.config_fp )

        assert os.path.isdir( self.output_data_dir )

    ###############################################################################

    def test_pipeline( self ):
        '''Test that transform works'''

        pipeline.transform( self.config_fp )
        pipeline.dashboard( self.config_fp )

        assert os.path.isdir( self.output_data_dir )
