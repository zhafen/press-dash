'''Time-series functions.
Most functions should be useful for most time-series datasets.
'''
import io
import numpy as np
import pandas as pd
import streamlit as st

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import seaborn as sns

################################################################################

def count_or_sum( selected_df, year_column, y_column, groupby_column, count_or_sum ):
    '''Aggregate. Wrapper function for other functions for the sake of caching.

    Args:
        selected_df (pd.DataFrame): The dataframe containing the selected data.
        year_column (str): The column containing the year.
        y_column (str): The column containing the data to count or sum.
        groupby_column (str): The category to group the data by, e.g. 'Research Topics'.
        count_or_sum (str): Whether to count or sum.

    Returns:
        agged (pd.DataFrame): The dataframe containing the aggregated_df data per year.
        total (pd.Series): The series containing the aggregated_df data per year, overall.
    '''

    if count_or_sum == 'Count':
        return count( selected_df, year_column, y_column, groupby_column )
    elif count_or_sum == 'Sum':
        return sum( selected_df, year_column, y_column, groupby_column )
    else:
        raise KeyError( 'How did you get here?' )

################################################################################

def count( selected_df, year_column, count_column, groupby_column ):
    '''Count up stats, e.g. number of articles per year per category or
    the number of people reached per year per category.

    Args:
        selected_df (pd.DataFrame): The dataframe containing the selected data.
        groupby_column (str): The category to group the data by, e.g. 'Research Topics'.
        count_column (str): What to count up.

    Returns:
        counts (pd.DataFrame): The dataframe containing the counts per year per category.
        total (pd.Series): The series containing the counts per year, overall.
    '''

    counts = selected_df.pivot_table(
        index=year_column,
        columns=groupby_column,
        values=count_column,
        aggfunc='nunique',
    )
    total = selected_df.pivot_table(
        index=year_column,
        values=count_column,
        aggfunc='nunique',
    )

    # Fill empty counts
    counts.fillna( value=0, inplace=True )
    total.fillna( value=0, inplace=True )

    return counts, total

################################################################################

def sum( selected_df, year_column, weight_column, groupby_column ):
    '''Sum up amouts, e.g. dollar amount per year.

    Args:
        selected_df (pd.DataFrame): The dataframe containing the selected data.
        groupby_column (str): The category to group the data by, e.g. 'Research Topics'.
        weight_column (str): What to weight the counts by, e.g. 'Article Count' or 'People Reached'.

    Returns:
        counts (pd.DataFrame): The dataframe containing the counts per year per category.
        total (pd.Series): The series containing the counts per year, overall.
    '''

    # We keep one entry per ID and group. This is to avoid double-counting.
    selected_for_sum_df = selected_df.copy()
    selected_for_sum_df['id_and_group'] = selected_df['id'].astype( str ) + selected_df[groupby_column]
    selected_for_sum_df.drop_duplicates( subset='id_and_group', keep='first', inplace=True )
    summed = selected_for_sum_df.pivot_table(
        values=weight_column,
        index=year_column,
        columns=groupby_column,
        aggfunc='sum'
    )
    # For total we only need one entry per ID.
    selected_for_sum_df.drop_duplicates( subset='id', keep='first', inplace=True )
    total = selected_for_sum_df.pivot_table(
        values=weight_column,
        index=year_column,
        aggfunc='sum'
    )

    # Replace the Nones with zeroes
    summed = summed.fillna( 0 )
    total = total.fillna( 0 )

    return summed, total

################################################################################

def setup_lineplot_settings(
        st_loc,
        default_ymax,
        default_x_label,
        default_y_label,
    ):
    '''Get user input for the lineplot.

    Args:
        st_loc (streamlit): The streamlit object to use.
        default_ymax (float): The default maximum y value.
        default_x_label (str): The default x label.
        default_y_label (str): The default y label.

    Returns:
        plot_kw (dict): The plotting keywords.
    '''

    # Settings specific to the counts
    unrounded_tick_spacing = default_ymax/11.
    default_tick_spacing = np.round( unrounded_tick_spacing, -np.floor(np.log10(unrounded_tick_spacing)).astype(int) )
    max_tick_spacing = int( default_ymax )
    plot_kw = {
        'x_label': st_loc.text_input( 'lineplot x label', value=default_x_label ),
        'y_label': st_loc.text_input( 'lineplot y label', value=default_y_label, ),
        'log_yscale': st_loc.checkbox( 'use log yscale', value=False ),
        'linewidth': st_loc.slider( 'linewidth', 0., 10., value=2. ),
        'marker_size': st_loc.slider( 'marker size', 0., 100., value=30. ),
        'y_lim': st_loc.slider( 'y limits', 0., default_ymax*2., value=[0., default_ymax ] ),
        'tick_spacing': st_loc.number_input( 'y tick spacing', value=default_tick_spacing ),
    }

    return plot_kw

################################################################################

