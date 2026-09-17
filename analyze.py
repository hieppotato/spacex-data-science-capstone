"""Reproducible wrangling, SQL, visual summaries and leak-aware classification."""
from pathlib import Path
import json
import sqlite3
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix
from sklearn.base import clone
from scrape_launches import scrape

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'
OUT.mkdir(exist_ok=True)

SQL={
 'sites': 'SELECT DISTINCT LaunchSite FROM launches ORDER BY LaunchSite',
 'cape_examples': "SELECT Date, LaunchSite FROM launches WHERE LaunchSite LIKE 'CC%' LIMIT 5",
 'nasa_payload': "SELECT COUNT(*) AS launches, SUM(PayloadMass) AS known_payload_kg, COUNT(PayloadMass) AS known_mass_count FROM launches WHERE Customer LIKE '%NASA%'",
 'v11_payload': "SELECT COUNT(*) AS launches, AVG(PayloadMass) AS mean_known_payload_kg FROM launches WHERE BoosterVersion LIKE '%v1.1%'",
 'first_ground_success': "SELECT MIN(Date) AS first_date FROM launches WHERE LandingOutcome LIKE 'Success%ground pad%'",
 'drone_4_to_6_tonnes': "SELECT Date, BoosterVersion, PayloadMass FROM launches WHERE LandingOutcome LIKE 'Success%drone ship%' AND PayloadMass > 4000 AND PayloadMass < 6000 ORDER BY Date",
 'mission_outcomes': 'SELECT MissionOutcome, COUNT(*) AS launches FROM launches GROUP BY MissionOutcome ORDER BY launches DESC',
 'landing_outcomes': 'SELECT LandingOutcome, COUNT(*) AS launches FROM launches GROUP BY LandingOutcome ORDER BY launches DESC',
 'max_payload': 'SELECT Date, BoosterVersion, PayloadMass FROM launches WHERE PayloadMass=(SELECT MAX(PayloadMass) FROM launches) ORDER BY Date',
 '2015_drone_failures': "SELECT strftime('%m',Date) AS month, BoosterVersion, LaunchSite FROM launches WHERE Date LIKE '2015%' AND LandingOutcome LIKE 'Failure%drone ship%'",
 'historical_outcome_rank': "SELECT LandingOutcome, COUNT(*) AS launches FROM launches WHERE Date BETWEEN '2010-06-04' AND '2017-03-20' GROUP BY LandingOutcome ORDER BY launches DESC",
 'site_success': "SELECT LaunchSite,COUNT(*) AS launches,SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END) AS recovered,ROUND(100.0*SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END)/COUNT(*),1) AS recovered_pct FROM launches GROUP BY LaunchSite ORDER BY recovered_pct DESC",
 'normalized_site_success': "SELECT SiteGroup,COUNT(*) AS launches,SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END) AS recovered,ROUND(100.0*SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END)/COUNT(*),1) AS recovered_pct FROM launches GROUP BY SiteGroup ORDER BY recovered_pct DESC",
}

def wrangle():
    d=pd.read_csv(ROOT/'data/dataset_part_1.csv')
    d['Date']=pd.to_datetime(d['Date'])
    d['Class']=d['Outcome'].str.startswith('True').astype(int)
    reference=pd.read_csv(ROOT/'data/dataset_part_2.csv')
    assert np.array_equal(d.Class.values,reference.Class.values)
    assert len(d)==90 and d.FlightNumber.is_unique
    assert not d[['Date','Class','LaunchSite','Orbit']].isna().any().any()
    d.to_csv(OUT/'wrangled.csv',index=False)
    return d

def sql_analysis():
    scraped=scrape()
    con=sqlite3.connect(OUT/'launches.sqlite')
    scraped.to_sql('launches',con,index=False,if_exists='replace')
    result={}
    for name,query in SQL.items():
        r=pd.read_sql_query(query,con)
        r.to_csv(OUT/f'sql_{name}.csv',index=False)
        result[name]=r.to_dict(orient='records')
    con.close()
    (ROOT/'queries.sql').write_text('\n\n'.join(f'-- {name}\n{query};' for name,query in SQL.items()))
    return scraped,result

