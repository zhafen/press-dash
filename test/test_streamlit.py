import unittest

import glob
import fileinput
import numpy as np
import os
import pandas as pd
import shutil
import subprocess
import yaml

from root_dash_lib import dash_utils, data_utils, time_series_utils
from .lib_for_tests import press_data_utils

def copy_config( root_config_fp, config_fp ):

        # Copy and edit config
        with open( root_config_fp, 'r' ) as f:
            config_text = f.read()
        config_text = config_text.replace( '../data', '.' )
        config_text = config_text.replace( './', '')
        with open( config_fp, 'w' ) as f:
            f.write( config_text )

###############################################################################

class TestDashboardSetupPressData( unittest.TestCase ):
    '''This tests the setup for press data.
    '''

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.data_dir = os.path.join( self.root_dir, 'test_data', 'test_data_complete', )
        root_config_fp = os.path.join( self.root_dir, 'test', 'config.yml' )
        self.config_fp = os.path.join( self.data_dir, 'config.yml' )
        copy_config( root_config_fp, self.config_fp )

    def tearDown( self ):
        if os.path.isfile( self.config_fp ):
            os.remove( self.config_fp )

    ###############################################################################

    def test_load_config( self ):

        config = dash_utils.load_config( self.config_fp )

        assert config['color_palette'] == 'deep'

    ###############################################################################

    def test_load_original_data( self ):

        config = dash_utils.load_config( self.config_fp )

        original_df = press_data_utils.load_original_data( config )

        assert original_df.size > 0

    ###############################################################################

    def test_load_data( self ):

        config = dash_utils.load_config( self.config_fp )

        df = press_data_utils.load_data( config )

        assert df.size > 0 

    ###############################################################################

    def test_consistent_original_and_processed( self ):

        config = dash_utils.load_config( self.config_fp )

        original_df = press_data_utils.load_original_data( config )
        df = press_data_utils.load_data( config )

        for groupby_column in config['groupings']:
            subset_df = df[['id',groupby_column]].fillna( 'N/A' )
            subset_df = subset_df.drop_duplicates()
            grouped = subset_df.groupby('id')
            actual = grouped[groupby_column].apply( '|'.join )
            not_equal = actual != original_df[groupby_column]
            assert not_equal.sum() == 0
            np.testing.assert_array_equal(
                actual,
                original_df[groupby_column]
            )

###############################################################################
###############################################################################

