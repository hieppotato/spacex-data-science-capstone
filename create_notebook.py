"""Create and execute the accompanying notebook. All embedded outputs are real."""
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT=Path(__file__).resolve().parent
md=nbf.v4.new_markdown_cell
code=nbf.v4.new_code_cell
cells=[
md('# SpaceX Falcon 9 landing analysis\n\nReproducible study using IBM teaching snapshots and archived Wikipedia records.\n\nAI-assisted project draft for learner review. Read the source code and verify your course rules before submission. The community API was unavailable during this run; no live-API collection result is claimed. Dataset cohorts and outcome definitions differ.'),
code('from pathlib import Path\nimport json\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nfrom IPython.display import display\nimport analyze\nfrom dashboard import figures\nfrom build_map import build_map\nROOT = Path.cwd()\nsns.set_theme(style="whitegrid")'),
md('## 1. Sources and provenance\nDownloaded snapshots retain original bytes and SHA-256 hashes in data/sources.json. The optional collect_api.py refresh script is provided separately.'),
code('display(pd.DataFrame(json.loads((ROOT/"data/sources.json").read_text()))[["file","status","url"]])'),
md('## 2. Wrangling and outcome definitions\nCourse Class=1 means Outcome starts with True, including five controlled ocean landings. Other outcomes include no attempt. Class therefore approximates landing success and does not directly measure economically reusable recovery. The IBM snapshot already contains mean-imputed payload values.'),
code('d=analyze.wrangle()\ndisplay(d.head())\ndisplay(d.Outcome.value_counts())\ndisplay(d.isna().sum().rename("missing"))'),
md('## 3. Web scraping and SQL\nBeautifulSoup selects launch tables, removes footnote tags, excludes narrative rows, and parses dates and kilogram payloads. SQL uses this separate scraped cohort, not the 90-row ML dataset. Raw site labels are retained and normalized into SiteGroup for comparison.'),
code('scraped,sql=analyze.sql_analysis()\nprint(f"{len(scraped)} unique numbered Falcon 9 launches: {scraped.Date.min()} to {scraped.Date.max()}")\ndisplay(scraped.head())'),
code('for name,result in sql.items():\n    print(name)\n    print(analyze.SQL[name])\n    display(pd.DataFrame(result))'),
md('## 4. Exploratory data analysis\nColor indicates the course landing Class, not orbital mission outcome. These are associations in a small historical cohort, not causal effects.'),
code('fig,axes=plt.subplots(1,2,figsize=(14,5))\nsns.scatterplot(data=d,x="FlightNumber",y="LaunchSite",hue="Class",ax=axes[0])\nsns.scatterplot(data=d,x="PayloadMass",y="LaunchSite",hue="Class",ax=axes[1])\naxes[0].set_title("Flight number and launch site")\naxes[1].set_title("Payload (kg) and launch site")\nplt.tight_layout();plt.show()'),
code('fig,axes=plt.subplots(1,2,figsize=(14,5))\nd.groupby("Orbit").Class.mean().plot.bar(ax=axes[0],color="#087f8c")\nd.groupby(d.Date.dt.year).Class.mean().plot(ax=axes[1],marker="o",color="#087f8c")\naxes[0].set(title="Success fraction by orbit",ylabel="Course Class=1 fraction",ylim=(0,1.05))\naxes[1].set(title="Yearly success trend",ylabel="Course Class=1 fraction",ylim=(0,1.05))\nplt.tight_layout();plt.show()'),
code('fig,axes=plt.subplots(1,2,figsize=(14,5))\nsns.scatterplot(data=d,x="FlightNumber",y="Orbit",hue="Class",ax=axes[0])\nsns.scatterplot(data=d,x="PayloadMass",y="Orbit",hue="Class",ax=axes[1])\nplt.tight_layout();plt.show()'),
md('## 5. Interactive analytics\nThe Folium HTML files contain markers, outcome records and pad-to-pad proximity. The notebook outputs below come directly from the Dash callback function. Run python dashboard.py to use the site dropdown and payload slider. The separate 56-row dashboard and geographical snapshots have older coverage.'),
code('geo=build_map()\ndisplay(pd.DataFrame(geo["sites"]))\nprint(f"Distance between supplied CCAFS LC-40 and KSC LC-39A coordinates: {geo[\"cape_to_ksc_km\"]:.2f} km")\nprint("Open results/launch_sites.html, launch_records.html, and proximity.html in a browser.")'),
code('pie,scatter,count=figures("ALL",[0,10000])\nprint(count)\ndisplay(pie)\ndisplay(scatter)'),
code('pie,scatter,count=figures("KSC LC-39A",[0,10000])\nprint(count)\ndisplay(pie)\ndisplay(scatter)'),
md('## 6. Predictive analysis\nSplit 72/18, stratified, random_state=42. Fit imputation, scaling and one-hot encoding inside each 5-fold training CV split. Choose the model by training CV accuracy, then evaluate once on the holdout. Outcome, Class, Serial, LandingPad and lifetime ReusedCount never enter features. A separate chronological split repeats training-only model selection.'),
code('model=analyze.modeling(d)\ndisplay(pd.DataFrame(model["scores"]))\nprint("Chosen by CV:",model["best_model"])\nprint("Majority baseline:",model["baseline_accuracy"])'),
code('cm=model["confusion_matrix"]\nsns.heatmap(cm,annot=True,fmt="d",cmap="Blues",xticklabels=["Other","Success"],yticklabels=["Other","Success"])\nplt.xlabel("Predicted");plt.ylabel("Actual");plt.title("SVM: untouched 18-row holdout");plt.show()\nprint("Chronological model:",model["chronological_model"])\nprint("Chronological accuracy:",model["chronological_accuracy"])\nprint("Chronological majority baseline:",model["chronological_test_successes"]/18)'),
md('## 7. Interpretation and limits\nThe model is educational, not a launch-safety or pricing system. An 18-row test set has high uncertainty. Site, mission era and payload are confounded. The Class=1 label includes ocean landings and does not measure refurbishment cost. Historical performance should not be extrapolated to current launches. A future extension should use raw missing payloads, mission-time core histories, grouped or rolling validation, probability calibration and actual recovery economics.'),
]
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}})
shell=InteractiveShell.instance()
import matplotlib
matplotlib.use('module://matplotlib_inline.backend_inline')
execution_count=0
for cell in nb.cells:
    if cell.cell_type!='code':
        continue
    execution_count+=1
    with capture_output() as captured:
        result=shell.run_cell(cell.source,store_history=True)
    if result.error_before_exec or result.error_in_exec:
        raise RuntimeError(f'Cell {execution_count} failed: {result.error_before_exec or result.error_in_exec}')
    cell.execution_count=execution_count
    cell.outputs=[]
    if captured.stdout:
        cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=captured.stdout))
    if captured.stderr:
        cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=captured.stderr))
    for output in captured.outputs:
        cell.outputs.append(nbf.v4.new_output('display_data',data=output.data,metadata=output.metadata))
nbf.write(nb,ROOT/'SpaceX_Capstone.ipynb')
print('Executed notebook:',len(nb.cells),'cells')

if __name__=='__main__':
    pass
