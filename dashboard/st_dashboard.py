# Computation imports
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
    os.chdir( 'src' )
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

st.markdown( '# Articles Per Year' )

# User data selection
group_by = st.selectbox( 'Grouping:', config['groupings'] )

@st.cache_data
def load_data( group_by ):

    group_by_label = group_by.lower().replace( ' ', '_' )

    # Load the counts data
    counts_fp = os.path.join( output_dir, 'counts', 'counts.{}.csv'.format( group_by_label ) )
    counts =  pd.read_csv( counts_fp, index_col=0 )

    return counts, group_by_label
counts, group_by_label = load_data( group_by )

# Display for a subset of the columns
categories = st.multiselect( 'Categories', counts.columns, default=list( counts.columns ) )

################################################################################
# Plot counts
################################################################################

# Sidebar for figure tweaks
st.sidebar.markdown( '# Figure Tweaks' )
fig_width, fig_height = matplotlib.rcParams['figure.figsize']
plot_kw = {
    'fig_width': st.sidebar.slider( 'figure width', 0.1*fig_width, 2.*fig_width, value=9. ),
    'fig_height': st.sidebar.slider( 'figure height', 0.1*fig_height, 2.*fig_height, value=fig_height ),
    'font_scale': st.sidebar.slider( 'font scale', 0.1, 2.0, value=1. ),
    'legend_x': st.sidebar.slider( 'legend x', 0., 1., value=0. ),
    'legend_y': st.sidebar.slider( 'legend y', 0., 1.5, value=1. ),
    'tick_spacing': st.sidebar.slider( 'y tick spacing', 1, 10, value=int(np.ceil(counts.values.max()/30.)) )
}

@st.cache_data
def plot_counts( group_by, categories, plot_kw ):
    years = counts.index

    fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
    ax = plt.gca()
    for j, category_j in enumerate( categories ):

        ax.plot(
            years,
            counts[category_j],
            linewidth = 2,
            alpha = 0.5,
        )
        ax.scatter(
            years,
            counts[category_j],
            label = category_j,
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
        fontsize = plot_context['legend.fontsize'] * plot_kw['font_scale'],
        ncol = len( categories ) // 4 + 1
    )

    ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
    ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )

    ax.tick_params( labelsize=plot_context['xtick.labelsize']*plot_kw['font_scale'] )

    # return facet_grid
    return fig
fig = plot_counts( group_by, categories, plot_kw )
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

# ################################################################################
# # Plot fractions
# ################################################################################
# 
# @st.cache_data
# def plot_fractions( group_by, categories, plot_kw ):
#     years = counts.index
# 
#     # Get data
#     total = counts.sum( axis='columns' )
#     fractions = counts.mul( 1./total, axis='rows' )
#     
#     years = counts.index
#     
#     fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
#     ax = plt.gca()
#     
#     stack = ax.stackplot(
#         years,
#         fractions.values.transpose()
#     )
#     ax.set_xlim( years[0], years[-1] )
#     ax.set_ylim( 0, 1. )
#     ax.set_xticks( years )
#     ax.set_ylabel( 'Fraction of Articles' )
# 
#     # Add labels
#     for j, poly_j in enumerate( stack ):
#         vertices = poly_j.get_paths()[0].vertices
#         last_vert_ind = vertices[:,0].argmax()
#         label_y = vertices[last_vert_ind,1]
# 
#         ax.annotate(
#             text = fractions.columns[j],
#             xy = ( 1, label_y ),
#             xycoords = matplotlib.transforms.blended_transform_factory( ax.transAxes, ax.transData ),
#             xytext = ( 5, 5 ),
#             textcoords = 'offset points',
#         )
# 
#     return fig
# fig = plot_fractions( group_by, categories, plot_kw )
# st.pyplot( fig )
# 
# # Add a download button for the image
# fn = 'fractions.{}.pdf'.format( group_by )
# img = io.BytesIO()
# fig.savefig( img, format='pdf', bbox_inches='tight' )
# st.download_button(
#     label="Download Figure",
#     data=img,
#     file_name=fn,
#     mime="image/pdf"
# )