class TestDataUtils( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.data_dir = os.path.join( self.root_dir, 'test_data', 'test_data_complete', )
        root_config_fp = os.path.join( self.root_dir, 'test', 'config.yml' )
        self.config_fp = os.path.join( self.data_dir, 'config.yml' )

        copy_config( root_config_fp, self.config_fp )

        self.group_by = 'Research Topics'
        self.config = dash_utils.load_config( self.config_fp )
        self.original_df = press_data_utils.load_original_data( self.config )
        self.df = press_data_utils.load_data( self.config )

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
        original_df = pd.DataFrame(data)
        data = {
            'id': [1, 1, 2, 2, 3],
            'Press Types': [ 'Northwestern Press', 'CIERA Press', 'External Press', 'CIERA Press', 'CIERA Press'],
            'Year': [ 2015, 2015, 2014, 2014, 2015 ],
        }
        df = pd.DataFrame(data)

        new_categories = {
            'Northwestern Press (Inclusive)': "'Northwestern Press' | ( 'Northwestern Press' & 'CIERA Press')",
        }

        df = data_utils.recategorize_data_per_grouping(
            df,
            groupby_column = 'Press Types',
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

        pd.testing.assert_series_equal( expected['Press Types'], df )

    ###############################################################################

    def test_recategorize_data_per_grouping_realistic( self ):

        group_by = 'Research Topics'
        recategorized = data_utils.recategorize_data_per_grouping(
            self.df,
            group_by,
            self.config['new_categories'][group_by],
            False,
        )

        # Check that compact objects is right
        not_included_groups = [
            'Stellar Dynamics & Stellar Populations',
            'Exoplanets & The Solar System',
            'Galaxies & Cosmology',
            'N/A',
        ]
        for group in not_included_groups:
            is_group = self.original_df[group_by].str.contains( group )
            is_compact = recategorized == 'Compact Objects'
            assert ( is_group.values & is_compact.values ).sum() == 0

        # Check that none of the singles categories shows up in other
        for group in pd.unique( self.df[group_by] ):
            is_group = self.original_df[group_by] == group
            is_other = recategorized == 'Other'
            is_bad = ( is_group.values & is_other.values )
            n_matched = is_bad.sum()
            # compare bad ids, good for debugging
            if n_matched > 0:
                bad_ids_original = self.original_df.index[is_bad]
                bad_ids_recategorized = recategorized.index[is_bad]
                np.testing.assert_allclose( bad_ids_original, bad_ids_recategorized )
            assert n_matched == 0

    ###############################################################################

    def test_recategorize_data( self ):

        recategorized = data_utils.recategorize_data(
            self.df,
            self.config['new_categories'],
            True,
        )

        # Check that NU Press inclusive is right
        group_by = 'Press Types'
        expected = (
            ( self.original_df[group_by] == 'CIERA Stories|Northwestern Press' ) |
            ( self.original_df[group_by] == 'Northwestern Press|CIERA Stories' ) |
            ( self.original_df[group_by] == 'Northwestern Press' )
        )
        actual = recategorized[group_by] == 'Northwestern Press (Inclusive)'
        np.testing.assert_allclose(
            actual.values,
            expected.values,
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
            is_group = self.original_df[group_by].str.contains( group )
            is_compact = recategorized[group_by] == 'Compact Objects'
            assert ( is_group.values & is_compact.values ).sum() == 0

        # Check that none of the singles categories shows up in other
        for group in pd.unique( self.df[group_by] ):
            is_group = self.original_df[group_by] == group
            is_other = recategorized[group_by] == 'Other'
            is_bad = ( is_group.values & is_other.values )
            n_matched = is_bad.sum()
            # compare bad ids, good for debugging
            if n_matched > 0:
                bad_ids_original = self.original_df.index[is_bad]
                bad_ids_recategorized = recategorized.loc[is_bad,'id']
                np.testing.assert_allclose( bad_ids_original, bad_ids_recategorized )
            assert n_matched == 0

    ###############################################################################

    def test_recategorize_data_rename( self ):

        new_categories = self.config['new_categories']
        new_categories['Also Research Topics [Research Topics]'] = {
            'Compact Objects': "only ('Life & Death of Stars' | 'Gravitational Waves & Multi-Messenger Astronomy' | 'Black Holes & Dead Stars' )",
            'Cosmological Populations': "only ('Galaxies & Cosmology' | 'Stellar Dynamics & Stellar Populations' )",
        }
        recategorized = data_utils.recategorize_data(
            self.df,
            new_categories,
            True,
        )

        is_bad = recategorized['Also Research Topics'] != recategorized['Research Topics']
        n_bad = is_bad.sum()
        assert n_bad == 0

    ###############################################################################

    def test_filter_data( self ):

        search_str = ''
        categorical_filters = {
            'Research Topics': [ 'Galaxies & Cosmology', ],
            'Press Types': [ 'External Press', ],
            'Categories': [ 'Science', 'Event', ],
        }
        range_filters = {
            'Year': [ 2016, 2023 ], 
            'Press Mentions': [ 0, 10 ], 
        }

        selected = data_utils.filter_data(
            self.df,
            search_str,
            'Title',
            categorical_filters,
            range_filters
        )

        assert np.invert( selected['Research Topics'] == 'Galaxies & Cosmology' ).sum() == 0
        assert np.invert( selected['Press Types'] == 'External Press' ).sum() == 0
        assert np.invert( ( selected['Categories'] == 'Science' ) | ( selected['Categories'] == 'Event' ) ).sum() == 0
        assert np.invert( ( 2016 <= selected['Year'] ) & ( selected['Year'] <= 2023 ) ).sum() == 0
        assert np.invert( ( 0 <= selected['Press Mentions'] ) & ( selected['Press Mentions'] <= 10 ) ).sum() == 0

###############################################################################
    
class TestTimeSeriesUtils( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.data_dir = os.path.join( self.root_dir, 'test_data', 'test_data_complete', )
        root_config_fp = os.path.join( self.root_dir, 'test', 'config.yml' )
        self.config_fp = os.path.join( self.data_dir, 'config.yml' )

        copy_config( root_config_fp, self.config_fp )

        self.group_by = 'Research Topics'
        self.config = dash_utils.load_config( self.config_fp )
        self.original_df = press_data_utils.load_original_data( self.config )
        self.df = press_data_utils.load_data( self.config )

    def tearDown( self ):
        if os.path.isfile( self.config_fp ):
            os.remove( self.config_fp )

    ###############################################################################

    def test_count( self ):

        selected = self.df

        counts, total = time_series_utils.count(
            selected,
            'Year',
            'id',
            self.group_by
        )

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

    def test_sum_press_mentions( self ):

        selected = self.df
        weighting = 'Press Mentions'

        sums, total = time_series_utils.count(
            selected,
            'Year',
            weighting,
            self.group_by,
        )

        test_year = 2015
        test_group = 'Galaxies & Cosmology'
        subselected = selected.loc[(
            ( selected['Year'] == test_year ) &
            ( selected[self.group_by] == test_group )
        )]
        subselected = subselected.drop_duplicates( subset='id' )
        subselected = subselected.replace( 'N/A', 0, )
        expected = subselected['Press Mentions'].sum()
        assert sums.loc[test_year,test_group] == expected

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

        selected = self.df
        weighting = 'Press Mentions'

        sums, total = time_series_utils.sum(
            selected,
            'Year',
            weighting,
            self.group_by,
        )

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
        assert sums.loc[test_year,test_group] == expected

        # Total count
        test_year = 2021
        subselected = selected.loc[(
            ( selected['Year'] == test_year )
        )]
        subselected = subselected.drop_duplicates( subset='id' )
        subselected = subselected.replace( 'N/A', 0 )
        expected = subselected['Press Mentions'].sum()
        assert total.loc[test_year][0] == expected

