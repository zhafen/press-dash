'''General-purpose functions for the dashboard.
Most functions should be useful for most datasets.
'''
import copy
import numpy as np
import os
import pandas as pd
import re
import streamlit as st
import yaml

import matplotlib
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import seaborn as sns

################################################################################

def load_config( config_fp ):
    '''Get the config. This is done once per session.
    The config directory is set as the working directory.

    Args:
        config_fp (str): Filepath for the config file.

    Returns:
        config (dict): The config dictionary.
    '''

    config_dir, config_fn = os.path.split( config_fp )

    # Check if we're in the directory the script is in,
    # which should also be the directory the config is in.
    # If not, move into that directory
    if os.getcwd() != config_dir:
        os.chdir( config_dir )

    with open( config_fn, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

################################################################################

def generate_widgets( st_loc, instructions, defaults={}, options={}, include=None ):
    '''Wrapper for generating widgets, which are the user input objects.
    This function should *not* be used for one-off creation of widgets.
    It's much much simpler to use streamlit directly for that.
    This is only if there is a set of widgets that are used repeatedly,
    with some variations.

    Args:
        st_loc (streamlit object): Where to put the user input.
        instructions (dict): How to generate the widgets.
        defaults (dict): Default values for the widgets.
            I.e. what the user sees as the standard value
        options (dict): The set of options the user can select from.
        include (list): Which widgets to include. If None, include all.

    Returns:
        widgets (dict of streamlit objects): The widgets.
    '''

    widgets = {}
    for key, instruction in instructions.items():

        # Skip over widgets we don't want
        if include is not None:
            if key not in include:
                continue

        # If the instructions is just a value, keep it.
        if not isinstance( instruction, dict ):
            widgets[key] = instruction
            continue

        # So there's no error thrown
        if 'kwargs' not in instruction:
            instruction['kwargs'] = {}
        if 'key' not in instruction:
            instruction['key'] = None

        # Create the widget
        if instruction['widget'] == 'checkbox':
            widgets[key] = st_loc.checkbox(
                instruction['label'],
                value=defaults.get( key, instruction['default'] ),
                key=instruction['key'],
                **instruction['kwargs']
            )
        elif instruction['widget'] == 'selectbox':
            widgets[key] = st_loc.selectbox(
                instruction['label'],
                options=options.get( key, instruction['options'] ),
                index=defaults.get( key, instruction['default'] ),
                key=instruction['key'],
                **instruction['kwargs']
            )
        elif instruction['widget'] == 'multiselect':
            widgets[key] = st_loc.multiselect(
                instruction['label'],
                options=options.get( key, instruction['options'] ),
                default=defaults.get( key, instruction['default'] ),
                key=instruction['key'],
                **instruction['kwargs']
            )
        elif instruction['widget'] == 'slider':
            widgets[key] = st_loc.slider(
                instruction['label'],
                instruction['min_value'],
                instruction['max_value'],
                value=defaults.get( key, instruction['default'] ),
                key=instruction['key'],
                **instruction['kwargs']
            )
        else:
            widgets[key] = getattr( st_loc, instruction['widget'] )(
                instruction['label'],
                **instruction['kwargs']
            )

    return widgets

################################################################################

def setup_data_axes(
        st_loc,
        config,
        defaults={},
        options={},
        include=[ 'count_or_sum', 'y_column', 'year_column', 'groupby_column'],
        count_or_sum='Count',
    ):
    '''
    Args:
        count_or_sum (str): If we're not prompting the user for a count or sum
            (i.e. it's not in include), then we need to know what to do for the y_column.
    
    '''

    # We have to add the data settings to a dictionary piece-by-piece
    # because as soon as they're called the user input exists.
    data_axes_kw = {}
    if 'count_or_sum' in include:
        data_axes_kw['count_or_sum'] = st_loc.selectbox(
            'Do you want to count entries or sum a column?',
            [ 'Count', 'Sum' ],
            index= defaults.get( 'count_or_sum', 0 ),
        )
    else:
        data_axes_kw['count_or_sum'] = count_or_sum
    if 'y_column' in include:
        if data_axes_kw['count_or_sum'] == 'Count':
            data_axes_kw['y_column'] = st_loc.selectbox(
                'What do you want to count unique entries of?',
                options.get( 'y_column', config['id_columns'] ),
                index=defaults.get( 'y_column', 0 ),
            )
        elif data_axes_kw['count_or_sum'] == 'Sum':
            data_axes_kw['y_column'] = st_loc.selectbox(
                'What do you want to sum?',
                options.get( 'y_column', config['weight_columns'] ),
                index=defaults.get( 'y_column', 0 ),
            )
    if 'year_column' in include:
        data_axes_kw['year_column'] = st_loc.selectbox(
            'What do you want to use as the year of record?',
            options.get( 'year_column', config['year_columns'] ),
            index=defaults.get( 'year_column', 0 ),
        )
    if 'groupby_column' in include:
        data_axes_kw['groupby_column'] = st_loc.selectbox(
            'What do you want to group the data by?',
            options.get( 'groupby_column', config['categorical_columns'] ),
            index=defaults.get( 'groupby_column', 0 ),
        )

    return data_axes_kw

################################################################################

def setup_data_settings(
        st_loc,
        defaults={},
        include=[ 'show_total', 'cumulative', 'recategorize', 'combine_single_categories' ],
):
    ''''''

    data_kw = {}
    if 'show_total' in include:
        data_kw['show_total'] = st_loc.checkbox(    
            'show total',
            value=defaults.get( 'show_total', True ),
        )
    if 'cumulative' in include:
        data_kw['cumulative'] = st_loc.checkbox(
            'use cumulative values',
            value=defaults.get( 'cumulative', False ),
        )
    if 'recategorize' in include:
        data_kw['recategorize'] = st_loc.checkbox(
            'use combined categories (avoids double counting; definitions can be edited in the config)',
            value=defaults.get( 'recategorize', True ),
        )
        if 'combine_single_categories' in include:
            data_kw['combine_single_categories'] = st_loc.checkbox(
                'group all undefined categories as "Other"',
                value=defaults.get( 'combine_single_categories', False ),
            )

    return data_kw

################################################################################

def setup_figure_settings(
        st_loc,
        defaults={},
        include=[
            'seaborn_style',
            'fig_width',
            'fig_height',
            'font_scale',
            'include_legend',
            'legend_scale',
            'legend_x',
            'legend_y',
            'legend_horizontal_alignment',
            'legend_vertical_alignment',
            'include_annotations',
            'annotations_horizontal_alignment',
            'font',
            'color_palette'
        ],
        color_palette='deep'
    ):
    '''Generic and common figure settings.

    Args:
        st_loc (streamlit object): Where to place the figure settings.
        tags (list): The categories that will be colored.
        config (dict): The config dictionary.

    Returns:
        plot_kw (dict): Generic figure settings.
    '''

    # Set up generic figure settings
    fig_width, fig_height = matplotlib.rcParams['figure.figsize']
    # The figure size is doubled because this is a primarily horizontal plot
    fig_width *= 2.
    plot_kw = {}
    if 'seaborn_style' in include:
        plot_kw['seaborn_style'] = st_loc.selectbox(
            'choose seaborn plot style',
            [ 'whitegrid', 'white', 'darkgrid', 'dark', 'ticks', ],
            index=defaults.get( 'seaborn_style', 0 ),
        )
    if 'fig_width' in include:
        plot_kw['fig_width'] = st_loc.slider(
            'figure width',
            0.1*fig_width,
            2.*fig_width,
            value=defaults.get( 'fig_width', fig_width ),
        )
    if 'fig_height' in include:
        plot_kw['fig_height'] = st_loc.slider(
            'figure height',
            0.1*fig_height,
            2.*fig_height,
            value=defaults.get( 'fig_height', fig_height ),
        )
    if 'font_scale' in include:
        plot_kw['font_scale'] = st_loc.slider(
            'font scale',
            0.1,
            2.,
            value=defaults.get( 'font_scale', 1. ),
        )
    if 'include_legend' in include:
        plot_kw['include_legend'] = st_loc.checkbox(
            'include legend',
            value=defaults.get( 'include_legend', True ),
        )
    if plot_kw.get( 'include_legend', False ):
        if 'legend_scale' in include:
            plot_kw['legend_scale'] = st_loc.slider(
                'legend scale',
                0.1,
                2.,
                value=defaults.get( 'legend_scale', 1. ),
            )
        if 'legend_x' in include:
            plot_kw['legend_x'] = st_loc.slider(
                'legend x',
                0.,
                1.5,
                value=defaults.get( 'legend_x', 1. ),
            )
        if 'legend_y' in include:
            plot_kw['legend_y'] = st_loc.slider(
                'legend y',
                0.,
                1.5,
                value=defaults.get( 'legend_y', 1. ),
            )
        if 'legend_horizontal_alignment' in include:
            plot_kw['legend_horizontal_alignment'] = st_loc.selectbox(
                'legend horizontal alignment',
                [ 'left', 'center', 'right' ],
                index=defaults.get( 'legend_horizontal_alignment', 2 ),
            )
        if 'legend_vertical_alignment' in include:
            plot_kw['legend_vertical_alignment'] = st_loc.selectbox(
                'legend vertical alignment',
                [ 'upper', 'center', 'lower' ],
                index=defaults.get( 'legend_vertical_alignment', 2 ),
            )
    if 'include_annotations' in include:
        plot_kw['include_annotations'] = st_loc.checkbox(
            'include annotations',
            value=defaults.get( 'include_annotations', False ),
        )
    if plot_kw.get( 'include_annotations', False ):
        if 'annotations_horizontal_alignment' in include:
            plot_kw['annotations_horizontal_alignment'] = st_loc.selectbox(
                'annotations horizontal alignment',
                [ 'left', 'center', 'right' ],
                index=defaults.get( 'annotations_horizontal_alignment', 0 ),
            )
    if 'color_palette' in include:
        plot_kw['color_palette'] = sns.color_palette( color_palette )

    if 'font' in include:
        original_font = copy.copy( plt.rcParams['font.family'] )[0]
        # This can be finicky, so we'll wrap it in a try/except
        try:
            ## Get all installed fonts
            font_fps = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
            fonts = [ os.path.splitext( os.path.basename( _ ) )[0] for _ in font_fps ]
            ## Get the default font
            default_font = font_manager.FontProperties(family='Sans Serif')
            default_font_fp = font_manager.findfont( default_font )
            default_index = int( np.where( np.array( font_fps ) == default_font_fp )[0][0] )
            ## Make the selection
            font_ind = st_loc.selectbox(
                'Select font',
                np.arange( len( fonts ) ),
                index=default_index,
                format_func=lambda x: fonts[x]
            )
            font = font_manager.FontProperties( fname=font_fps[font_ind] )
            plot_kw['font'] = font.get_name()
        except:
            plot_kw['font'] = original_font

    return plot_kw

################################################################################

def get_range_and_spacing( total, cumulative, ax_frac=0.1 ):
    '''Solid defaults for ymax and the tick_spacing.

    Args:
        total (pd.Series): The total counts or sums.
        cumulative (bool): Whether the data is cumulative.
        ax_frac (float): Fraction of axis between ticks.

    Returns:
        ymax (float): The maximum y value.
        tick_spacing (float): The spacing between ticks.
    '''

    # Settings for the lineplot
    if cumulative:
        ymax = total.sum().max() * 1.05
    else:
        ymax = total.values.max() * 1.05

    # Round the tick spacing to a nice number 
    unrounded_tick_spacing = ax_frac * ymax
    tick_spacing = np.round( unrounded_tick_spacing, -np.floor(np.log10(unrounded_tick_spacing)).astype(int) )

    return ymax, tick_spacing

################################################################################

def recategorize_data(
        df,
        new_categories,
        recategorize=True,
        combine_single_categories=False
    ):
    '''Recategorize the data, i.e. combine existing categories into new ones.
    The end result is one category per article, so no articles are double-counted.
    However, if the new categories are ill-defined they can contradict one another
    and lead to inconsistencies.

    Args:
        df (pd.DataFrame): The dataframe containing the original data.
        new_categories (dict): The new categories to use.
        recategorize (bool): Whether to recategorize the data. Included for caching.

    Returns:
        recategorized (pd.DataFrame): The dataframe containing the recategorized data.
            One entry per article.
    '''

    # We include the automatic return to help with data caching.
    if not recategorize:
        return df
    
    # Get the condensed data frame
    # This is probably dropping stuff that shouldn't be dropped!!!!!!!
    recategorized = df.drop_duplicates( subset='id', keep='first' )
    recategorized.set_index( 'id', inplace=True )

    for groupby_column, new_categories_per_grouping in new_categories.items():
        recategorized_groupby = recategorize_data_per_grouping(
            df,
            groupby_column,
            copy.deepcopy( new_categories_per_grouping ),
            combine_single_categories
        )
        recategorized[groupby_column] = recategorized_groupby

    recategorized.reset_index( inplace=True )
    return recategorized

################################################################################

def recategorize_data_per_grouping(
        df,
        groupby_column,
        new_categories_per_grouping,
        combine_single_categories=False
    ):
    '''The actual function doing most of the recategorizing.

    Args:
        df (pd.DataFrame): The dataframe containing the original data.
        groupby_column (str): The category to group the data by, e.g. 'Research Topics'. 
        new_categories_per_grouping (dict): The new categories to use for this specific grouping.

    Returns:
        recategorized (pd.Series): The new categories.
    '''

    # Get the formatted data used for the categories
    dummies = pd.get_dummies( df[groupby_column] )
    dummies['id'] = df['id']
    dummies_grouped = dummies.groupby( 'id' )
    bools = dummies_grouped.sum() >= 1
    n_cats = bools.sum( axis='columns' )
    if bools.values.max() > 1:
        raise ValueError(
            'Categorization cannot proceed---' +
            'At least one category shows up multiple times for a single ID.'
        )

    # Setup return arr
    base_categories = bools.columns
    recategorized_dtype = np.array( new_categories_per_grouping.keys() ).dtype
    recategorized = np.full( len(bools), fill_value='Other', dtype=recategorized_dtype )
    recategorized = pd.Series( recategorized, index=bools.index, name=groupby_column )

    if not combine_single_categories:
        # Do all the single-category entries
        # These will be overridden if any are a subset of a new category
        bools_singles = bools.loc[n_cats == 1]
        for base_category in base_categories:
            is_base_cat = bools_singles[base_category].values
            recategorized.loc[bools_singles.index[is_base_cat]] = base_category

    # Loop through and do the recategorization
    for category_key, category_definition in new_categories_per_grouping.items():
        # Replace the definition with something that can be evaluated
        not_included_cats = []
        for base_category in base_categories:
            if base_category not in category_definition:
                not_included_cats.append( base_category )
                continue
            category_definition = category_definition.replace(
                "'{}'".format( base_category ),
                "row['{}']".format( base_category )
            )
        # Handle the not-included categories
        if 'only' in category_definition:
            category_definition = (
                '(' + category_definition + ') & ( not ( ' +
                ' | '.join(
                    [ "row['{}']".format( cat ) for cat in not_included_cats ]
                ) + ' ) )'
            )
            category_definition = category_definition.replace( 'only', '' )
        is_new_cat = bools.apply( lambda row: eval( category_definition ), axis='columns' )
        recategorized[is_new_cat] = category_key
        
    return recategorized

################################################################################

def setup_filters(
        st_loc,
        df,
        config,
        include_search=True,
        include_categorical_filters=True,
        include_numerical_filters=True,
        categorical_filter_defaults={},
        numerical_filter_defaults={},
        tag = '',
    ):
    '''Request user input for the filters.

    Args:
        st_loc (st object): Location to put the filters widgets.
        df (pd.DataFrame): The dataframe containing the data.
        config (dict): The config dictionary.
        include_search (bool): If True, include the search bar.
        include_categorical_filters (bool): If True, include the categorical filters.
        include_numerical_filters (bool): If True, include the numerical filters.
        categorical_filter_defaults (dict): Default values for the categorical filters.
        numerical_filter_defaults (dict): Default values for the numerical filters.

    Returns:
        search_str (str): What to search the data for.
        search_col (str): What column to search
        categorical_filters (dict): How categories are filtered.
        numerical_filters (dict): Ranges for numerical data filters
    '''

    if tag != '':
        tag += ':'
   
    # Text search
    if include_search:
        search_str = st_loc.text_input(
            'Text search (case insensitive; not a smart search)',
            key='{}search_str'.format( tag ),
        )
        search_col = st_loc.selectbox(
            'Search text in which column?',
            config['text_columns'],
            key='{}search_col'.format( tag ),
        )
    else:
        search_str = ''
        search_col = pd.NA

    # Category restrictions
    if include_categorical_filters:
        # Select which columns to filter on
        if len( categorical_filter_defaults ) == 0:
            multiselect_default = []
        else:
            multiselect_default = list( categorical_filter_defaults.keys() )
        categorical_filter_columns = st_loc.multiselect(
            'What categories do you want to filter on?',
            options=config['categorical_columns'],
            default=multiselect_default,
            key='{}select_categorical_columns'.format( tag ),
        )
        categorical_filter_instructions = {}
        for cat_filter_col in categorical_filter_columns:
            possible_columns = pd.unique( df[cat_filter_col] )
            categorical_filter_instructions[cat_filter_col] = {
                'widget': 'multiselect',
                'label': '"{}" Filter'.format( cat_filter_col ),
                'options': possible_columns,
                'default': possible_columns,
                'key': '{}{}_filter'.format( tag, cat_filter_col),
            }
        categorical_filters = generate_widgets(
            st_loc,
            categorical_filter_instructions,
            defaults=categorical_filter_defaults,
        )
    else:
        categorical_filters = {}

    # Range restrictions
    if include_numerical_filters:
        # Select which columns to filter on
        if len( numerical_filter_defaults ) == 0:
            multiselect_default = []
        else:
            multiselect_default = list( numerical_filter_defaults.keys() )
        numerical_filter_columns = st_loc.multiselect(
            'What numerical columns do you want to filter on?',
            options = config['weight_columns'] + config['year_columns'],
            default = multiselect_default,
            key='{}select_numerical_columns'.format( tag ),
        )
        # Setup filters for each
        numerical_filter_instructions = {}
        for num_filter_col in numerical_filter_columns:
            column_min = float( df[num_filter_col].min() )
            column_max = float( df[num_filter_col].max() )
            numerical_filter_instructions[num_filter_col] = {
                'widget': 'slider',
                'label': '"{}" Filter'.format( num_filter_col ),
                'min_value': column_min,
                'max_value': column_max,
                'default': [column_min, column_max],
                'key': '{}{}_filter'.format( tag, num_filter_col),
            }
        numerical_filters = generate_widgets(
            st_loc,
            numerical_filter_instructions,
            defaults=numerical_filter_defaults,
        )
    else:
        numerical_filters = {}

    return search_str, search_col, categorical_filters, numerical_filters

################################################################################

def filter_data( df, search_str, search_col, categorical_filters, numerical_filters ):
    '''Filter what data shows up in the dashboard.

    Args:
        df (pd.DataFrame): The dataframe containing the data.
        search_str (str): What to search the data for.
        search_col (str): What column to search
        categorical_filters (dict): How categories are filtered.
        numerical_filters (dict): Ranges for numerical data filters

    Returns:
        selected_df (pd.DataFrame): The dataframe containing the selected data.
    '''

    # # Search filter
    if search_str != '':
        is_included = df[search_col].str.extract( '(' + search_str + ')', flags=re.IGNORECASE ).notna().values[:,0]
    else:
        is_included = np.ones( len( df ), dtype=bool )

    # Categories filter
    for cat_filter_col, selected_cats in categorical_filters.items():
        is_included = is_included & df[cat_filter_col].isin( selected_cats )

    # Range filters
    for num_filter_col, column_range in numerical_filters.items():
        is_included = is_included & (
            ( column_range[0] <= df[num_filter_col] ) &
            ( df[num_filter_col] <= column_range[1] )
        )

    selected_df = df.loc[is_included]
    return selected_df
