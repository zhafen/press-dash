import unittest

import glob
import os
import shutil
import subprocess
import yaml

from press_dashboard_library import streamlit as st_lib

###############################################################################

class TestDashboard( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.processed_dir = os.path.join( self.root_dir, 'test_data', 'processed' )

    ###############################################################################

    def test_load_config( self ):

        config = st_lib.load_config( os.path.join( self.root_dir, 'src', 'st_dashboard.py' ) )

        assert config['color_palette'] == 'deep'

    ###############################################################################

    def test_load_original_data( self ):

        press_fp = os.path.join( self.processed_dir, 'press.csv' )
        df = st_lib.load_original_data( press_fp )

        assert df.size > 0
