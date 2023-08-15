Certainly! Here's the complete documentation, including the how-to use the data pipeline with Streamlit and the annotated directory structure:

---

# Data Science Dashboard Project

Welcome to the Data Science Dashboard project! This documentation provides an overview of the project's directory structure and guidelines for using the data pipeline with Streamlit to create interactive and insightful data visualizations for non-technical business administrators.

## Using the Data Pipeline with Streamlit

The data pipeline is a crucial component of your data science dashboard project, responsible for processing and transforming raw data into insights that drive your visualizations and analyses. Follow these steps to effectively utilize the data pipeline along with Streamlit, a user-friendly Python library for creating interactive web applications:

1. **Data Preparation**:
   - Place your raw data files (e.g., CSV, Excel) in the `data/raw_data/` directory.
   - Ensure that your raw data adheres to the expected format.

2. **Configuration**:
   - Modify the `config.yml` file in the `src/` directory to specify configuration settings, such as data sources and processing options.

3. **Data Transformation**:
   - Utilize the `transform.ipynb` notebook in the `src/` directory to perform data transformation tasks.
   - Implement data cleaning, feature engineering, and other necessary manipulations within this notebook.
   - Execute the notebook to generate processed data files, which will be saved in the `data/processed_data/` directory.

4. **Dashboard Implementation with Streamlit**:
   - Work with the `dashboard.py` file in the `src/` directory to build and customize your data science dashboard using Streamlit.
   - Streamlit is a powerful Python library that simplifies the creation of interactive web applications for data visualization and analysis.
   - Leverage the Streamlit utilities provided in the `datasci_dash/` package to create dynamic and user-friendly visualizations and interfaces.
   - Configure your dashboard components, layout, and interactivity based on your specific requirements.

5. **Unit Testing**:
   - Write unit tests using the `tests/` directory to ensure the correctness of your dashboard components and data processing steps.
   - Use the `test_streamlit.py` file to test Streamlit components and the `test_pipeline.py` file for data processing tests.

6. **Execution and Deployment**:
   - Run your data science dashboard by executing the `streamlit run src/dashboard.py` command in your terminal.
   - Ensure that all necessary dependencies are installed, as specified in the `requirements.txt` file.
   - Deploy your dashboard to your desired platform or share it with your target audience.

By following this structured approach and harnessing the capabilities of Streamlit, you can efficiently manage your data pipeline, create insightful visualizations, and deliver valuable insights to your non-technical business administrators.

## Directory Structure

```
DataScienceDashboard/
│
├── src/                          # Source code for dashboard components
│   ├── __init__.py
│   ├── config.yml                # Configuration settings
│   ├── dashboard.py              # Dashboard implementation
│   ├── transform.ipynb           # Data transformation notebook
│
├── datasci_dash/                # Package for dashboard utilities
│   ├── __init__.py
│   └── streamlit_utils.py       # Streamlit utility functions
│
├── tests/                        # Unit tests
│   ├── __init__.py
│   ├── test_streamlit.py         # Tests for Streamlit components
│   ├── test_pipeline.py          # Tests for data processing pipeline
│
├── requirements.txt              # List of project dependencies
│
├── setup.py                      # Setup script for packaging
│
├── .gitignore                    # Git ignore file
│
├── README.md                     # Project documentation
│
├── data/                         # Data storage directory
│   ├── raw_data/                 # Raw data sources
│   │   ├── News_Report_2023-07-25.csv
│   │   └── press_office.xlsx
│   ├── processed_data/           # Processed data and datasets
│   │   ├── press.csv
│
└── test_data/                    # Test datasets for unit testing
    ├── test_data_complete/       # Complete test data with config
    │   ├── raw_data/
    │   │   ├── News_Report_2023-07-25.csv
    │   │   └── press_office.xlsx
    │   ├── processed_data/
    │   │   ├── press.csv
    │   └── config.yml
    ├── test_data_raw_only/       # Raw data only for testing with config
    │   ├── raw_data/
    │   │   ├── News_Report_2023-07-25.csv
    │   │   └── press_office.xlsx
    │   └── config.yml
```

This organized structure ensures a modular and efficient workflow for developing your data science dashboard. It promotes clear separation of concerns, ease of testing, and streamlined deployment of your interactive visualizations.

---

Please feel free to use or customize this documentation as needed for your project. If you have any further questions or require additional assistance, don't hesitate to ask!

# Usage

