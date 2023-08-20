# Computation imports
import copy
import importlib
import numpy as np
import os
import pandas as pd
import streamlit as st
import sys

# Plotting imports
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import seaborn as sns

# DEBUG: I *think* this is handled now, but let's leave the code here just in case.
# # Import the custom library.
# # This should typically be accessible post pip-installation
# # But we add it to the path because when hosted on the web that doesn't work necessarily.
# src_dir = os.path.dirname( os.path.dirname( __file__ ) )
# if src_dir not in sys.path:
#     sys.path.append( src_dir )
# from g_and_p_dash_lib import dash_utils, data_utils, time_series_utils
from .. import dash_utils, data_utils, time_series_utils

def add_tab(
        preprocessed_df,
        config,
        global_data_kw,
        global_categorical_filter_defaults,
        global_plot_kw,
        header=None,
    ):
    '''Add a generic tab to a dashboard.
    There is room to make this more flexible, but at the cost of less readability.
    If made more flexible, should likely go with a class structure to avoid passing around too many arguments.
    '''

    if header is not None:
        st.header( 'header' )

    figure_tab, data_settings_tab, figure_settings_tab = st.tabs([ 'Figure', 'Data Settings', 'Figure Settings' ])

    # Data settings tab
    with data_settings_tab:

        # Create two columns
        general_st_col, filter_st_col = st.columns( 2 )

        # Column for general settings
        with general_st_col:
            st.markdown( '#### General Settings' )

            data_kw = dash_utils.setup_data_axes(
                st,
                config,
            )
            recat_data_kw = dash_utils.setup_data_settings(
                st,
                include=[ 'recategorize', 'combine_single_categories' ],
                defaults={
                    'recategorize': True, 'combine_single_categories': True
                },
            )
            data_kw.update( recat_data_kw )
            data_kw.update( global_data_kw )

            # Then change categories if requested.
            # The new categories avoid double counting.
            recategorized_df = st.cache_data( dash_utils.recategorize_data )( preprocessed_df, config['new_categories'], data_kw['recategorize'], data_kw['combine_single_categories'] )

        # Column for filters
        with filter_st_col:
            st.markdown( '#### Filter Settings' )

            categorical_filter_defaults = {}
            if data_kw['recategorize']:
                categorical_filter_defaults.update( global_categorical_filter_defaults )

            # Set up the filters
            search_str, search_col, categorical_filters, numerical_filters = dash_utils.setup_filters(
                st,
                recategorized_df,
                config,
                include_search=False,
                categorical_filter_defaults = categorical_filter_defaults,
            )

            # Apply the filters
            selected_df = st.cache_data( dash_utils.filter_data )( recategorized_df, search_str, search_col, categorical_filters, numerical_filters )

            # Retrieve counts or sums
            aggregated_df, total = st.cache_data( time_series_utils.count_or_sum )(
                selected_df,
                data_kw['year_column'],
                data_kw['y_column'],
                data_kw['groupby_column'],
                data_kw['count_or_sum'],
            )

    with figure_settings_tab:

        lineplot_st_col, stackplot_st_col = st.columns( 2 )

        with lineplot_st_col:
            st.markdown( '#### Lineplot Settings' )

            # Settings for the lineplot
            if data_kw['cumulative']:
                default_ymax = total.sum().max() * 1.05
            else:
                default_ymax = total.values.max() * 1.05
            plot_kw = time_series_utils.setup_lineplot_settings(
                st,
                default_ymax,
                default_x_label = 'Year',
                default_y_label = 'Count of Unique Investigators',
            )
            plot_kw['category_colors'] = {
                category: global_plot_kw['color_palette'][i] for i, category in enumerate( aggregated_df.columns )
            }
            # Pull in the other dictionaries
            plot_kw.update( global_plot_kw )
            plot_kw.update( data_kw )

        with stackplot_st_col:
            st.markdown( '#### Stackplot Settings' )

            # Settings for the stackplot
            stackplot_kw = time_series_utils.setup_stackplot_settings(
                st,
                default_x_label = 'Year',
                default_y_label = 'Fraction of Unique Investigators',
            )
            stackplot_kw['category_colors'] = {
                category: global_plot_kw['color_palette'][i] for i, category in enumerate( aggregated_df.columns )
            }
            # Pull in the other dictionaries
            stackplot_kw.update( global_plot_kw )
            stackplot_kw.update( data_kw )

    with figure_tab:

        view = st.radio( 'How do you want to view the data?', [ 'lineplot', 'stackplot', 'data' ], horizontal=True )

        download_kw = st.cache_data( time_series_utils.view_time_series )(
            view,
            preprocessed_df,
            selected_df,
            aggregated_df,
            total,
            data_kw,
            plot_kw,
            stackplot_kw,
        )

        st.download_button( **download_kw )

def main( config_fp ):
    '''Everything is wrapped in the main function, which has one argument:
    the config file path. This enables the same application to be used
    for multiple pages by passing in different config files.

    Args:
        config_fp (str): Location of the config filepath.
    '''

    # Streamlit works by repeatedly rerunning the code,
    # so if we want to propogate changes to the library we need to reload it.
    for module_to_reload in [ dash_utils, data_utils, time_series_utils ]:
        importlib.reload( module_to_reload )

    ################################################################################
    # Script Setup
    ################################################################################

    # This must be the first streamlit command
    st.set_page_config(layout='wide')

    # Load the configuration
    config = st.cache_data( dash_utils.load_config )( config_fp )

    # Set the title that shows up at the top of the dashboard
    st.title( config['page_title'] )

    ################################################################################
    # Load data
    ################################################################################

    df = st.cache_data( data_utils.load_data )( config )

    # Do general preprocessing
    preprocessed_df, config = st.cache_data( data_utils.preprocess )( df, config )

    ################################################################################
    # Set up global settings
    ################################################################################

    # Get global data settings
    st.sidebar.markdown( '# Data Settings' )
    global_data_kw = dash_utils.setup_data_settings( st.sidebar, config, include=['show_total', 'cumulative'] )

    # Global figure settings
    st.sidebar.markdown( '# Figure Settings' )
    global_plot_kw = dash_utils.setup_figure_settings( st.sidebar, config, color_palette=config['color_palette'] ),

    global_categorical_filter_defaults = {
        'Award Dept Name': [ 'CIERA', 'P&A',]
    }

    ################################################################################
    # Add tabs
    ################################################################################

    add_tab(
        preprocessed_df,
        config,
        global_data_kw,
        global_categorical_filter_defaults,
        global_plot_kw,
    )