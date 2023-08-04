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
import matplotlib.patheffects as path_effects
import seaborn as sns

################################################################################
# Script Setup
################################################################################

st.set_page_config(layout='wide')

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

    # Colors for the categories
    color_palette = sns.color_palette( config['color_palette'] )
    category_colors = {}
    for i, category in enumerate( pd.unique( exploded[group_by] ) ):
        category_colors[category] = color_palette[i]

    return exploded, remaining_groupings, category_colors

exploded, remaining_groupings, category_colors = load_data( group_by )

################################################################################
# Filter Data
################################################################################

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

# Select the categories to show
years = counts.index
categories = st.multiselect( group_by, counts.columns, default=list(counts.columns) )

st.header( 'Article Count per Year' )

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
# Plot Counts
################################################################################

st.sidebar.markdown( '# Figure Settings' )

fig_width, fig_height = matplotlib.rcParams['figure.figsize']
generic_plot_kw = {
    'fig_width': st.sidebar.slider( 'figure width', 0.1*fig_width, 2.*fig_width, value=9. ),
    'fig_height': st.sidebar.slider( 'figure height', 0.1*fig_height, 2.*fig_height, value=fig_height ),
    'font_scale': st.sidebar.slider( 'font scale', 0.1, 2.0, value=1. ),
    'seaborn_style': st.sidebar.selectbox(
        'choose seaborn plot style',
        [ 'whitegrid', 'white', 'darkgrid', 'dark', 'ticks', ],
        index = 0,
    ),
}

# Sidebar figure tweaks
st.sidebar.markdown( '## Counts Figure Settings' )
plot_kw = {
    'legend_scale': st.sidebar.slider( 'legend scale', 0.1, 2.0, value=1. ), 
    'legend_x': st.sidebar.slider( 'legend x', 0., 1., value=0. ),
    'legend_y': st.sidebar.slider( 'legend y', 0., 1.5, value=1. ),
    'tick_spacing': st.sidebar.slider( 'y tick spacing', 1, 10, value=int(np.ceil(counts.values.max()/30.)) ),
}

plot_kw.update( generic_plot_kw )
plot_kw.update( data_kw )

@st.cache_data
def plot_counts( group_by, all_selected_columns, categories, plot_kw ):

    sns.set_style( plot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")

    fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
    ax = plt.gca()
    for j, category_j in enumerate( categories ):

        ax.plot(
            years,
            counts[category_j],
            linewidth = 2,
            alpha = 0.5,
            zorder = 2,
            color = category_colors[category_j],
        )
        ax.scatter(
            years,
            counts[category_j],
            label = category_j,
            zorder = 2,
            color = category_colors[category_j],
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

    # Labels, inc. size
    ax.set_xlabel( 'Year', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
    ax.set_ylabel( 'Count', fontsize=plot_context['axes.labelsize'] * plot_kw['font_scale'] )
    ax.tick_params( labelsize=plot_context['xtick.labelsize']*plot_kw['font_scale'] )

    # return facet_grid
    return fig

with st.spinner():
    fig = plot_counts( group_by, all_selected_columns, categories, plot_kw )
    st.pyplot( fig )

# Add a download button for the image
fn = 'counts.{}.pdf'.format( group_by.lower().replace( ' ', '_' ) )
img = io.BytesIO()
fig.savefig( img, format='pdf', bbox_inches='tight' )
st.download_button(
    label="Download Figure",
    data=img,
    file_name=fn,
    mime="image/pdf"
)

################################################################################
# Sand/Stack Plot
################################################################################

# Sidebar figure tweaks
st.sidebar.markdown( '## Fractions Figure Settings' )
fig_width, fig_height = matplotlib.rcParams['figure.figsize']
stackplot_kw = {
    'horizontal_alignment': st.sidebar.selectbox( 'label alignment', [ 'right', 'left' ], index=0 ),
}

stackplot_kw.update( generic_plot_kw )
stackplot_kw.update( data_kw )

st.header( 'Fraction of Tags per Year' )

@st.cache_data
def plot_fractions( group_by, all_selected_columns, categories, stackplot_kw ):

    sns.set_style( stackplot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")

    counts_used = counts[categories]

    # Get data
    total = counts_used.sum( axis='columns' )
    fractions = counts_used.mul( 1./total, axis='rows' )
    
    years = counts_used.index
    
    fig = plt.figure( figsize=( stackplot_kw['fig_width'], stackplot_kw['fig_height'] ) )
    ax = plt.gca()
    
    stack = ax.stackplot(
        years,
        fractions.values.transpose(),
        linewidth = 0.3,
        colors = [ category_colors[category_j] for category_j in categories ],
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

with st.spinner():
    fig = plot_fractions( group_by, all_selected_columns, categories, stackplot_kw )
    st.pyplot( fig )

# Add a download button for the image
fn = 'fractions.{}.pdf'.format( group_by.lower().replace( ' ', '_' ) )
img = io.BytesIO()
fig.savefig( img, format='pdf', bbox_inches='tight' )
st.download_button(
    label="Download Figure",
    data=img,
    file_name=fn,
    mime="image/pdf"
)
# 

################################################################################
# Display Raw Data
################################################################################

st.header( 'Selected Data' )
with st.spinner():
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
