import ast
import copy
import numpy as np
import os
import pandas as pd
import re
import streamlit as st
import yaml
from sympy import symbols, parse_expr

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import seaborn as sns

################################################################################

def load_config( config_fp ):
    '''Get the config. Do this only once.
    '''

    # Check if we're in the directory the script is in,
    # which should also be the directory the config is in.
    # If not, move into that directory
    config_dir = os.path.dirname( config_fp )
    if os.getcwd() != config_dir:
        os.chdir( config_dir )

    with open( './config.yml', "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

################################################################################

def load_original_data( config ):

    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    press_fp = os.path.join( output_dir, config['combined_filename'] )
    df = pd.read_csv( press_fp, index_col=0 )

    df[['Press Mentions', 'People Reached']] = df[['Press Mentions','People Reached']].fillna( value=0 )
    df.fillna( value='N/A', inplace=True )

    return df

################################################################################

def load_exploded_data( config, group_by ):

    remaining_groupings = copy.copy( config['groupings'] )
    remaining_groupings.remove( group_by )

    base, ext = os.path.splitext( config['combined_filename'] )
    exploded_filename = '{}.exploded{}'.format( base, ext )
    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    exploded_fp = os.path.join( output_dir, exploded_filename )
    exploded = pd.read_csv( exploded_fp )

    # Handle NaNs and such
    exploded[['Press Mentions', 'People Reached']] = exploded[['Press Mentions','People Reached']].fillna( value=0 )
    exploded.fillna( value='N/A', inplace=True )

    return exploded, remaining_groupings, category_colors

################################################################################

def recategorize_data( df, exploded, new_categories, recategorize ):

    if not recategorize:
        return exploded

    recategorized = df.copy()
    for group_by, new_categories_per_grouping in new_categories.items():
        recategorized[group_by] = recategorize_data_per_grouping(
            exploded,
            group_by,
            copy.deepcopy( new_categories_per_grouping ),
        )

    recategorized.reset_index( inplace=True )
    return recategorized

################################################################################

def recategorize_data_per_grouping( exploded, group_by, new_categories_per_grouping ):

    # Get the formatted data used for the categories
    dummies = pd.get_dummies( exploded[group_by] )
    dummies['id'] = exploded['id']
    dummies_grouped = dummies.groupby( 'id' )
    bools = dummies_grouped.sum().astype( bool )
    n_cats = dummies_grouped['id'].count()
    if bools.values.max() > 1:
        raise ValueError(
            'Categorization cannot proceed---' +
            'At least one category shows up multiple times for a single ID.'
        )

    # Setup return arr
    base_categories = bools.columns
    recategorized_dtype = np.array( new_categories_per_grouping.keys() ).dtype
    recategorized = np.full( len(bools), fill_value='Other', dtype=recategorized_dtype )

    # Do all the single-category entries
    # These will be overridden if any are a subset of a new category
    is_single_cat = dummies_grouped['id'].count() == 1
    for base_category in base_categories:
        recategorized[bools[base_category]&is_single_cat] = base_category

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
        
    return pd.Series( recategorized, index=bools.index, name=group_by )

################################################################################

def filter_data( exploded, selected_groups, search_str, range_filters ):
    '''Filter the data shown.'''

    # Search filter
    is_included = exploded['Title'].str.extract( '(' + search_str + ')', flags=re.IGNORECASE ).notna().values[:,0]

    # Categories filter
    for group_by_i, groups in selected_groups.items():
        is_included = is_included & exploded[group_by_i].isin( groups )

    # Range filters
    for column, column_range in range_filters.items():
        is_included = is_included & (
            ( column_range[0] <= exploded[column] ) &
            ( exploded[column] <= column_range[1] )
        )

    selected = exploded.loc[is_included]
    return selected

################################################################################

def count( selected, group_by, weighting ):
    '''Count up stats.'''

    # Nice simple case
    if weighting == 'Article Count':
        counts = selected.pivot_table( index='Year', columns=group_by, values='id', aggfunc='nunique' )
        total = selected.pivot_table( index='Year', values='id', aggfunc='nunique' )

    # More-complicated alternative
    else:
        def aggfunc( df_agg ):
            df_agg = df_agg.drop_duplicates( 'id', keep='first' )
            return df_agg[weighting].sum()
        counts = selected.pivot_table(
            values=[weighting,'id'],
            index='Year',
            columns=group_by,
            aggfunc=aggfunc
        )
        total = selected.pivot_table(
            values=[weighting,'id'],
            index='Year',
            aggfunc=aggfunc
        )

    # Replace the Nones with zeroes
    counts = counts.fillna( 0 )
    total = total.fillna( 0 )

    return counts, total

################################################################################

def plot_counts( counts, total, plot_kw ):

    if plot_kw['cumulative']:
        counts = counts.cumsum( axis='rows' )
        total = total.cumsum()

    years = counts.index
    categories = counts.columns

    sns.set_style( plot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")

    fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
    ax = plt.gca()
    for j, category_j in enumerate( categories ):

        ys = counts[category_j]

        ax.plot(
            years,
            ys,
            linewidth = plot_kw['linewidth'],
            alpha = 0.5,
            zorder = 2,
            color = plot_kw['category_colors'][category_j],
        )
        ax.scatter(
            years,
            ys,
            label = category_j,
            zorder = 2,
            color = plot_kw['category_colors'][category_j],
            s = plot_kw['marker_size'],
        )
    if plot_kw['show_total']:
        ax.plot(
            years,
            total,
            linewidth = plot_kw['linewidth'],
            alpha = 0.5,
            color = 'k',
            zorder = 1,
        )
        ax.scatter(
            years,
            total,
            label = 'Total',
            color = 'k',
            zorder = 1,
            s = plot_kw['marker_size'],
        )

    ymax = plot_kw['y_lim'][1]

    ax.set_xticks( years )
    count_ticks = np.arange( 0, ymax, plot_kw['tick_spacing'] )
    ax.set_yticks( count_ticks )

    ax.set_xlim( years[0], years[-1] )
    ax.set_ylim( plot_kw['y_lim'] )

    l = ax.legend(
        bbox_to_anchor = ( plot_kw['legend_x'], plot_kw['legend_y'] ),
        loc = 'lower left', 
        framealpha = 1.,
        fontsize = plot_context['legend.fontsize'] * plot_kw['legend_scale'],
        ncol = len( categories ) // 4 + 1
    )

    # Labels, inc. size
    ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
    ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
    ax.tick_params( labelsize=plot_context['xtick.labelsize']*plot_kw['font_scale'] )

    # return facet_grid
    return fig

################################################################################

def plot_fractions( counts, stackplot_kw ):

    sns.set_style( stackplot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")

    if stackplot_kw['cumulative']:
        counts = counts.cumsum( axis='rows' )

    years = counts.index
    categories = counts.columns

    # Get data
    total = counts.sum( axis='columns' )
    fractions = counts.mul( 1./total, axis='rows' ).fillna( value=0. )
    
    fig = plt.figure( figsize=( stackplot_kw['fig_width'], stackplot_kw['fig_height'] ) )
    ax = plt.gca()
    
    stack = ax.stackplot(
        years,
        fractions.values.transpose(),
        linewidth = 0.3,
        colors = [ stackplot_kw['category_colors'][category_j] for category_j in categories ],
    )
    ax.set_xlim( years[0], years[-1] )
    ax.set_ylim( 0, 1. )
    ax.set_xticks( years )
    ax.set_ylabel( 'Fraction of Articles' )

    # Add labels
    for j, poly_j in enumerate( stack ):

        # The y labels are centered in the middle of the last band
        vertices = poly_j.get_paths()[0].vertices
        xs = vertices[:,0]
        end_vertices = vertices[:,1][xs == xs.max()]
        label_y = 0.5 * ( end_vertices.min() + end_vertices.max() )

        text = ax.annotate(
            text = fractions.columns[j],
            xy = ( 1, label_y ),
            xycoords = matplotlib.transforms.blended_transform_factory( ax.transAxes, ax.transData ),
            xytext = ( -5 + 10 * ( stackplot_kw['horizontal_alignment'] == 'left' ), 0 ),
            va = 'center',
            ha = stackplot_kw['horizontal_alignment'],
            textcoords = 'offset points',
        )
        text.set_path_effects([
            path_effects.Stroke(linewidth=2.5, foreground='w'),
            path_effects.Normal(),
        ])

    # Labels, inc. size
    ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * stackplot_kw['font_scale'] )
    ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * stackplot_kw['font_scale'] )
    ax.tick_params( labelsize=plot_context['xtick.labelsize']*stackplot_kw['font_scale'] )

    return fig
