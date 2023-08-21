'''General-purpose functions for relational data-analysis.
Most functions should be useful for most relational datasets.
'''
import copy
import numpy as np
import os
import pandas as pd
import re
import streamlit as st
import yaml

import matplotlib
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import seaborn as sns

################################################################################

def get_year( date, start_of_year='January 1', years_min=None, years_max=None ):
    '''Get the year from a date, with a user-specified start date
    for the year.

    Args:
        date (datetime.datetime): The date to get the year from.
        start_of_year (str): The start of the year, e.g. 'January 1'.
        years_min (int): The minimum year to include. Defaults to the minimum year in the data.
        years_max (int): The maximum year to include. Defaults to the maximum year in the data.

    Returns:
        years (pd.Series of int): The year of the date.
    '''

    # Get date bins
    if years_min is None:
        years_min = date.min().year - 1
    if years_max is None:
        years_max = date.max().year + 1
    date_bins = pd.date_range(
        '{} {}'.format( start_of_year, years_min ),
        pd.Timestamp.now() + pd.offsets.DateOffset( years=1 ),
        freq = pd.offsets.DateOffset( years=1 ),
    )
    date_bin_labels = date_bins.year[:-1]

    # The actual binning
    years = pd.cut( date, date_bins, labels=date_bin_labels ) 

    return years

################################################################################

def recategorize_data(
        df,
        new_categories,
        recategorize=True,
        combine_single_categories=False
    ):
    '''Recategorize the data, i.e. combine existing categories into new ones.
    The end result is one category per article, so no articles are double-counted.
    However, if the new categories are ill-defined they can contradict one another
    and lead to inconsistencies.

    Args:
        df (pd.DataFrame): The dataframe containing the original data.
        new_categories (dict): The new categories to use.
        recategorize (bool): Whether to recategorize the data. Included for caching.

    Returns:
        recategorized (pd.DataFrame): The dataframe containing the recategorized data.
            One entry per article.
    '''

    # We include the automatic return to help with data caching.
    if not recategorize:
        return df
    
    # Get the condensed data frame
    # This is probably dropping stuff that shouldn't be dropped!!!!!!!
    recategorized = df.drop_duplicates( subset='id', keep='first' )
    recategorized.set_index( 'id', inplace=True )

    for groupby_column, new_categories_per_grouping in new_categories.items():

        # Look for columns that are re-definitions of existing columns
        # This regex looks for anything in front of anything else in brackets
        search = re.findall( r'(.*?)\s\[(.+)\]', groupby_column )
        if len( search ) == 0:
            new_column = groupby_column
        elif len( search ) == 1:
            new_column, groupby_column = search[0]
        else:
            raise KeyError( 'New categories cannot have multiple sets of brackets.' )

        recategorized_groupby = recategorize_data_per_grouping(
            df,
            groupby_column,
            copy.deepcopy( new_categories_per_grouping ),
            combine_single_categories
        )
        recategorized[new_column] = recategorized_groupby

    recategorized.reset_index( inplace=True )
    return recategorized

################################################################################

def recategorize_data_per_grouping(
        df,
        groupby_column,
        new_categories_per_grouping,
        combine_single_categories=False
    ):
    '''The actual function doing most of the recategorizing.

    Args:
        df (pd.DataFrame): The dataframe containing the original data.
        groupby_column (str): The category to group the data by, e.g. 'Research Topics'. 
        new_categories_per_grouping (dict): The new categories to use for this specific grouping.

    Returns:
        recategorized (pd.Series): The new categories.
    '''

    # Get the formatted data used for the categories
    dummies = pd.get_dummies( df[groupby_column] )
    dummies['id'] = df['id']
    dummies_grouped = dummies.groupby( 'id' )
    bools = dummies_grouped.sum() >= 1
    n_cats = bools.sum( axis='columns' )
    if bools.values.max() > 1:
        raise ValueError(
            'Categorization cannot proceed---' +
            'At least one category shows up multiple times for a single ID.'
        )

    # Setup return arr
    base_categories = bools.columns
    recategorized_dtype = np.array( new_categories_per_grouping.keys() ).dtype
    recategorized = np.full( len(bools), fill_value='Other', dtype=recategorized_dtype )
    recategorized = pd.Series( recategorized, index=bools.index, name=groupby_column )

    if not combine_single_categories:
        # Do all the single-category entries
        # These will be overridden if any are a subset of a new category
        bools_singles = bools.loc[n_cats == 1]
        for base_category in base_categories:
            is_base_cat = bools_singles[base_category].values
            recategorized.loc[bools_singles.index[is_base_cat]] = base_category

    # Loop through and do the recategorization
    for category_key, category_definition in new_categories_per_grouping.items():
        # Replace the definition with something that can be evaluated
        not_included_cats = []
        for base_category in base_categories:
            if base_category not in category_definition:
                not_included_cats.append( base_category )
                continue
            category_definition = category_definition.replace(
                "'{}'".format( base_category ),
                "row['{}']".format( base_category )
            )
        # Handle the not-included categories
        if 'only' in category_definition:
            category_definition = (
                '(' + category_definition + ') & ( not ( ' +
                ' | '.join(
                    [ "row['{}']".format( cat ) for cat in not_included_cats ]
                ) + ' ) )'
            )
            category_definition = category_definition.replace( 'only', '' )
        is_new_cat = bools.apply( lambda row: eval( category_definition ), axis='columns' )
        recategorized[is_new_cat] = category_key
        
    return recategorized

################################################################################

def filter_data( df, search_str, search_col, categorical_filters, numerical_filters ):
    '''Filter what data shows up in the dashboard.

    Args:
        df (pd.DataFrame): The dataframe containing the data.
        search_str (str): What to search the data for.
        search_col (str): What column to search
        categorical_filters (dict): How categories are filtered.
        numerical_filters (dict): Ranges for numerical data filters

    Returns:
        selected_df (pd.DataFrame): The dataframe containing the selected data.
    '''

    # # Search filter
    if search_str != '':
        is_included = df[search_col].str.extract( '(' + search_str + ')', flags=re.IGNORECASE ).notna().values[:,0]
    else:
        is_included = np.ones( len( df ), dtype=bool )

    # Categories filter
    for cat_filter_col, selected_cats in categorical_filters.items():
        is_included = is_included & df[cat_filter_col].isin( selected_cats )

    # Range filters
    for num_filter_col, column_range in numerical_filters.items():
        is_included = is_included & (
            ( column_range[0] <= df[num_filter_col] ) &
            ( df[num_filter_col] <= column_range[1] )
        )

    selected_df = df.loc[is_included]
    return selected_df