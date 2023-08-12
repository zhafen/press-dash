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
import seaborn as sns

from press_dash_lib import streamlit_utils as st_lib

# DEBUG
import importlib
importlib.reload( st_lib )

################################################################################
# Script Setup
################################################################################

st.set_page_config(layout='wide')

config = st.cache_data( st_lib.load_config )( __file__ )

################################################################################
# Load data
################################################################################

st.title( 'Overview of CIERA Articles' )

# User data selection
group_by = st.selectbox( 'Select what you want to group the articles by:', config['groupings'] )

st.header( 'Data Filters' )

df = st.cache_data( st_lib.load_original_data )( config )

exploded, remaining_groupings, category_colors = st.cache_data( st_lib.load_exploded_data )( config, group_by )

################################################################################
# Filter and Count Data
################################################################################

# Sidebar data settings
alternate_weightings = [ 'People Reached', 'Press Mentions' ]
st.sidebar.markdown( '# Data Settings' )
data_kw = {
    'weighting': st.sidebar.selectbox(
        'count type',
        [ 'Article Count', ] + alternate_weightings,
        index = 0,
        format_func = lambda x: x.lower(),
    ),
    'recategorize': st.sidebar.checkbox( 'use combined categories (avoids double counting)', value=False ),
    'count_range': None,
    'show_total': st.sidebar.checkbox( 'show total article count per year', value=False ),
    'cumulative': st.sidebar.checkbox( 'use cumulative count', value=False ),
}
if data_kw['weighting'] in alternate_weightings:
    count_max = int( df[data_kw['weighting']].replace('N/A', 0).max() )

# Change categories
exploded = st.cache_data( st_lib.recategorize_data )( exploded, config['new_categories'], data_kw['recategorize'] )

# Setup range filters
range_filters = {}
for column in [ 'Year', 'Press Mentions', 'People Reached' ]:
    column_min, column_max = int( df[column].min() ), int( df[column].max() )
    range_filters[column] = st.sidebar.slider( column.lower(), column_min, column_max, value=[ column_min, column_max ] )

data_kw.update( range_filters )

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
selected = st.cache_data( st_lib.filter_data )( exploded, selected_groups, search_str, range_filters )

# Retrieve counts
counts, total = st.cache_data( st_lib.count )( selected, group_by, data_kw['weighting'] )
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
    fig = st.cache_data( st_lib.plot_counts )( counts, total, plot_kw )
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

with st.spinner():
    fig = st.cache_data( st_lib.plot_fractions )( counts, stackplot_kw )
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
    selected_entries = df.loc[pd.unique(selected['id'])]
    st.markdown( 'This table contains all {} selected articles.'.format( len( selected_entries ) ) )
    st.write( selected_entries )

# Add a download button for the data
fn = 'selected.csv'
f = io.BytesIO()
selected_entries.to_csv( f )
st.download_button(
    label="Download Selected Data",
    data=f,
    file_name=fn,
    mime="text/plain"
)
