import unittest

import glob
import fileinput
import numpy as np
import os
import pandas as pd
import shutil
import subprocess
import yaml

from press_dash_lib import streamlit_utils as st_lib

def copy_config( root_config_fp, config_fp ):

        # Copy and edit config
        with open( root_config_fp, 'r' ) as f:
            config_text = f.read()
        config_text = config_text.replace( '../data', '.' )
        config_text = config_text.replace( './', '')
        with open( config_fp, 'w' ) as f:
            f.write( config_text )

###############################################################################

class TestDashboardSetup( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.data_dir = os.path.join( self.root_dir, 'test_data', 'test_data_complete', )
        root_config_fp = os.path.join( self.root_dir, 'src', 'config.yml' )
        self.config_fp = os.path.join( self.data_dir, 'config.yml' )
        copy_config( root_config_fp, self.config_fp )

    def tearDown( self ):
        if os.path.isfile( self.config_fp ):
            os.remove( self.config_fp )

    ###############################################################################

    def test_load_config( self ):

        config = st_lib.load_config( self.config_fp )

        assert config['color_palette'] == 'deep'

    ###############################################################################

    def test_load_original_data( self ):

        config = st_lib.load_config( self.config_fp )

        df = st_lib.load_original_data( config )

        assert df.size > 0

    ###############################################################################

    def test_load_exploded_data( self ):

        group_by = 'Research Topics'

        config = st_lib.load_config( os.path.join( self.root_dir, 'src', 'dashboard.py' ) )
        exploded, remaining_groupings = st_lib.load_exploded_data( config, group_by )

        assert exploded.size > 0 

###############################################################################
###############################################################################

class TestDashboard( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.data_dir = os.path.join( self.root_dir, 'test_data', 'test_data_complete', )
        root_config_fp = os.path.join( self.root_dir, 'src', 'config.yml' )
        self.config_fp = os.path.join( self.data_dir, 'config.yml' )

        copy_config( root_config_fp, self.config_fp )

        self.group_by = 'Research Topics'
        self.config = st_lib.load_config( self.config_fp )
        self.df = st_lib.load_original_data( self.config )
        self.exploded, self.remaining_groupings = st_lib.load_exploded_data( self.config, self.group_by )

    def tearDown( self ):
        if os.path.isfile( self.config_fp ):
            os.remove( self.config_fp )

    ###############################################################################

    def test_recategorize_data_per_group( self ):

        # Test Dataset
        data = {
            'id': [1, 2, 3],
            'Press Types': [ 'Northwestern Press|CIERA Press', 'External Press|CIERA Press', 'CIERA Press'],
            'Year': [ 2015, 2014, 2015 ],
        }
        df = pd.DataFrame(data)
        data = {
            'id': [1, 1, 2, 2, 3],
            'Press Types': [ 'Northwestern Press', 'CIERA Press', 'External Press', 'CIERA Press', 'CIERA Press'],
            'Year': [ 2015, 2015, 2014, 2014, 2015 ],
        }
        exploded = pd.DataFrame(data)

        new_categories = {
            'Northwestern Press (Inclusive)': "'Northwestern Press' | ( 'Northwestern Press' & 'CIERA Press')",
        }

        exploded = st_lib.recategorize_data_per_grouping(
            df,
            exploded,
            group_by = 'Press Types',
            new_categories_per_grouping = new_categories,
        )

        # Build up expected data
        expected = pd.DataFrame(
            data = {
                'id': [ 1, 2, 3, ],
                'Press Types': [ 'Northwestern Press (Inclusive)', 'Other', 'CIERA Press' ],
                'Year': [ 2015, 2014, 2015 ],
            },
        )
        expected.set_index( 'id', inplace=True )

        pd.testing.assert_series_equal( expected['Press Types'], exploded )

    ###############################################################################

    def test_recategorize_data( self ):

        recategorized = st_lib.recategorize_data(
            self.df,
            self.exploded,
            self.config['new_categories'],
            True,
        )

        # Check that NU Press inclusive is right
        group_by = 'Press Types'
        expected = (
            ( self.df[group_by] == 'CIERA Stories|Northwestern Press' ) |
            ( self.df[group_by] == 'Northwestern Press|CIERA Stories' ) |
            ( self.df[group_by] == 'Northwestern Press' )
        )
        actual = recategorized[group_by] == 'Northwestern Press (Inclusive)'
        np.testing.assert_allclose(
            actual,
            expected
        )

        # Check that compact objects is right
        group_by = 'Research Topics'
        not_included_groups = [
            'Stellar Dynamics & Stellar Populations',
            'Exoplanets & The Solar System',
            'Galaxies & Cosmology',
            'N/A',
        ]
        for group in not_included_groups:
            is_group = self.df[group_by].str.contains( group )
            is_compact = recategorized[group_by] == 'Compact Objects'
            assert ( is_group.values & is_compact.values ).sum() == 0

        # Check that Other is right
        for group in pd.unique( self.exploded[group_by] ):
            is_group = self.df[group_by] == group
            is_other = recategorized[group_by] == 'Other'
            is_bad = ( is_group.values & is_other.values )
            n_matched = is_bad.sum()
            assert n_matched == 0

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
        subselected = subselected.drop_duplicates( subset='id' )
        subselected = subselected.replace( 'N/A', 0, )
        expected = subselected['Press Mentions'].sum()
        assert counts.loc[test_year,test_group] == expected

        # Total count
        test_year = 2015
        subselected = selected.loc[(
            ( selected['Year'] == test_year )
        )]
        subselected = subselected.drop_duplicates( subset='id' )
        subselected = subselected.replace( 'N/A', 0, )
        expected = subselected['Press Mentions'].sum()
        assert total.loc[test_year][0] == expected

    ###############################################################################

    def test_count_press_mentions_nonzero( self ):

        selected = self.exploded
        weighting = 'Press Mentions'

        counts, total = st_lib.count( selected, self.group_by, weighting )

        # Non-zero test
        test_year = 2021
        test_group = 'Gravitational Waves & Multi-Messenger Astronomy'
        subselected = selected.loc[(
            ( selected['Year'] == test_year ) &
            ( selected[self.group_by] == test_group )
        )]
        subselected = subselected.drop_duplicates( subset='id' )
        subselected = subselected.replace( 'N/A', 0 )
        expected = subselected['Press Mentions'].sum()
        assert expected > 0
        assert counts.loc[test_year,test_group] == expected

        # Total count
        test_year = 2021
        subselected = selected.loc[(
            ( selected['Year'] == test_year )
        )]
        subselected = subselected.drop_duplicates( subset='id' )
        subselected = subselected.replace( 'N/A', 0 )
        expected = subselected['Press Mentions'].sum()
        assert total.loc[test_year][0] == expected

