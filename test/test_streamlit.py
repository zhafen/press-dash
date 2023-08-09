import unittest

import glob
import numpy as np
import os
import pandas as pd
import shutil
import subprocess
import yaml

from press_dashboard_library import streamlit as st_lib

###############################################################################

class TestDashboardSetup( unittest.TestCase ):

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

        config = st_lib.load_config( os.path.join( self.root_dir, 'src', 'st_dashboard.py' ) )
        df = st_lib.load_original_data( config )

        assert df.size > 0

    ###############################################################################

    def test_load_exploded_data( self ):

        group_by = 'Research Topics'

        config = st_lib.load_config( os.path.join( self.root_dir, 'src', 'st_dashboard.py' ) )
        exploded, remaining_groupings, category_colors = st_lib.load_exploded_data( config, group_by )

        assert exploded.size > 0 

###############################################################################
###############################################################################

class TestDashboard( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.processed_dir = os.path.join( self.root_dir, 'test_data', 'processed' )

        self.group_by = 'Research Topics'
        self.config = st_lib.load_config( os.path.join( self.root_dir, 'src', 'st_dashboard.py' ) )
        self.df = st_lib.load_original_data( self.config )
        self.exploded, self.remaining_groupings, self.category_colors = st_lib.load_exploded_data( self.config, self.group_by )

    ###############################################################################

    def test_filter_data( self ):

        search_str = ''
        all_selected_columns = {
            'Research Topics': [ 'Galaxies & Cosmology', ],
            'Press Types': [ 'External Press', ],
            'Categories': [ 'Science', 'Event', ],
        }
        range_filters = {
            'Year': [ 2016, 2023 ], 
            'Press Mentions': [ 0, 10 ], 
        }

        selected = st_lib.filter_data( self.exploded, all_selected_columns, search_str, range_filters )

        assert np.invert( selected['Research Topics'] == 'Galaxies & Cosmology' ).sum() == 0
        assert np.invert( selected['Press Types'] == 'External Press' ).sum() == 0
        assert np.invert( ( selected['Categories'] == 'Science' ) | ( selected['Categories'] == 'Event' ) ).sum() == 0
        assert np.invert( ( 2016 <= selected['Year'] ) & ( selected['Year'] <= 2023 ) ).sum() == 0
        assert np.invert( ( 0 <= selected['Press Mentions'] ) & ( selected['Press Mentions'] <= 10 ) ).sum() == 0
    
    ###############################################################################

    def test_count( self ):

        selected = self.exploded
        weighting = 'Article Count'

        counts, total = st_lib.count( selected, self.group_by, weighting )

        test_year = 2015
        test_group = 'Galaxies & Cosmology'
        expected = len( pd.unique(
            selected.loc[(
                ( selected['Year'] == test_year ) &
                ( selected[self.group_by] == test_group )
            ),'id']
        ) )
        assert counts.loc[test_year,test_group] == expected

        # Total count
        test_year = 2015
        expected = len( pd.unique(
            selected.loc[(
                ( selected['Year'] == test_year )
            ),'id']
        ) )
        assert total.loc[test_year][0] == expected

    ###############################################################################

    def test_count_press_mentions( self ):

        selected = self.exploded
        weighting = 'Press Mentions'

        counts, total = st_lib.count( selected, self.group_by, weighting )

        test_year = 2015
        test_group = 'Galaxies & Cosmology'
        subselected = selected.loc[(
            ( selected['Year'] == test_year ) &
            ( selected[self.group_by] == test_group )
        )]
        subselected.drop_duplicates( subset='id', inplace=True )
        subselected.replace( 'N/A', 0, inplace=True )
        expected = subselected['Press Mentions'].sum()
        assert counts.loc[test_year,test_group] == expected

        # Total count
        test_year = 2015
        subselected = selected.loc[(
            ( selected['Year'] == test_year )
        )]
        subselected.drop_duplicates( subset='id', inplace=True )
        subselected.replace( 'N/A', 0, inplace=True )
        expected = subselected['Press Mentions'].sum()
        assert total.loc[test_year][0] == expected

    ###############################################################################

    def test_count_press_mentions_nonzero( self ):

        selected = self.exploded
        weighting = 'Press Mentions'

        counts = st_lib.count( selected, self.group_by, weighting )

        # Non-zero test
        test_year = 2021
        test_group = 'Gravitational Waves & Multi-Messenger Astronomy'
        subselected = selected.loc[(
            ( selected['Year'] == test_year ) &
            ( selected[self.group_by] == test_group )
        )]
        subselected.drop_duplicates( subset='id', inplace=True )
        subselected.replace( 'N/A', 0, inplace=True )
        expected = subselected['Press Mentions'].sum()
        assert expected > 0
        assert counts.loc[test_year,test_group] == expected
