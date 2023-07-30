import unittest

import glob
import os
import shutil
from press_dashboard_library import pipeline

TEST_DIR = os.path.dirname( __file__ )
DASHBOARD_DIR = os.path.join( TEST_DIR, 'test_dashboard' )
CONFIG_FP = os.path.join( DASHBOARD_DIR, 'config.yml' )

###############################################################################

class TestPipeline( unittest.TestCase ):

    def setUp( self ):

        # Clean things up
        self.output_data_dir = os.path.abspath( os.path.join( TEST_DIR, 'test_data', 'output' ) )
        if os.path.isdir( self.output_data_dir ):
            shutil.rmtree( self.output_data_dir )

    ###############################################################################

    def tearDown( self ):
        
        transform_fps = glob.glob( os.path.join( DASHBOARD_DIR, 'transform_*.ipynb' ) )
        for fp in transform_fps:
            os.remove( fp )

    ###############################################################################

    def test_transform( self ):

        pipeline.transform( CONFIG_FP )

        assert os.path.isdir( self.output_data_dir )