def modeling(d):
    nums=['FlightNumber','PayloadMass','Flights','Block']
    cats=['Orbit','LaunchSite','GridFins','Reused','Legs']
    # Outcome / Class are labels. Serial is an identifier. ReusedCount is a
    # lifetime snapshot and may reveal future use. LandingPad is also excluded.
    X=d[nums+cats].copy()
    y=d.Class
    prep=ColumnTransformer([
        ('numeric',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),nums),
        ('categorical',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('onehot',OneHotEncoder(handle_unknown='ignore'))]),cats)
    ])
    train,test=train_test_split(np.arange(len(d)),test_size=.2,random_state=42,stratify=y)
    cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
    specs={
        'Logistic regression':(LogisticRegression(max_iter=3000,random_state=42),{'model__C':[.01,.1,1,10,100]}),
        'SVM':(SVC(random_state=42),{'model__C':[.1,1,10], 'model__kernel':['linear','rbf'],'model__gamma':['scale',.01,.1]}),
        'Decision tree':(DecisionTreeClassifier(random_state=42),{'model__max_depth':[2,3,4,6,None],'model__min_samples_leaf':[1,2,4],'model__criterion':['gini','entropy']}),
        'KNN':(KNeighborsClassifier(),{'model__n_neighbors':[3,5,7,9],'model__weights':['uniform','distance'],'model__p':[1,2]})
    }
    scores=[]; fits={}
    for name,(model,grid) in specs.items():
        search=GridSearchCV(Pipeline([('prep',clone(prep)),('model',model)]),grid,cv=cv,scoring='accuracy',n_jobs=1)
        search.fit(X.iloc[train],y.iloc[train])
        pred=search.predict(X.iloc[test])
        scores.append(dict(model=name,cv_accuracy=search.best_score_,cv_std=search.cv_results_['std_test_score'][search.best_index_],
                           test_accuracy=accuracy_score(y.iloc[test],pred),test_balanced_accuracy=balanced_accuracy_score(y.iloc[test],pred),
                           test_f1=f1_score(y.iloc[test],pred),parameters=search.best_params_))
        fits[name]=search.best_estimator_
    best=max(scores,key=lambda v:v['cv_accuracy'])['model']
    pred=fits[best].predict(X.iloc[test])
    cm=confusion_matrix(y.iloc[test],pred,labels=[0,1])
    base=DummyClassifier(strategy='most_frequent').fit(X.iloc[train],y.iloc[train])
    chronological=np.argsort(d.Date.values)
    temporal_scores=[]
    for name,(model,grid) in specs.items():
        search=GridSearchCV(Pipeline([('prep',clone(prep)),('model',clone(model))]),grid,cv=cv,scoring='accuracy',n_jobs=1)
        search.fit(X.iloc[chronological[:-18]],y.iloc[chronological[:-18]])
        temporal_scores.append((search.best_score_,name,search.best_estimator_))
    _,temporal_name,temporal=max(temporal_scores,key=lambda x:x[0])
    temporal_pred=temporal.predict(X.iloc[chronological[-18:]])
    pd.DataFrame(scores).drop(columns='parameters').to_csv(OUT/'model_comparison.csv',index=False)
    pd.DataFrame({'FlightNumber':d.iloc[test].FlightNumber.values,'actual':y.iloc[test].values,'prediction':pred}).to_csv(OUT/'test_predictions.csv',index=False)
    return dict(scores=scores,best_model=best,confusion_matrix=cm.tolist(),test_size=len(test),train_size=len(train),
                baseline_accuracy=accuracy_score(y.iloc[test],base.predict(X.iloc[test])),
                chronological_accuracy=accuracy_score(y.iloc[chronological[-18:]],temporal_pred),
                chronological_test_from=str(d.Date.iloc[chronological[-18]].date()),
                chronological_test_successes=int(y.iloc[chronological[-18:]].sum()),
                chronological_model=temporal_name,
                features=nums+cats,train_indices=train.tolist(),test_indices=test.tolist())

def main():
    d=wrangle()
    scraped,sql=sql_analysis()
    model=modeling(d)
    site=d.groupby('LaunchSite').Class.agg(['size','sum','mean']).reset_index()
    orbit=d.groupby('Orbit').Class.agg(['size','sum','mean']).reset_index()
    yearly=d.groupby(d.Date.dt.year).Class.agg(['size','sum','mean']).reset_index().rename(columns={'Date':'Year'})
    for name,frame in [('site',site),('orbit',orbit),('yearly',yearly)]:
        frame.to_csv(OUT/f'eda_{name}.csv',index=False)
    records=d.copy();records['Date']=records.Date.dt.strftime('%Y-%m-%d');records=records.fillna('')
    metrics=dict(n=len(d),successes=int(d.Class.sum()),date_min=str(d.Date.min().date()),date_max=str(d.Date.max().date()),
                 scraped_n=len(scraped),scraped_date_min=scraped.Date.min(),scraped_date_max=scraped.Date.max(),
                 site=site.to_dict('records'),orbit=orbit.to_dict('records'),yearly=yearly.to_dict('records'),
                 outcomes=d.Outcome.value_counts().to_dict(),sql=sql,model=model,records=records.to_dict('records'))
    (OUT/'metrics.json').write_text(json.dumps(metrics,indent=2,default=str))
    print(json.dumps({k:metrics[k] for k in ['n','successes','scraped_n','scraped_date_min','scraped_date_max','model']},indent=2))
    return metrics

if __name__=='__main__':
    main()
