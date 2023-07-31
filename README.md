# CIERA Press Dashboard

## How to Run

### 1. Install

Clone the repository, move into the folder containing the repository, and install it using the provided command script.
```
git clone git@github.com:CIERA-Northwestern/press-dashboard.git
cd press-dashboard
./install.sh
```

### 2. Update the data

Using your own data is as simple as updating or replacing the files in `./data/input`.
The `press_office.xlsx` file contains information from the press office, likely manually entered.
The `News_Report*.csv` file contains data downloaded from the CIERA website.

[!WARNING]
Ensure you do not have multiple `News_Report.csv` or `press_office.xlsx` files before running.

### 3. Execute

Run the analysis scripts (i.e. the pipeline) as follows:
```
./press_dashboard_library/pipeline.py ./dashboard/config.yml
```

## Description of Output

**Analysis code** (inside `./dashboard`):
* `dashboard_YYYY-MM-DD.ipynb`: The main notebook for user interaction with the data via python.
* `transform_YYYY-MM-DD.ipynb`: The notebook that transformed (processed) the data.

**Figures** (inside `./dashboard/figures`):
* `counts/counts.*.pdf`: Figures showing article counts per year, grouped by article category, press type, and research topic.

**Processed data** (inside `./data/processed`):
* `press.csv`: Website data and press office data combined in one file.
* `counts/counts.*.csv`: Article count per-year, grouped by article category, press type, and research topic.

## Customizing the Analysis
You can customize the analysis by editing `./dashboard/config.yml`.
Most notably, you can change what day the year starts on by changing `year_start`.
The default start date is September 1, the start of the Northwestern financial year.