The instructions below describe how to use and edit the dashboard.
Even if you have never edited code before, the goal of the instructions in [Level 1](#level-1-using-the-dashboard-on-your-computer) is for you to run the dashboard on your computer.
On the other end of things, if you are comfortable with routine use of git, code testing, etc., then jump to [Level 4](#level-4-significant-customization-and-editing) to get an overview of how the dashboard works and what you might want to edit.

## Level 0: Using the Dashboard Online

If the dashboard is currently live at [ciera-press.streamlit.app](https://ciera-press.streamlit.app), you can use the dashboard without any additional effort.
The dashboard has a plethora of features that can be interacted with via the web interface.
One of the main features is the application of filters and the ability to download the edited data and images.

## Level 1: Using the Dashboard on your Computer

This is the minimal set of instructions to run and use the dashboard.
Note: If the dashboard is live online and you don't need to update the data or config, you can skip straight to [Using the Dashboard](#using-the-dashboard-locally).

### Downloading the Code

The code lives in a git repository, but you don't have to know git to retrieve and use it.
The process for downloading the code is as follows:

1. Click on the green "Code" button on [the GitHub repository](), near the top of the page.
2. Select "Download ZIP."
3. Extract the downloaded ZIP file to a location on your computer.

### Using the Dashboard Locally

The downloaded dashboard can be run via the command line:

1. Navigate to the directory containing the downloaded code using the command line or terminal.
2. Enter the following command:
   ```
   streamlit run src/dashboard.py
   ```

### Using the Dashboard Locally
The downloaded dashboard can be run via command line.
Navigate to the directory containing the downloaded code.
To do this ....
Once there, enter
`streamlit run src/dashboard.py`

## Level 2: Changing the Configuration and Data
### The Two Main Components: Pipeline and Streamlit Script
### Editing the Config
Not all configurable options for the data are available via the interface.
Some are stored in the config.
### Running the Pipeline
To run the pipeline, navigate to the directory containing the code and enter
`./src/pipeline.sh ./config.yml`
You can change which configuration file the pipeline uses by replacing `./config.yml` in the previous line with the path to your alternative config, e.g. `~/Desktop/temporary_folder/config.yml`.
It's important to keep the name of the config itself the same.
### Updating the Data
The raw data lives in the `data/raw_data` folder.
To update the data used, add and/or replace the data in this folder.
The pipeline will automatically select the most recent data.
You will then need to run the pipeline to see the updated data in the dashboard.
### Viewing the Logs
Usage logs are automatically output to the `logs` directory.
You can open the notebooks as you would a normal python notebook, if you are familiar with those.

## Level 3: Making Some Edits to the Code
### Downloading the Code (with git)
A basic familiarity with git is highly recommended if you intend to edit the code yourself.
There are many good tutorials available (such as [tutorial A] and [tutorial B]) so I will not cover git usage here.
For convenience, the main command you need to download the code with git is
`git clone https://github.com/CIERA-Northwestern/press-dashboard`
### Editing the Pipeline or Streamlit Script
The main code responsible for doing the data transformations lives at ...
The main code responsible for creating the interactive visualization lives at ...
with much of the functionality inside the utils at ...
It is recommended to use the config whenever ...
### Adding to the Pipeline
You can add new notebooks to the pipeline.
Just make the notebook, place it in the `src` dir, and add its name to the array at the top of `pipeline.sh`.

## Level 4: Significant Customization and Editing
Before making significant edits it is recommended you make your own fork of the dashboard repository,
and make your own edits as a branch.
This will enable you to share your edits as a pull request.
### Repository Structure
An overview of the repository is as follows...
### Running the Test Suite
The dashboard comes with a suite of code tests that help ensure base functionality.
If you are unfamiliar with the concept of code tests, you can find more information at ...
It is recommended you run these tests both before and after editing the code.
To run the tests, simply navigate to the code's root directory (the one containing the original `config.yml` and the readme) and enter
`pytest`
### Editing the Test Suite
The configs are copied over into the test_data folder.
Generated test data is reset before and after every test.
### Updating the Usage and Installation Instructions
If your edits include new packages, you need to add them to both `requirements.txt` and `setup.py`.
You may also consider changing the metadata in setup.py
### Deploying on the Web
You can deploy your app on the web via streamlit.
Go to streamlit.io/cloud (not sure that's the right site) for more information.

## Level 5: Additional Features
### Continuous Integration
Continuous integration is an excellent way to check if your dashboard is likely to function for other users.
Continuous integration can be enabled via GitHub actions.
You have to enable it for your fork.
You can add a badge showing the status of your continuous integration.
Continuous integration can be tested locally using the act code.
Some tests don't work on continuous integration.
These could potentially be debugged, but it's also not clearly worth it.
### Deploying a Private App
streamlit has the option to deploy your code without sharing it publicly.
More information can be found at ...

Certainly! Here's the revised version with direct links to the appropriate sections:

---


## Level 2: Changing the Configuration and Data

### The Two Main Components: Pipeline and Streamlit Script

The dashboard consists of two main components: the data processing pipeline and the Streamlit script for creating interactive visualizations.

### Editing the Config

Not all configurable options for the data are available via the interface. Some are stored in the `config.yml` file.

### Running the Pipeline

To run the pipeline, navigate to the directory containing the code and enter the following command:

```
./src/pipeline.sh ./config.yml
```

You can change which configuration file the pipeline uses by replacing `./config.yml` in the previous line with the path to your alternative config, e.g., `~/Desktop/temporary_folder/config.yml`. It's important to keep the name of the config itself the same.

### Updating the Data

The raw data lives in the `data/raw_data` folder. To update the data used, add and/or replace the data in this folder. The pipeline will automatically select the most recent data. You will then need to run the pipeline to see the updated data in the dashboard.

### Viewing the Logs

Usage logs are automatically output to the `logs` directory. You can open the notebooks as you would a normal Python notebook if you are familiar with those.

Certainly! Here's the continuation and completion of the usage guide with direct links and updated sections:

---

## Level 3: Making Some Edits to the Code

### Downloading the Code (with git)

A basic familiarity with git is highly recommended if you intend to edit the code yourself. There are many good tutorials available (such as [tutorial A] and [tutorial B]) so I will not cover git usage here. For convenience, the main command you need to download the code with git is:

```
git clone https://github.com/CIERA-Northwestern/press-dashboard
```

### Editing the Pipeline or Streamlit Script

The main code responsible for data transformations lives at `src/transform.ipynb`, and the interactive visualization code resides in `src/dashboard.py`. Much of the functionality is also encapsulated in utility functions inside the `datasci_dash/` package, particularly in `datasci_dash/streamlit_utils.py`. It is recommended to use the config whenever possible for any changes.

### Adding to the Pipeline

You can add new notebooks to the pipeline. Create the notebook, place it in the `src` directory, and add its name to the array at the top of `src/pipeline.sh`.

## Level 4: Significant Customization and Editing

Before making significant edits, it is recommended to create your own fork of the dashboard repository and make your own edits as a branch. This will enable you to share your edits as a pull request.

### Repository Structure

An overview of the repository is as follows:

- `src/`: Source code for the dashboard.
- `datasci_dash/`: Package for dashboard utilities.
- `tests/`: Unit tests.
- `requirements.txt`: List of project dependencies.
- `setup.py`: Setup script for packaging.
- `README.md`: Project documentation.
- `data/`: Data storage directory.
- `test_data/`: Test datasets for unit testing.

### Running the Test Suite

The dashboard comes with a suite of code tests that help ensure base functionality. To run these tests:

1. Navigate to the code's root directory (the one containing the original `config.yml` and the readme).
2. Enter the following command:
   ```
   pytest
   ```

### Editing the Test Suite

The configs are copied over into the `test_data` folder. Generated test data is reset before and after every test.

### Updating the Usage and Installation Instructions

If your edits include new packages, add them to both `requirements.txt` and `setup.py`. You may also consider changing the metadata in `setup.py`.

### Deploying on the Web

You can deploy your app on the web using Streamlit sharing. Visit [Streamlit Sharing](https://streamlit.io/sharing) for more information.

## Level 5: Additional Features

### Continuous Integration

Continuous integration is an excellent way to check if your dashboard is likely to function for other users. You can enable continuous integration via GitHub Actions for your fork. You can add a badge showing the status of your continuous integration. It is recommended to run these tests both before and after editing the code. To run the tests, navigate to the code's root directory and enter:

```
pytest
```

### Deploying a Private App

Streamlit allows you to deploy your code without sharing it publicly. More information can be found at [Streamlit Sharing](https://streamlit.io/sharing).

Here are some links to git tutorials that can help users who are new to version control and git:

- [GitHub's "Git Handbook"](https://guides.github.com/introduction/git-handbook/)
- [Git - The Simple Guide](http://rogerdudler.github.io/git-guide/)
- [Atlassian Git Tutorial](https://www.atlassian.com/git/tutorials)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
