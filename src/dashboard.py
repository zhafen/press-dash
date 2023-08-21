# Get the config file.
import os
config_dir = os.path.dirname( __file__ )
config_fn = 'config.yml'

# Call the main function.
import importlib
from root_dash_lib.pages import blank_page
importlib.reload( blank_page )
blank_page.main( os.path.join( config_dir, config_fn ) )