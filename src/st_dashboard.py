# Computation imports
import copy
import io
import numpy as np
import os
import pandas as pd
import re
import yaml
import streamlit as st

# Matplotlib imports
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import seaborn as sns

from press_dashboard_library import streamlit as st_lib

# DEBUG
import importlib
importlib.reload( st_lib )

################################################################################
# Script Setup
################################################################################

st.set_page_config(layout='wide')

config = st_lib.load_config( __file__ )

################################################################################
# Load data
################################################################################

st.title( 'Overview of CIERA Articles' )

# User data selection
group_by = st.selectbox( 'Select what you want to group the articles by:', config['groupings'] )

st.header( 'Data Filters' )

df = st_lib.load_original_data( config )

exploded, remaining_groupings, category_colors = st_lib.load_exploded_data( config, group_by )

################################################################################
# Filter and Count Data
################################################################################

# Sidebar data settings
alternate_weightings = [ 'People Reached', 'Press Mentions' ]
st.sidebar.markdown( '# Data Settings' )
year_min, year_max = df['Year'].min(), df['Year'].max()
data_kw = {
    'weighting': st.sidebar.selectbox(
        'count type',
        [ 'Article Count', ] + alternate_weightings,
        index = 0,
        format_func = lambda x: x.lower(),
    ),
    'count_range': None,
    'years': st.sidebar.slider( 'year range', year_min, year_max, value=[ year_min, year_max ] ),
    'show_total': st.sidebar.checkbox( 'show total article count per year', value=False ),
    'cumulative': st.sidebar.checkbox( 'use cumulative count', value=False ),
}
if data_kw['weighting'] in alternate_weightings:
    count_max = int( df[data_kw['weighting']].replace('N/A', 0).max() )
    data_kw['count_range'] = st.sidebar.slider( 'count range', 0, count_max, value=[0, count_max ]  )

# Look for matching strings
search_str = st.text_input( 'Title search (case insensitive; not a smart search)' )

# User selection for the categories to show
selected_groups = {}
for group_by_i in config['groupings']:
    possible_columns = pd.unique( exploded[group_by_i] )
    selected_groups_i = st.multiselect( group_by_i, possible_columns, default=possible_columns )
    if len( selected_groups_i ) == 0:
        st.error( 'You must select at least one option.' )
        st.stop()
    selected_groups[group_by_i] = selected_groups_i

# Retrieve selected data
selected = st_lib.filter_data( exploded, selected_groups, search_str )

# Retrieve counts
counts = st_lib.count( selected, group_by, data_kw['weighting'] )
categories = counts.columns

st.header( 'Article Count per Year' )

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
    'category_colors': category_colors,
}

# Sidebar figure tweaks
st.sidebar.markdown( '## Counts Figure Settings' )
if data_kw['cumulative']:
    default_ymax = counts.sum( axis='rows' ).max() * 1.05
else:
    default_ymax = counts.values.max() * 1.05

default_tick_spacing = int(np.ceil(default_ymax/30.))
max_tick_spacing = int( default_ymax )
plot_kw = {
    'linewidth': st.sidebar.slider( 'linewidth', 0., 10., value=2. ),
    'marker_size': st.sidebar.slider( 'marker size', 0., 100., value=30. ),
    'y_lim': st.sidebar.slider( 'y limits', 0., default_ymax*2., value=[0., default_ymax ] ),
    'tick_spacing': st.sidebar.slider( 'y tick spacing', 1, max_tick_spacing, value=default_tick_spacing ),
    'legend_scale': st.sidebar.slider( 'legend scale', 0.1, 2.0, value=1. ), 
    'legend_x': st.sidebar.slider( 'legend x', 0., 1., value=0. ),
    'legend_y': st.sidebar.slider( 'legend y', 0., 1.5, value=1. ),
}

plot_kw.update( generic_plot_kw )
plot_kw.update( data_kw )

with st.spinner():
    fig = st_lib.plot_counts( counts, plot_kw )
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
def plot_fractions( group_by, selected_groups, categories, stackplot_kw ):

    sns.set_style( stackplot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")
    
    years = np.arange( stackplot_kw['years'][0], stackplot_kw['years'][-1] + 1, )
    counts_used = counts.reindex( years, fill_value=0 )[categories]

    if stackplot_kw['cumulative']:
        counts_used = counts_used.cumsum( axis='rows' )

    # Get data
    total_used = counts_used.sum( axis='columns' )
    fractions = counts_used.mul( 1./total_used, axis='rows' ).fillna( value=0. )
    
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
    fig = plot_fractions( group_by, selected_groups, categories, stackplot_kw )
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
    fully_selected_df = subselected_df.loc[
        ( data_kw['years'][0] <= subselected_df['Year'] ) &
        ( subselected_df['Year'] <= data_kw['years'][1] )
    ]
    st.markdown( 'This table contains all {} selected articles.'.format( len( fully_selected_df ) ) )
    st.write( fully_selected_df )

# Add a download button for the data
fn = 'selected.csv'
f = io.BytesIO()
fully_selected_df.to_csv( f )
st.download_button(
    label="Download Selected Data",
    data=f,
    file_name=fn,
    mime="text/plain"
)
