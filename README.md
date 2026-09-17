# SpaceX Falcon 9 landing analysis

All numerical results come from the included data and executed Python analysis.
Project repository:
https://github.com/hieppotato/spacex-data-science-capstone

Review and understand the work, and follow your course's policy on AI
assistance before submitting it.

## Quick start

Use Python 3.12 in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analyze.py
python build_map.py
python dashboard.py
```

Open `http://127.0.0.1:8050` for the actual Dash app. The dropdown filters launch
sites and the slider filters payload mass. Open `results/launch_sites.html`,
`results/launch_records.html` and `results/proximity.html` in a normal browser
to use the Folium maps. Map tiles and Leaflet assets require Internet access.

`SpaceX_Capstone.ipynb` contains executed cells and outputs. Its code uses the
Python modules in the same directory. `python create_notebook.py` rebuilds it
with actual in-process execution, which avoids a networked Jupyter kernel.
The notebook does not fabricate execution counters or outputs.

## Files and evidence

- `download_data.py`: source URLs, file download and SHA-256 manifest.
- `collect_api.py`: optional API refresh. The community API was unavailable
  during this run (HTTP 525), so the report uses the downloaded IBM extract.
- `scrape_launches.py`: executed BeautifulSoup scraping from the historical
  Wikipedia page. 121 numbered Falcon 9 rows, June 2010 through June 2021.
- `analyze.py`: wrangling, SQLite queries, model fitting and evaluation.
- `queries.sql`: all SQL queries executed for this project.
- `results/sql_*.csv`: actual query outputs, including unknown-payload counts.
- `dashboard.py`: tested Dash layout and callbacks, based on the separate
  56-row IBM dashboard dataset.
- `build_map.py`: markers, launch records, layer control and pad-to-pad
  proximity using supplied educational coordinates.
- `dashboard.py`: run locally to reproduce the interactive figures. Large
  standalone HTML bundles are kept in the downloadable project archive.
- `results/metrics.json`: report numbers, selected model settings and split IDs.
- `data/sources.json`: exact input provenance and known source failures.

## Dataset distinctions

The 90-row IBM modeling cohort covers 2010-06-04 to 2020-11-13. Course `Class=1`
means Outcome starts with `True`, including five controlled ocean landings.
There are 60 positive and 30 other outcomes, including launches without a
landing attempt. This label is not identical to economically reusable recovery.
The input IBM snapshot already includes payload imputation. A raw-data study
should redo imputation using training observations only.

The geographical and Dash teaching cohorts contain 56 launches through June
2018. Their site labels and definitions differ from the model dataset. The SQL
analysis instead uses the freshly scraped 121-row historical Wikipedia cohort.
Do not compare their rates as though the populations were identical.

The source geographical file contains approximate teaching coordinates, with
historical LC-40/SLC-40 labels and an apparent KSC coordinate discrepancy relative
to the API-derived extract. Distances in this project use that supplied file and
are not surveyed operational distances. Record-view dots have a small display
offset to reveal overlaps; popups preserve original coordinates.

## Validation design

Stratified 72/18 split, seed 42. Five-fold training-only CV selects among logistic
regression, SVM, decision tree and KNN. The preprocessing pipeline fits inside
each fold. Target, serial ID, landing pad and lifetime reused count are excluded.
SVM has the highest CV accuracy (88.9%) and holdout accuracy 77.8% (14/18).
The holdout majority baseline is 66.7%. Four false-positive landing predictions
are important even though positive-class recall is 100% in this small test.

A separate chronological experiment trains/selects only on the earlier 72
records and evaluates on the latest 18. Accuracy is 88.9%, versus 83.3% for a
majority baseline. This small advantage does not establish production utility.

## Review notes

1. Review the notebook and PDF and confirm compliance with course AI rules.
2. Run the Folium maps and Dash app locally, capture genuine screenshots and
   replace the coordinate-chart and exported-figure evidence where requested.
   The PDF explicitly identifies the current evidence format.
3. Export the revised presentation to PDF and review it before submitting.

## References

- IBM Skills Network data URLs: `data/sources.json`.
- Wikipedia historical page, revision 1027686922:
  https://en.wikipedia.org/w/index.php?title=List_of_Falcon_9_and_Falcon_Heavy_launches&oldid=1027686922
- SpaceX community API: https://github.com/r-spacex/SpaceX-API
- Pipeline leakage guidance: https://scikit-learn.org/stable/common_pitfalls.html
- Dash callbacks: https://dash.plotly.com/basic-callbacks

Wikipedia-derived data retain their original source attribution and applicable
CC BY-SA terms. The project does not claim ownership of the source datasets.