def lineplot(
        aggregated_df,
        total,
        **lineplot_kw
    ):
    '''Function to plot the counts.

    Args:
        counts (pd.DataFrame): The dataframe containing the counts per year per category.
        total (pd.Series): The series containing the counts per year, overall.
        plot_kw (dict): The plotting keywords. Typically set things like font size, figure dimensions, etc.

    Returns:
        fig (matplotlib.figure.Figure): The figure containing the plot.
    '''

    if lineplot_kw['cumulative']:
        aggregated_df = aggregated_df.cumsum( axis='rows' )
        total = total.cumsum()

    years = aggregated_df.index
    categories = aggregated_df.columns

    sns.set( font=lineplot_kw['font'], style=lineplot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")

    fig = plt.figure( figsize=( lineplot_kw['fig_width'], lineplot_kw['fig_height'] ) )
    ax = plt.gca()
    for j, category_j in enumerate( categories ):

        ys = aggregated_df[category_j]

        ax.plot(
            years,
            ys,
            linewidth = lineplot_kw['linewidth'],
            alpha = 0.5,
            zorder = 2,
            color = lineplot_kw['category_colors'][category_j],
        )
        ax.scatter(
            years,
            ys,
            label = category_j,
            zorder = 2,
            color = lineplot_kw['category_colors'][category_j],
            s = lineplot_kw['marker_size'],
            )

        # Add labels
        if lineplot_kw.get( 'include_annotations', False ):
            label_y = ys.iloc[-1]

            text = ax.annotate(
                text = category_j,
                xy = ( 1, label_y ),
                xycoords = matplotlib.transforms.blended_transform_factory( ax.transAxes, ax.transData ),
                xytext = ( -5 + 10 * ( lineplot_kw['annotations_horizontal_alignment'] == 'left' ), 0 ),
                va = 'center',
                ha = lineplot_kw['annotations_horizontal_alignment'],
                textcoords = 'offset points',
            )
            text.set_path_effects([
                path_effects.Stroke(linewidth=2.5, foreground='w'),
                path_effects.Normal(),
            ])

    if lineplot_kw['show_total']:
        ax.plot(
            years,
            total,
            linewidth = lineplot_kw['linewidth'],
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
            s = lineplot_kw['marker_size'],
        )

    ymax = lineplot_kw['y_lim'][1]

    ax.set_xticks( years )
    count_ticks = np.arange( 0, ymax, lineplot_kw['tick_spacing'] )
    ax.set_yticks( count_ticks )

    if lineplot_kw['log_yscale']:
        ax.set_yscale( 'log' )

    ax.set_xlim( years[0], years[-1] )
    ax.set_ylim( lineplot_kw['y_lim'] )


    if lineplot_kw.get( 'include_legend', False ):
        l = ax.legend(
            bbox_to_anchor = ( lineplot_kw['legend_x'], lineplot_kw['legend_y'] ),
            loc = '{} {}'.format(
                lineplot_kw['legend_vertical_alignment'],
                lineplot_kw['legend_horizontal_alignment']
            ), 
            framealpha = 1.,
            fontsize = plot_context['legend.fontsize'] * lineplot_kw['legend_scale'],
            ncol = len( categories ) // 4 + 1
        )

    # Labels, inc. size
    ax.set_xlabel( lineplot_kw['x_label'], fontsize=plot_context['axes.labelsize'] * lineplot_kw['font_scale'] )
    ax.set_ylabel( lineplot_kw['y_label'], fontsize=plot_context['axes.labelsize'] * lineplot_kw['font_scale'] )
    ax.tick_params( labelsize=plot_context['xtick.labelsize']*lineplot_kw['font_scale'] )

    # return facet_grid
    return fig

################################################################################

def setup_stackplot_settings( st_loc, default_x_label, default_y_label ):
    '''Get user input for the lineplot.

    Args:
        st_loc (streamlit): The streamlit object to use.
        default_x_label (str): The default x label.
        default_y_label (str): The default y label.

    Returns:
        stackplot_kw (dict): The plotting keywords.
    '''

    stackplot_kw = {
        'x_label': st_loc.text_input( 'stackplot x label', value=default_x_label ),
        'y_label': st_loc.text_input( 'stackplot y label', value=default_y_label ),
        'horizontal_alignment': st_loc.selectbox( 'label alignment', [ 'right', 'left' ], index=0 ),
    }

    return stackplot_kw

################################################################################

def stackplot( aggregated_df, total, **stackplot_kw ):
    '''Function to plot the relative contribution of the categories.

    Args:
        counts (pd.DataFrame): The dataframe containing the counts per year per category.
        stackplot_kw (dict): The plotting keywords. Typically set things like font size, figure dimensions, etc.

    Returns:
        fig (matplotlib.figure.Figure): The figure containing the plot.
    '''

    sns.set( font=stackplot_kw['font'], style=stackplot_kw['seaborn_style'] )
    plot_context = sns.plotting_context("notebook")


    if stackplot_kw['cumulative']:
        aggregated_df = aggregated_df.cumsum( axis='rows' )

    years = aggregated_df.index
    categories = aggregated_df.columns

    # Get data
    sum_total = aggregated_df.sum( axis='columns' )
    fractions = aggregated_df.mul( 1./sum_total, axis='rows' ).fillna( value=0. )
    
    fig = plt.figure( figsize=( stackplot_kw['fig_width'], stackplot_kw['fig_height'] ) )
    ax = plt.gca()
    
    stack = ax.stackplot(
        years,
        fractions.values.transpose(),
        linewidth = 0.3,
        colors = [ stackplot_kw['category_colors'][category_j] for category_j in categories ],
        labels = categories,
    )
    ax.set_xlim( years[0], years[-1] )
    ax.set_ylim( 0, 1. )
    ax.set_xticks( years )
    ax.set_ylabel( 'Fraction of Articles' )

    # Add labels
    if stackplot_kw.get( 'include_annotations', False ):
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
                xytext = ( -5 + 10 * ( stackplot_kw['annotations_horizontal_alignment'] == 'left' ), 0 ),
                va = 'center',
                ha = stackplot_kw['annotations_horizontal_alignment'],
                textcoords = 'offset points',
            )
            text.set_path_effects([
                path_effects.Stroke(linewidth=2.5, foreground='w'),
                path_effects.Normal(),
            ])

    if stackplot_kw.get( 'include_legend', False ):
        l = ax.legend(
            bbox_to_anchor = ( stackplot_kw['legend_x'], stackplot_kw['legend_y'] ),
            loc = '{} {}'.format(
                stackplot_kw['legend_vertical_alignment'],
                stackplot_kw['legend_horizontal_alignment']
            ), 
            framealpha = 1.,
            fontsize = plot_context['legend.fontsize'] * stackplot_kw['legend_scale'],
            ncol = len( categories ) // 4 + 1
        )

    # Labels, inc. size
    ax.set_xlabel( stackplot_kw['x_label'], fontsize=plot_context['axes.labelsize'] * stackplot_kw['font_scale'] )
    ax.set_ylabel( stackplot_kw['y_label'], fontsize=plot_context['axes.labelsize'] * stackplot_kw['font_scale'] )
    ax.tick_params( labelsize=plot_context['xtick.labelsize']*stackplot_kw['font_scale'] )

    return fig

