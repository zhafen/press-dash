# Computation imports
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
sns.set_style( 'whitegrid' )

st.set_page_config(layout='wide')

# Config
@st.cache_data
def load_config():
    with open( './config.yml', "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
config = load_config()

input_dir = os.path.join( config['data_dir'], config['input_dirname'] )
output_dir = os.path.join( config['data_dir'], config['output_dirname'] )

# Load the data
@st.cache_data
def load_data():

    # Directory for figures
    figure_dir = config['figure_dir']
    os.makedirs( figure_dir, exist_ok=True )

    grouping_labels = [ group_by_i.lower().replace( ' ', '_' ) for group_by_i in config['groupings'] ]

    # Load the raw data
    press_fp = os.path.join( output_dir, config['combined_filename'] )
    df = pd.read_csv( press_fp, index_col=0 )

    # Load the counts data
    counts_dfs = {}
    for i, group_by_i in enumerate( config['groupings'] ):
        
        counts_i_fp = os.path.join( output_dir, 'counts', 'counts.{}.csv'.format( grouping_labels[i] ) )
        counts_i =  pd.read_csv( counts_i_fp, index_col=0 )
        counts_dfs[group_by_i] = counts_i

    return df, counts_dfs

df, counts_dfs = load_data()

# Display for a particular group
group_by_i = st.selectbox( 'Grouping:', config['groupings'] )
counts_i = counts_dfs[group_by_i]

# Display for a subset of the columns
categories = st.multiselect( 'Categories', counts_i.columns, default=list( counts_i.columns ) )

@st.cache_data
def plot_counts( group_by_i, categories, counts_i ):
    years = counts_i.index

    fig = plt.figure()
    ax = plt.gca()
    for j, category_j in enumerate( categories ):

        ax.plot(
            years,
            counts_i[category_j],
        )
    # facet_grid = sns.relplot(
    #     counts_i,
    #     kind = 'line',
    #     dashes = False,
    #     linewidth = 3,
    #     aspect = 2,
    #     legend = 'brief',
    #     # legend_kws = { 'loc': 'upper left'}
    # )
    # facet_grid.ax.set_xlim( years[0], years[-1] )
    # facet_grid.ax.set_ylim( 0, facet_grid.ax.get_ylim()[1] )
    # ticks = facet_grid.ax.set_xticks( years )
    # facet_grid.ax.set_ylabel( 'Count' )

    ymax = ax.get_ylim()[1]

    ax.set_xticks( years )
    count_ticks = np.arange( 0, ymax, 1 )
    ax.set_yticks( count_ticks )

    ax.set_xlim( years[0], years[-1] )
    ax.set_ylim( 0, ymax )

    # return facet_grid
    return fig
    

fig = plot_counts( group_by_i, categories, counts_i )
# facet_grid.fig
st.pyplot( fig )


