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
alternate_weightings = [ 'People Reached', 'Press Mentions' ]
st.sidebar.markdown( '# Data Settings' )
year_min, year_max = df['Year'].min(), df['Year'].max()
data_kw = {
    'weighting': st.sidebar.selectbox(
        'count type',
        [ 'article count', ] + alternate_weightings,
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
search_str = st.text_input( 'title search (case insensitive; not a smart search)' )
is_included = exploded['Title'].str.extract( '(' + search_str + ')', flags=re.IGNORECASE ).notna().values[:,0]

# Select the categories to show
all_selected_columns = []
for i, group_by_i in enumerate( remaining_groupings ):
    possible_columns = pd.unique( exploded.index.get_level_values(i) )
    selected_columns = st.multiselect( group_by_i, possible_columns, default=possible_columns )
    if len( selected_columns ) == 0:
        st.error( 'You must select at least one option.' )
        st.stop()
    all_selected_columns.append( selected_columns )
@st.cache_data
def filter_data( is_included, group_by, all_selected_columns, weighting, count_range ):
    for i, group_by_i in enumerate( remaining_groupings ):
        is_included = is_included & exploded.index.isin( all_selected_columns[i], level=i )
    selected = exploded.loc[is_included]

    if weighting in alternate_weightings:

        # Filter on count
        selected_for_sum = selected.copy()
        selected_for_sum[weighting].replace( 'N/A', 0, inplace=True )
        is_in_count_range = (
            ( count_range[0] <= selected_for_sum[weighting] ) &
            ( selected_for_sum[weighting] <= count_range[1] )
        )
        selected_for_sum = selected_for_sum.loc[is_in_count_range]
        selected = selected.loc[is_in_count_range]

        # Replace N/A w/ zeros for counting
        def aggfunc( df_agg ):
            df_agg = df_agg.drop_duplicates( 'id', keep='first' )
            return df_agg[weighting].sum()
        counts = selected_for_sum.pivot_table(
            values=[weighting,'id'],
            index='Year',
            columns=group_by,
            aggfunc=aggfunc
        )
    else:
        # Get counts
        counts = selected.pivot_table( values='id', index='Year', columns=group_by, aggfunc='nunique' )

    # Replace "None"s
    counts.fillna( value=0, inplace=True )

    return selected, counts
selected, counts = filter_data( is_included, group_by, all_selected_columns, data_kw['weighting'], data_kw['count_range'] )

# Select the categories to show
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

@st.cache_data
def plot_counts( group_by, all_selected_columns, categories, plot_kw ):

    years = np.arange( plot_kw['years'][0], plot_kw['years'][-1] + 1, )
    counts_used = counts.reindex( years, fill_value=0 )
    total_used = total.reindex( years, fill_value=0 )

    if plot_kw['cumulative']:
        counts_used = counts_used.cumsum( axis='rows' )
        total_used = total_used.cumsum()

    sns.set_style( plot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")

    fig = plt.figure( figsize=( plot_kw['fig_width'], plot_kw['fig_height'] ) )
    ax = plt.gca()
    for j, category_j in enumerate( categories ):

        ys = counts_used[category_j]

        ax.plot(
            years,
            ys,
            linewidth = plot_kw['linewidth'],
            alpha = 0.5,
            zorder = 2,
            color = category_colors[category_j],
        )
        ax.scatter(
            years,
            ys,
            label = category_j,
            zorder = 2,
            color = category_colors[category_j],
            s = plot_kw['marker_size'],
        )
    if plot_kw['show_total']:
        ax.plot(
            years,
            total_used,
            linewidth = plot_kw['linewidth'],
            alpha = 0.5,
            color = 'k',
            zorder = 1,
        )
        ax.scatter(
            years,
            total_used,
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
