import unittest

import datetime
import glob
import os
import shutil
import subprocess
import yaml

###############################################################################

class TestPipeline( unittest.TestCase ):

    def setUp( self ):

        # Get filepath info
        test_dir = os.path.abspath( os.path.dirname( __file__ ) )
        self.root_dir = os.path.dirname( test_dir )
        self.test_data_dir = os.path.join( self.root_dir, 'test_data', 'test_data_raw_only' )
        root_config_fp = os.path.join( self.root_dir, 'src', 'config.yml' )
        self.config_fp = os.path.join( self.test_data_dir, 'config.yml' )
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Set up temporary dirs
        self.temp_dirs = {
            'processed_data_dir': os.path.join( self.test_data_dir, 'processed_data' ),
            'figure_dir': os.path.join( self.test_data_dir, 'figures' ),
            'logs_dir': os.path.join( self.root_dir, 'logs' ),
        }
        for key, temp_dir in self.temp_dirs.items():
            if os.path.isdir( temp_dir ):
                shutil.rmtree( temp_dir )

        # Set up news data fp
        self.news_data_fp = os.path.join( self.test_data_dir, 'raw_data', 'News_Report_2023-07-25.csv' )
        self.dup_news_data_fp = self.news_data_fp.replace( '07-25', 'null-null' )

        # Copy and edit config
        with open( root_config_fp, 'r' ) as f:
            config_text = f.read()
        config_text = config_text.replace( '../data', '.' )
        config_text = config_text.replace( './', '')
        with open( self.config_fp, 'w' ) as f:
            f.write( config_text )

    ###############################################################################

    def tearDown( self ):

        # Remove dashboard and figures temp dirs
        for key in [ 'processed_data_dir', 'figure_dir', 'logs_dir' ]:
            temp_dir = self.temp_dirs[key]
            if os.path.isdir( temp_dir ):
                shutil.rmtree( temp_dir )

        if os.path.exists( self.dup_news_data_fp ):
            os.remove( self.dup_news_data_fp )

        if os.path.isfile( self.config_fp ):
            os.remove( self.config_fp )

    ###############################################################################

    def test_parse_config( self ):

        with open( self.config_fp, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        # Paths are relative to the config
        os.chdir( os.path.dirname( self.config_fp ) )
        assert config['data_dir'] == os.path.relpath( self.test_data_dir )
        assert config['figure_dir'] == os.path.relpath( self.temp_dirs['figure_dir'] )

    ###############################################################################

    def check_processed_data_and_logs( self ):
        '''This method is re-used a few times to ensure that the requested output is available.'''

        # Check that there are output files
        output_files = [
            ( 'counts', 'counts.categories.csv', ),
            ( 'counts', 'counts.press_types.csv', ),
            ( 'counts', 'counts.research_topics.csv', ),
            ( 'press.csv', ),
            ( 'press.exploded.csv', ),
        ]
        for output_file in output_files:
            output_fp = os.path.join( self.temp_dirs['processed_data_dir'], *output_file )
            assert os.path.isfile( output_fp )

        # Check that there's an output NB in the logs
        transform_fps = glob.glob( os.path.join( self.temp_dirs['logs_dir'], 'transform*.py' ) )
        assert len( transform_fps ) > 0

    ###############################################################################

    def test_transform( self ):
        '''Test that the transform works.'''

        # Move to the config directory
        nb_fp = os.path.join( self.root_dir, 'src', 'transform.ipynb' )
        script_fn_base = 'transform.{}.test'.format( self.timestamp )
        command = ' '.join( (
            'jupyter',
            'nbconvert',
            '--to script',
            nb_fp,
            '--output={}'.format( script_fn_base ),
            '--output-dir={}'.format( self.temp_dirs['logs_dir'] ),
        ) )
        conversion_subprocess_output = subprocess.run(
            command,
            shell = True,
            capture_output = True,
            cwd = self.test_data_dir,
        )
        assert conversion_subprocess_output.returncode == 0

        execution_subprocess_output = subprocess.run(
            'python {}.py'.format( os.path.join( self.temp_dirs['logs_dir'], script_fn_base )),
            shell = True,
            capture_output = True,
            cwd = self.test_data_dir,
        )
        assert execution_subprocess_output.returncode == 0

        self.check_processed_data_and_logs()

    ###############################################################################

    @unittest.skip( "This attempts to use nbconvert's --to notebook functionality, but that function does not work with a changing working directory." )
    def test_transform_execute_as_nb( self ):
        '''Test that transform works when executing the notebook directly.
        This would be nice because it would create the script that was run, and show the results alongside it in NB format.
        '''

        # Move to the config directory
        os.chdir( self.test_data_dir )

        nb_fp = os.path.join( self.root_dir, 'src', 'transform.ipynb' )
        command = ' '.join( (
            'jupyter',
            'nbconvert',
            '--to notebook',
            '--execute {}'.format( nb_fp ),
            '--output=transform.{}.test.ipynb'.format( self.timestamp ),
            '--output-dir={}'.format( self.temp_dirs['logs_dir'] ),
        ) )
        subprocess_output = subprocess.run(
            command,
            shell = True,
            capture_output = True,
            cwd = self.test_data_dir,
        )

        # Ensure it ran successfully
        assert subprocess_output.returncode == 0

        self.check_processed_data_and_logs()

    ###############################################################################

    def test_transform_extra_files( self ):
        '''Test that transform works when there are multiple options.'''

        # Make an extra copy
        shutil.copy( self.news_data_fp, self.dup_news_data_fp )

        self.test_transform()

    ###############################################################################

    def test_pipeline( self ):
        '''Test the pipeline script works.'''

        command = ' '.join( (
            os.path.join( self.root_dir, 'src', 'pipeline.sh' ),
            self.config_fp,
        ) )
        subprocess_output = subprocess.run(
            command,
            shell = True,
            capture_output = True,
            cwd = self.test_data_dir,
        )

        self.check_processed_data_and_logs()

    ###############################################################################

    def test_streamlit( self ):

        # Move to the root directory
        os.chdir( self.root_dir )

        subprocess.check_output([ 'streamlit', './test_dashboard/st_dashboard.py' ])


