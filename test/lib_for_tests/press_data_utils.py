import copy
import numpy as np
import os
import pandas as pd
import re
import streamlit as st
import yaml

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import seaborn as sns

################################################################################

# def load_config( config_fp ):
#     '''Get the config. This is done once per session.
#     The config directory is set as the working directory,
#     and the config must be named config.yml.
# 
#     Args:
#         config_fp (str): The filepath to the config file.
# 
#     Returns:
#         config (dict): The config dictionary.
#     '''
# 
#     # Check if we're in the directory the script is in,
#     # which should also be the directory the config is in.
#     # If not, move into that directory
#     config_dir = os.path.dirname( config_fp )
#     if os.getcwd() != config_dir:
#         os.chdir( config_dir )
# 
#     with open( './config.yml', "r") as f:
#         config = yaml.load(f, Loader=yaml.FullLoader)
#     return config
# 
################################################################################

def load_original_data( config ):
    '''Load the merged-but-unprocessed data.

    Args:
        config (dict): The config dictionary.

    Returns:
        original_df (pd.DataFrame): The dataframe containing the original data.
    '''

    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    press_fp = os.path.join( output_dir, config['combined_filename'] )
    original_df = pd.read_csv( press_fp, index_col=0 )

    original_df[['Press Mentions', 'People Reached']] = original_df[['Press Mentions','People Reached']].fillna( value=0 )
    original_df.fillna( value='N/A', inplace=True )

    return original_df

################################################################################

def load_data( config ):
    '''Load the df data. (df means one row per category.)
    https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.explode.html

    Args:
        config (dict): The config dictionary.
        group_by (str): The category to group the data by, e.g. 'Research Topics'.

    Returns:
        df (pd.DataFrame): The dataframe containing the df data.
    '''

    base, ext = os.path.splitext( config['combined_filename'] )
    df_filename = '{}.exploded{}'.format( base, ext )
    output_dir = os.path.join( config['data_dir'], config['output_dirname'] )
    df_fp = os.path.join( output_dir, df_filename )
    df = pd.read_csv( df_fp )

    return df

################################################################################

def preprocess_data( df ):

    # Handle NaNs and such
    df[['Press Mentions', 'People Reached']] = df[['Press Mentions','People Reached']].fillna( value=0 )
    df.fillna( value='N/A', inplace=True )

    return df

