# Computation imports
import copy
import io
import numpy as np
import os
import glob
import pandas as pd
import sys
import yaml
import streamlit as st

# Matplotlib imports
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

################################################################################
# Script Setup
################################################################################

@st.cache_data
def load_config():
    '''Get the config. Do this only once.
    '''

    # Check if we're in the directory the script is in,
    # which should also be the directory the config is in.
    # If not, move into that directory
    config_dir = os.path.dirname( __file__ )
    if os.getcwd() != config_dir:
        os.chdir( config_dir )

    with open( './config.yml', "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
config = load_config()

input_dir = os.path.join( config['data_dir'], config['input_dirname'] )
output_dir = os.path.join( config['data_dir'], config['output_dirname'] )

@st.cache_data
def plotting_setup():
    sns.set_style( 'whitegrid' )
    plot_context = sns.plotting_context("notebook")

    return plot_context
plot_context = plotting_setup()

################################################################################
# Load data
################################################################################

st.title( 'Overview of CIERA Articles' )

# User data selection
group_by = st.selectbox( 'Select what you want to group the articles by:', config['groupings'] )

st.header( 'Data Filters' )

@st.cache_data
def load_original_data():

    press_fp = os.path.join( output_dir, config['combined_filename'] )
    df = pd.read_csv( press_fp, index_col=0 )

    df.fillna( value='N/A', inplace=True )

    return df
df = load_original_data()

@st.cache_data
def load_data( group_by ):

    remaining_groupings = copy.copy( config['groupings'] )
    remaining_groupings.remove( group_by )

    base, ext = os.path.splitext( config['combined_filename'] )
    exploded_filename = '{}.exploded{}'.format( base, ext )
    exploded_fp = os.path.join( output_dir, exploded_filename )
    exploded = pd.read_csv( exploded_fp )
    exploded.fillna( value='N/A', inplace=True )

    exploded.set_index(remaining_groupings, inplace=True)

    return exploded, remaining_groupings

exploded, remaining_groupings = load_data( group_by )

################################################################################
# Filter Data
################################################################################

st.header( 'Article Count per Year' )

# Sidebar data settings
st.sidebar.markdown( '# Data Settings' )
data_kw = {
    'show_total': st.sidebar.checkbox( 'show total article count per year', value=False ),
}

# Select the categories to show
all_selected_columns = []
for i, group_by_i in enumerate( remaining_groupings ):
    possible_columns = pd.unique( exploded.index.get_level_values(i) )
    selected_columns = st.multiselect( group_by_i, possible_columns, default=possible_columns )
    if len( selected_columns ) == 0:
        st.error( 'You must select at least one option.' )
        st.stop()
    all_selected_columns.append( selected_columns )

cumulative = st.sidebar.checkbox( 'use cumulative count', value=False )

@st.cache_data
def filter_data( group_by, all_selected_columns, cumulative ):
    is_included = np.ones( len( exploded ), ).astype( bool )
    for i, group_by_i in enumerate( remaining_groupings ):
        is_included = is_included & exploded.index.isin( all_selected_columns[i], level=i )
    selected = exploded.loc[is_included]

    # Get counts
    counts = selected.pivot_table( values='id', index='Year', columns=group_by, aggfunc='nunique' )

    if cumulative:
        counts = counts.cumsum( axis='rows' )

    # Replace "None"s
    counts.fillna( value=0, inplace=True )

    return selected, counts
selected, counts = filter_data( group_by, all_selected_columns, cumulative )

years = counts.index
categories = st.multiselect( group_by, counts.columns, default=list(counts.columns) )

@st.cache_data
def filter_data_again( group_by, categories, all_selected_columns ):
    subselected = selected.loc[selected[group_by].isin( categories )]
    total = subselected.pivot_table( index='Year', values='id', aggfunc='nunique' )

    selected_ids = pd.unique( subselected['id'] )
    subselected_df = df.loc[selected_ids]
    return subselected, total, subselected_df
subselected, total, subselected_df = filter_data_again( group_by, categories, all_selected_columns )

if cumulative:
    total = total.cumsum()

################################################################################
# Plot
################################################################################

# Sidebar figure tweaks
st.sidebar.markdown( '# Figure Settings' )
fig_width, fig_height = matplotlib.rcParams['figure.figsize']
plot_kw = {
    'fig_width': st.sidebar.slider( 'figure width', 0.1*fig_width, 2.*fig_width, value=9. ),
    'fig_height': st.sidebar.slider( 'figure height', 0.1*fig_height, 2.*fig_height, value=fig_height ),
    'font_scale': st.sidebar.slider( 'font scale', 0.1, 2.0, value=1. ),
    'legend_scale': st.sidebar.slider( 'legend scale', 0.1, 2.0, value=1. ), 
    'legend_x': st.sidebar.slider( 'legend x', 0., 1., value=0. ),
    'legend_y': st.sidebar.slider( 'legend y', 0., 1.5, value=1. ),
    'tick_spacing': st.sidebar.slider( 'y tick spacing', 1, 10, value=int(np.ceil(counts.values.max()/30.)) ),
}

plot_kw.update( data_kw )

@st.cache_data
def plot_counts( group_by, all_selected_columns, categories, plot_kw ):

    fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
    ax = plt.gca()
    for j, category_j in enumerate( categories ):

        ax.plot(
            years,
            counts[category_j],
            linewidth = 2,
            alpha = 0.5,
            zorder = 2,
        )
        ax.scatter(
            years,
            counts[category_j],
            label = category_j,
            zorder = 2,
        )
    if plot_kw['show_total']:
        ax.plot(
            years,
            total,
            linewidth = 2,
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
        )

    ymax = ax.get_ylim()[1]

    ax.set_xticks( years )
    count_ticks = np.arange( 0, ymax, plot_kw['tick_spacing'] )
    ax.set_yticks( count_ticks )

    ax.set_xlim( years[0], years[-1] )
    ax.set_ylim( 0, ymax )

    l = ax.legend(
        bbox_to_anchor = ( plot_kw['legend_x'], plot_kw['legend_y'] ),
        loc = 'lower left', 
        framealpha = 1.,
        fontsize = plot_context['legend.fontsize'] * plot_kw['legend_scale'],
        ncol = len( categories ) // 4 + 1
    )

    ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
    ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )

    ax.tick_params( labelsize=plot_context['xtick.labelsize']*plot_kw['font_scale'] )

    # return facet_grid
    return fig