################################################################################

def view_time_series(
        view,
        preprocessed_df,
        selected_df,
        aggregated_df,
        total,
        data_kw,
        lineplot_kw,
        stackplot_kw,
        filetag = None,
        tag = '',
    ):

    if tag != '':
        tag += ':'

    # For easy access
    year_column, y_column, groupby_column = data_kw['year_column'], data_kw['y_column'], data_kw['groupby_column']

    # Tag for the file
    if filetag is None:
        filetag = '{}.{}.{}'.format( *[
            _.lower().replace( ' ', '_' )
            for _ in [ year_column, y_column, groupby_column ]
        ] )

    if view == 'lineplot':
        # st.spinner provides a visual indicator that the data is loading
        with st.spinner():
            fig = lineplot(
                aggregated_df,
                total,
                **lineplot_kw
            )
            st.pyplot( fig )
        # Add a download button for the image
        # The image is saved as PDF, enabling arbitrary resolution
        fn = 'lineplot.{}.pdf'.format( filetag )
        img = io.BytesIO()
        fig.savefig( img, format='pdf', bbox_inches='tight' )
        download_kw = {
            'label': "Download Figure",
            'data': img,
            'file_name': fn,
            'mime': "text/pdf",
            'key': '{}lineplot'.format( tag ),
        }

    elif view == 'stackplot':
        with st.spinner():
            fig = stackplot(
                aggregated_df,
                total,
                **stackplot_kw
            )
            st.pyplot( fig )

        # Add a download button for the image
        fn = 'stackplot.{}.pdf'.format( filetag )
        img = io.BytesIO()
        fig.savefig( img, format='pdf', bbox_inches='tight' )
        download_kw = {
            'label': "Download Figure",
            'data': img,
            'file_name': fn,
            'mime': "text/pdf",
            'key': '{}stackplot'.format( tag ),
        }

    elif view == 'data':

        # The selected data is shown in a table,
        # so that the user can always see the raw data being plotted
        st.header( 'Selected Data' )
        with st.spinner():
            original_and_selected_df = preprocessed_df.loc[preprocessed_df['id'].isin( selected_df['id'] )]
            st.markdown( 'This table contains all {} selected entries.'.format( len( original_and_selected_df ) ) )
            st.write( original_and_selected_df )

        # Add a download button for the data
        fn = 'data.{}.csv'.format( filetag )
        f = io.BytesIO()
        selected_df.to_csv( f )
        download_kw = {
            'label': "Download Selected Data",
            'data': f,
            'file_name': fn,
            'mime': "text/plain",
            'key': 'data.{}'.format( filetag ),
            'key': '{}data'.format( tag ),
        }

    return download_kw