# ################################################################################
# 
# def recategorize_data( original_df, df, new_categories, recategorize=True ):
#     '''Recategorize the data, i.e. combine existing categories into new ones.
#     The end result is one category per article, so no articles are double-counted.
#     However, if the new categories are ill-defined they can contradict one another
#     and lead to inconsistencies.
# 
#     Args:
#         original_df (pd.DataFrame): The dataframe containing the original data.
#         df (pd.DataFrame): The dataframe containing the df data.
#         new_categories (dict): The new categories to use.
#         recategorize (bool): Whether to recategorize the data. Included for caching.
# 
#     Returns:
#         recategorized (pd.DataFrame): The dataframe containing the recategorized data.
#             One entry per article.
#     '''
# 
#     # We include the automatic return to help with data caching.
#     if not recategorize:
#         return df
# 
#     recategorized = original_df.copy()
#     for group_by, new_categories_per_grouping in new_categories.items():
#         recategorized[group_by] = recategorize_data_per_grouping(
#             original_df,
#             df,
#             group_by,
#             copy.deepcopy( new_categories_per_grouping ),
#         )
# 
#     recategorized.reset_index( inplace=True )
#     return recategorized
# 
# ################################################################################
# 
# def recategorize_data_per_grouping( original_df, df, group_by, new_categories_per_grouping ):
#     '''The actual function doing most of the recategorizing.
# 
#     Args:
#         original_df (pd.DataFrame): The dataframe containing the original data.
#         df (pd.DataFrame): The dataframe containing the df data.
#         group_by (str): The category to group the data by, e.g. 'Research Topics'. 
#         new_categories_per_grouping (dict): The new categories to use for this specific grouping.
# 
#     Returns:
#         recategorized (pd.Series): The new categories.
#     '''
# 
#     # Get the formatted data used for the categories
#     dummies = pd.get_dummies( df[group_by] )
#     dummies['id'] = df['id']
#     dummies_grouped = dummies.groupby( 'id' )
#     bools = dummies_grouped.sum().astype( bool )
#     n_cats = dummies_grouped['id'].count()
#     if bools.values.max() > 1:
#         raise ValueError(
#             'Categorization cannot proceed---' +
#             'At least one category shows up multiple times for a single ID.'
#         )
# 
#     # Setup return arr
#     base_categories = bools.columns
#     recategorized_dtype = np.array( new_categories_per_grouping.keys() ).dtype
#     recategorized = np.full( len(bools), fill_value='Other', dtype=recategorized_dtype )
# 
#     # Do all the single-category entries
#     # These will be overridden if any are a subset of a new category
#     for base_category in base_categories:
#         is_base_cat_only = ( original_df[group_by] == base_category ).values
#         recategorized[is_base_cat_only] = base_category
# 
#     # Loop through and do the recategorization
#     for category_key, category_definition in new_categories_per_grouping.items():
#         # Replace the definition with something that can be evaluated
#         not_included_cats = []
#         for base_category in base_categories:
#             if base_category not in category_definition:
#                 not_included_cats.append( base_category )
#                 continue
#             category_definition = category_definition.replace(
#                 "'{}'".format( base_category ),
#                 "row['{}']".format( base_category )
#             )
#         # Handle the not-included categories
#         if 'only' in category_definition:
#             category_definition = (
#                 '(' + category_definition + ') & ( not ( ' +
#                 ' | '.join(
#                     [ "row['{}']".format( cat ) for cat in not_included_cats ]
#                 ) + ' ) )'
#             )
#             category_definition = category_definition.replace( 'only', '' )
#         is_new_cat = bools.apply( lambda row: eval( category_definition ), axis='columns' )
#         recategorized[is_new_cat] = category_key
#         
#     return pd.Series( recategorized, index=bools.index, name=group_by )
# 
# ################################################################################
# 
# def filter_data( df, selected_groups, search_str, range_filters ):
#     '''Filter what data shows up in the dashboard.
# 
#     Args:
#         df (pd.DataFrame): The dataframe containing the df data.
#         selected_groups (list): What categories to include.
#         search_str (str): What to search for in the title.
#         range_filters (dict of tuples): What numeric-data ranges to include.
# 
#     Returns:
#         selected (pd.DataFrame): The dataframe containing the selected data.
#     '''
# 
#     # Search filter
#     is_included = df['Title'].str.extract( '(' + search_str + ')', flags=re.IGNORECASE ).notna().values[:,0]
# 
#     # Categories filter
#     for group_by_i, groups in selected_groups.items():
#         is_included = is_included & df[group_by_i].isin( groups )
# 
#     # Range filters
#     for column, column_range in range_filters.items():
#         is_included = is_included & (
#             ( column_range[0] <= df[column] ) &
#             ( df[column] <= column_range[1] )
#         )
# 
#     selected = df.loc[is_included]
#     return selected
# 
# ################################################################################
# 
# def count( selected, group_by, weighting ):
#     '''Count up stats, e.g. number of articles per year per category or
#     the number of people reached per year per category.
# 
#     Args:
#         selected (pd.DataFrame): The dataframe containing the selected data.
#         group_by (str): The category to group the data by, e.g. 'Research Topics'.
#         weighting (str): What to weight the counts by, e.g. 'Article Count' or 'People Reached'.
# 
#     Returns:
#         counts (pd.DataFrame): The dataframe containing the counts per year per category.
#         total (pd.Series): The series containing the counts per year, overall.
#     '''
# 
#     # Nice simple case
#     if weighting == 'Article Count':
#         counts = selected.pivot_table( index='Year', columns=group_by, values='id', aggfunc='nunique' )
#         total = selected.pivot_table( index='Year', values='id', aggfunc='nunique' )
# 
#     # More-complicated alternative
#     else:
#         # We keep one entry per ID and group. This is to avoid double-counting.
#         selected_for_sum = selected.copy()
#         selected_for_sum['id_and_group'] = selected['id'].astype( str ) + selected[group_by]
#         selected_for_sum.drop_duplicates( subset='id_and_group', keep='first', inplace=True )
#         counts = selected_for_sum.pivot_table(
#             values=weighting,
#             index='Year',
#             columns=group_by,
#             aggfunc='sum'
#         )
#         # For total we only need one entry per ID.
#         selected_for_sum.drop_duplicates( subset='id', keep='first', inplace=True )
#         total = selected_for_sum.pivot_table(
#             values=weighting,
#             index='Year',
#             aggfunc='sum'
#         )
# 
#     # Replace the Nones with zeroes
#     counts = counts.fillna( 0 )
#     total = total.fillna( 0 )
# 
#     return counts, total
# 
# ################################################################################
# 
# def plot_counts( counts, total, plot_kw ):
#     '''Function to plot the counts.
# 
#     Args:
#         counts (pd.DataFrame): The dataframe containing the counts per year per category.
#         total (pd.Series): The series containing the counts per year, overall.
#         plot_kw (dict): The plotting keywords. Typically set things like font size, figure dimensions, etc.
# 
#     Returns:
#         fig (matplotlib.figure.Figure): The figure containing the plot.
#     '''
# 
#     if plot_kw['cumulative']:
#         counts = counts.cumsum( axis='rows' )
#         total = total.cumsum()
# 
#     years = counts.index
#     categories = counts.columns
# 
#     sns.set( font=plot_kw['font'], style=plot_kw['seaborn_style'] )
#     plot_context = sns.plotting_context("notebook")
# 
#     fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
#     ax = plt.gca()
#     for j, category_j in enumerate( categories ):
# 
#         ys = counts[category_j]
# 
#         ax.plot(
#             years,
#             ys,
#             linewidth = plot_kw['linewidth'],
#             alpha = 0.5,
#             zorder = 2,
#             color = plot_kw['category_colors'][category_j],
#         )
#         ax.scatter(
#             years,
#             ys,
#             label = category_j,
#             zorder = 2,
#             color = plot_kw['category_colors'][category_j],
#             s = plot_kw['marker_size'],
#         )
#     if plot_kw['show_total']:
#         ax.plot(
#             years,
#             total,
#             linewidth = plot_kw['linewidth'],
#             alpha = 0.5,
#             color = 'k',
#             zorder = 1,
#         )
#         ax.scatter(
#             years,
#             total,
#             label = 'Total',
#             color = 'k',
#             zorder = 1,
#             s = plot_kw['marker_size'],
#         )
# 
#     ymax = plot_kw['y_lim'][1]
# 
#     ax.set_xticks( years )
#     count_ticks = np.arange( 0, ymax, plot_kw['tick_spacing'] )
#     ax.set_yticks( count_ticks )
# 
#     ax.set_xlim( years[0], years[-1] )
#     ax.set_ylim( plot_kw['y_lim'] )
# 
#     l = ax.legend(
#         bbox_to_anchor = ( plot_kw['legend_x'], plot_kw['legend_y'] ),
#         loc = 'lower left', 
#         framealpha = 1.,
#         fontsize = plot_context['legend.fontsize'] * plot_kw['legend_scale'],
#         ncol = len( categories ) // 4 + 1
#     )
# 
#     # Labels, inc. size
#     ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
#     ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
#     ax.tick_params( labelsize=plot_context['xtick.labelsize']*plot_kw['font_scale'] )
# 
#     # return facet_grid
#     return fig
# 
# ################################################################################
# 
# def plot_fractions( counts, stackplot_kw ):
#     '''Function to plot the relative contribution of the categories.
# 
#     Args:
#         counts (pd.DataFrame): The dataframe containing the counts per year per category.
#         stackplot_kw (dict): The plotting keywords. Typically set things like font size, figure dimensions, etc.
# 
#     Returns:
#         fig (matplotlib.figure.Figure): The figure containing the plot.
#     '''
# 
#     sns.set( font=stackplot_kw['font'], style=stackplot_kw['seaborn_style'] )
#     plot_context = sns.plotting_context("notebook")
# 
# 
#     if stackplot_kw['cumulative']:
#         counts = counts.cumsum( axis='rows' )
# 
#     years = counts.index
#     categories = counts.columns
# 
#     # Get data
#     total = counts.sum( axis='columns' )
#     fractions = counts.mul( 1./total, axis='rows' ).fillna( value=0. )
#     
#     fig = plt.figure( figsize=( stackplot_kw['fig_width'], stackplot_kw['fig_height'] ) )
#     ax = plt.gca()
#     
#     stack = ax.stackplot(
#         years,
#         fractions.values.transpose(),
#         linewidth = 0.3,
#         colors = [ stackplot_kw['category_colors'][category_j] for category_j in categories ],
#     )
#     ax.set_xlim( years[0], years[-1] )
#     ax.set_ylim( 0, 1. )
#     ax.set_xticks( years )
#     ax.set_ylabel( 'Fraction of Articles' )
# 
#     # Add labels
#     for j, poly_j in enumerate( stack ):
# 
#         # The y labels are centered in the middle of the last band
#         vertices = poly_j.get_paths()[0].vertices
#         xs = vertices[:,0]
#         end_vertices = vertices[:,1][xs == xs.max()]
#         label_y = 0.5 * ( end_vertices.min() + end_vertices.max() )
# 
#         text = ax.annotate(
#             text = fractions.columns[j],
#             xy = ( 1, label_y ),
#             xycoords = matplotlib.transforms.blended_transform_factory( ax.transAxes, ax.transData ),
#             xytext = ( -5 + 10 * ( stackplot_kw['horizontal_alignment'] == 'left' ), 0 ),
#             va = 'center',
#             ha = stackplot_kw['horizontal_alignment'],
#             textcoords = 'offset points',
#         )
#         text.set_path_effects([
#             path_effects.Stroke(linewidth=2.5, foreground='w'),
#             path_effects.Normal(),
#         ])
# 
#     # Labels, inc. size
#     ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * stackplot_kw['font_scale'] )
#     ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * stackplot_kw['font_scale'] )
#     ax.tick_params( labelsize=plot_context['xtick.labelsize']*stackplot_kw['font_scale'] )
# 
#     return fig