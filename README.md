# CIERA Press Dashboard

[![Installation and Tests](https://github.com/CIERA-Northwestern/press-dashboard/actions/workflows/installation_and_tests.yml/badge.svg)](https://github.com/CIERA-Northwestern/press-dashboard/actions/workflows/installation_and_tests.yml)


The CIERA press dashboard provides a way for interested individuals to explore data regarding articles published by, and about, individuals associated with the [Center for Interdisciplinary Exploration and Research in Astrophysics](https://ciera.northwestern.edu/) at [Northwestern University](https://www.northwestern.edu/).

Instructions are provided below for various levels of usage.
Even if you have never edited code before, the goal of the instructions in [Level 1](#level-1-using-the-dashboard-on-your-computer) is for you to run the dashboard on your computer.
On the other end of things, if you are comfortable with routine use of git, code testing, etc., then jump to [Level 4](#level-4-significant-customization-and-editing) to get an overview of how the dashboard works and what you might want to edit.

## Table of Contents

- [Level 0: Using the Dashboard Online](#level-0-using-the-dashboard-online)
- [Level 1: Using the Dashboard on your Computer](#level-1-using-the-dashboard-on-your-computer)
- [Level 2: Changing the Configuration and Data](#level-2-changing-the-configuration-and-data)
- [Level 3: Making Some Edits to the Code](#level-3-making-some-edits-to-the-code)
- [Level 4: Significant Customization and Editing](#level-4-significant-customization-and-editing)
- [Level 5: Additional Features](#level-5-additional-features)

## Level 0: Using the Dashboard Online

The dashboard has a plethora of features that can be interacted with via a web interface.
If the dashboard is currently live at [ciera-press.streamlit.app](https://ciera-press.streamlit.app), you can use the dashboard without any additional effort.
One of the main features is the application of filters and the ability to download the edited data and images.

## Level 1: Using the Dashboard on your Computer

This is the minimal set of instructions to run and use the dashboard.

### Downloading the Code

The code lives in a git repository, but you don't have to know git to retrieve and use it.
The process for downloading the code is as follows:

1. Click on the green "Code" button on [the GitHub repository](https://github.com/CIERA-Northwestern/press-dashboard), near the top of the page.
2. Select "Download ZIP."
3. Extract the downloaded ZIP file.
4. Optional: Move the extracted folder (`press-dashboard-main`; referred to as the code's "root directory") to a more-permanent location.

### Installing the Dashboard

Running the dashboard requires Python.
If you do not have Python on your computer it is recommended you download and install [Miniconda](https://docs.conda.io/en/main/miniconda.html).

With Python installed, 
open the directory containing the code (the root directory) in your terminal or command prompt.
If youre a mac user and you've never used a terminal or command prompt before
you can do this by right clicking the extracted folder and selecting "New Terminal at Folder" ([more info](https://support.apple.com/guide/terminal/open-new-terminal-windows-and-tabs-trmlb20c7888/mac); [Windows Terminal is the windows equivalent](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands)).

Once inside the root directory and in a terminal, you can install the code by executing the command
```
pip install -e .
```

### Running the Dashboard Locally

Inside the root directory and in a terminal window, enter
```
streamlit run src/dashboard.py
```
This will open the dashboard in a tab in your default browser.
This does not require internet access.

## Level 2: Updating the Configuration and Data

The dashboard consists of two main components:
the data-processing pipeline and the Streamlit script for creating interactive visualizations in the browser.
We have so far used the Streamlit script (`dashboard.py`),
but changing the data or a subset of the options requires rerunning the data-processing pipeline.

### Editing the Config

Some options are only available in the `config.yml` file found in the `src` directory (`./src/config.yml` if you are in the root directory).
This can be edited with TextEdit (mac), Notepad (Windows), or your favorite code editor.

### Running the Data Pipeline

To run the data-processing pipeline, while in the root directory run the following command in your terminal:
```
./src/pipeline.sh ./src/config.yml
```

### Updating the Data

The raw data lives in the `data/raw_data` folder.
To update the data used, add and/or replace the data in this folder.
The pipeline will automatically select the most recent data.
You will then need to run the data pipeline and the dashboard to see the updated data in the dashboard.

### Viewing the Logs

Usage logs are automatically output to the `logs` directory.
You can open the notebooks as you would a normal Python notebook, if you are familiar with those.

## Level 3: Making Some Edits to the Code

### Downloading the Code (with git)

A basic familiarity with git is highly recommended if you intend to edit the code yourself.
There are many good tutorials available (e.g.
[GitHub's "Git Handbook"](https://guides.github.com/introduction/git-handbook/),
[Atlassian Git Tutorial](https://www.atlassian.com/git/tutorials),
[Git - The Simple Guide](http://rogerdudler.github.io/git-guide/),
[Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)).
For convenience, the main command you need to download the code with git is
```
git clone git@github.com:CIERA-Northwestern/press-dashboard.git`
```

### Editing the Pipeline

If you want to change how the data is processed, edit `src/transform.ipynb`.
The data-processing pipeline runs this notebook when you execute the bash script `./src/pipeline.sh`,
and saves the output in the logs.
It is recommended to use the config whenever possible for any new variables introduced.

### Adding to the Pipeline

You can add additional notebooks to the data-processing pipeline.
Just make the notebook, place it in the `src` dir, and add its name to the array at the top of `src/pipeline.sh`.

### Editing the Streamlit Script

The interactive dashboard is powered by [Streamlit](https://streamlit.io/), a Python library that enables easy interactive access.
Streamlit is built on a very simple idea---to make something interactive, just rerun the script every time the user makes a change.
This enables editing the streamlit script to be almost exactly like an ordinary Python script.
If you know how to make plots in Python, then you know how to make interactive plots with Streamlit.

If you want to change the Streamlit dashboard, edit `src/dashboard.py`.
Much of the Streamlit functionality is also encapsulated in utility functions inside the `datasci_dash/` directory, particularly in `datasci_dash/streamlit_utils.py`.
Streamlit speeds up calculations by caching calls to functions.
If a particular combination of arguments has been passed to the function
(and the function is wrapped in the decorator `st.cache_data` or `st.cache_resource`)
then the results are stored in memory for easy access if the same arguments are passed again.

## Level 4: Significant Customization and Editing

Before making significant edits it is recommended you make your own fork of the dashboard repository,
and make your own edits as a branch.
This will enable you to share your edits as a pull request.

### Repository Structure
The repository is structured as follows:
```
press-dashboard-main/
│
├── README.md                  # Documentation for the project
├── __init__.py
├── src                        # Source code directory
│   ├── __init__.py
|   ├── config.yml              # Configuration file for the dashboard
│   ├── dashboard.py            # Script for interactive dashboard
│   ├── pipeline.sh             # Shell script for running data pipeline
│   └── transform.ipynb         # Jupyter notebook for data transformation
├── press_dash_lib              # Custom library directory
│   ├── __init__.py
│   └── streamlit_utils.py      # Utility functions for the dashboard
├── setup.py                   # Script for packaging the project
├── requirements.txt           # List of project dependencies
├── data                       # Data storage directory
│   ├── raw_data                # Raw data directory
│   |   ├── News_Report_2023-07-25.csv     # Data downloaded from wordpress
│   |   └── press_office.xlsx              # Data provided by the NU press office.
│   └── processed_data          # Processed data directory
│       ├── press.csv           # The raw data combined
│       └── press.exploded.csv  # Reformatted to be one entry for each tag
├── test                       # Test directory
│   ├── __init__.py
│   ├── test_pipeline.py        # Unit tests for data pipeline
│   └── test_streamlit.py       # Unit tests for the dashboard
├── conftest.py                # Configuration for test suite
└── test_data                   # Test datasets
```

### The Test Suite

The dashboard comes with a suite of code tests that help ensure base functionality.
It is recommended you run these tests both before and after editing the code.
To run the tests, simply navigate to the code's root directory and enter
```
pytest
```

### Updating the Usage and Installation Instructions

If your edits include new packages, you need to add them to both `requirements.txt` and `setup.py`.
You may also consider changing the metadata in `setup.py`.

### Deploying on the Web
You can deploy your app on the web using Streamlit sharing.
Visit [Streamlit Sharing](https://streamlit.io/sharing) for more information.

## Level 5: Additional Features

### Continuous Integration

Continuous integration (automated testing) is an excellent way to check if your dashboard is likely to function for other users.
You can enable continuous integration [via GitHub Actions](https://docs.github.com/en/actions/automating-builds-and-tests/about-continuous-integration), including adding a badge showing the status of your tests.
Continuous integration can be tested locally using [act](https://github.com/nektos/act).
Some tests don't work on continuous integration,
and are disabled until the underlying issues are addressed.

### Deploying a Private App
Streamlit has the option to deploy your code without sharing it publicly.
More information can be found [in this section of the Streamlit Sharing documentation](https://docs.streamlit.io/streamlit-community-cloud/share-your-app#make-your-app-public-or-private).


ChatGPT was used in the construction of this document.