with st.spinner():
    fig = plot_counts( group_by, all_selected_columns, categories, plot_kw )
    st.pyplot( fig )

# Add a download button for the image
fn = 'counts.{}.pdf'.format( group_by )
img = io.BytesIO()
fig.savefig( img, format='pdf', bbox_inches='tight' )
st.download_button(
    label="Download Figure",
    data=img,
    file_name=fn,
    mime="image/pdf"
)

################################################################################
# Display Raw Data
################################################################################

st.subheader( 'Selected Data' )
st.markdown( 'This table contains all {} selected articles.'.format( len( subselected_df ) ) )
st.write( subselected_df )

# Add a download button for the data
fn = 'selected.csv'
f = io.BytesIO()
subselected_df.to_csv( f )
st.download_button(
    label="Download Selected Data",
    data=f,
    file_name=fn,
    mime="text/plain"
)

################################################################################
# Plot counts
################################################################################

# # Sidebar for figure tweaks
# st.sidebar.markdown( '# Figure Tweaks' )
# fig_width, fig_height = matplotlib.rcParams['figure.figsize']
# plot_kw = {
#     'fig_width': st.sidebar.slider( 'figure width', 0.1*fig_width, 2.*fig_width, value=9. ),
#     'fig_height': st.sidebar.slider( 'figure height', 0.1*fig_height, 2.*fig_height, value=fig_height ),
#     'font_scale': st.sidebar.slider( 'font scale', 0.1, 2.0, value=1. ),
#     'legend_x': st.sidebar.slider( 'legend x', 0., 1., value=0. ),
#     'legend_y': st.sidebar.slider( 'legend y', 0., 1.5, value=1. ),
#     'tick_spacing': st.sidebar.slider( 'y tick spacing', 1, 10, value=int(np.ceil(counts.values.max()/30.)) )
# }
# 
# @st.cache_data
# def plot_counts( group_by, categories, plot_kw ):
#     years = counts.index
# 
#     fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
#     ax = plt.gca()
#     for j, category_j in enumerate( categories ):
# 
#         ax.plot(
#             years,
#             counts[category_j],
#             linewidth = 2,
#             alpha = 0.5,
#         )
#         ax.scatter(
#             years,
#             counts[category_j],
#             label = category_j,
#         )
# 
#     ymax = ax.get_ylim()[1]
# 
#     ax.set_xticks( years )
#     count_ticks = np.arange( 0, ymax, plot_kw['tick_spacing'] )
#     ax.set_yticks( count_ticks )
# 
#     ax.set_xlim( years[0], years[-1] )
#     ax.set_ylim( 0, ymax )
# 
#     l = ax.legend(
#         bbox_to_anchor = ( plot_kw['legend_x'], plot_kw['legend_y'] ),
#         loc = 'lower left', 
#         framealpha = 1.,
#         fontsize = plot_context['legend.fontsize'] * plot_kw['font_scale'],
#         ncol = len( categories ) // 4 + 1
#     )
# 
#     ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
#     ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
# 
#     ax.tick_params( labelsize=plot_context['xtick.labelsize']*plot_kw['font_scale'] )
# 
#     # return facet_grid
#     return fig
# fig = plot_counts( group_by, categories, plot_kw )
# st.pyplot( fig )
# 
# # Add a download button for the image
# fn = 'counts.{}.pdf'.format( group_by )
# img = io.BytesIO()
# fig.savefig( img, format='pdf', bbox_inches='tight' )
# st.download_button(
#     label="Download Figure",
#     data=img,
#     file_name=fn,
#     mime="image/pdf"
# )
# 
# # ################################################################################
# # # Plot fractions
# # ################################################################################
# # 
# # @st.cache_data
# # def plot_fractions( group_by, categories, plot_kw ):
# #     years = counts.index
# # 
# #     # Get data
# #     total = counts.sum( axis='columns' )
# #     fractions = counts.mul( 1./total, axis='rows' )
# #     
# #     years = counts.index
# #     
# #     fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
# #     ax = plt.gca()
# #     
# #     stack = ax.stackplot(
# #         years,
# #         fractions.values.transpose()
# #     )
# #     ax.set_xlim( years[0], years[-1] )
# #     ax.set_ylim( 0, 1. )
# #     ax.set_xticks( years )
# #     ax.set_ylabel( 'Fraction of Articles' )
# # 
# #     # Add labels
# #     for j, poly_j in enumerate( stack ):
# #         vertices = poly_j.get_paths()[0].vertices
# #         last_vert_ind = vertices[:,0].argmax()
# #         label_y = vertices[last_vert_ind,1]
# # 
# #         ax.annotate(
# #             text = fractions.columns[j],
# #             xy = ( 1, label_y ),
# #             xycoords = matplotlib.transforms.blended_transform_factory( ax.transAxes, ax.transData ),
# #             xytext = ( 5, 5 ),
# #             textcoords = 'offset points',
# #         )
# # 
# #     return fig
# # fig = plot_fractions( group_by, categories, plot_kw )
# # st.pyplot( fig )
# # 
# # # Add a download button for the image
# # fn = 'fractions.{}.pdf'.format( group_by )
# # img = io.BytesIO()
# # fig.savefig( img, format='pdf', bbox_inches='tight' )
# # st.download_button(
# #     label="Download Figure",
# #     data=img,
# #     file_name=fn,
# #     mime="image/pdf"
# # )
# 