import json,sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from glucotwin.data import generate,load_patient
from glucotwin.features import features,labels,eligible
from glucotwin.twin import Twin
ROOT=Path(__file__).resolve().parents[1]

def test_reproducible():
    a,b=generate(2,2,7);c,d=generate(2,2,7);pd.testing.assert_frame_equal(a,c);pd.testing.assert_frame_equal(b,d)

def test_no_future_feature_leakage():
    e,s=generate(1,2,7);original=features(s,e.iloc[0]).iloc[:101]
    s.loc[101:,'glucose_mg_dl']=999;s.loc[101:,'meal_event']=1;s.loc[101:,'steps']=9999
    pd.testing.assert_frame_equal(original,features(s,e.iloc[0]).iloc[:101])

def test_labels_boundaries_and_missing():
    s=pd.DataFrame({'glucose_mg_dl':[190.]+[100.]*24+[181.]})
    y=labels(s);assert y.iloc[0]==0;assert y.iloc[1]==1;assert y.iloc[2:].isna().all()
    s.loc[4,'glucose_mg_dl']=np.nan;assert np.isnan(labels(s).iloc[0])

def test_stale_withholding():
    e,s=generate(1,2,7);s.loc[10:20,'glucose_mg_dl']=np.nan
    assert not eligible(features(s.iloc[:21],e.iloc[0])).iloc[-1]

def test_partitions_disjoint():
    r=json.loads((ROOT/'artifacts/metrics.json').read_text());sets=[set(v) for v in r['split'].values()]
    for i,a in enumerate(sets):
        for b in sets[i+1:]:assert not a&b
    assert sum(map(len,sets))==r['config']['patients']

def test_twin_replay_log_and_reset(tmp_path):
    bundle=joblib.load(ROOT/'artifacts/model.joblib');e=pd.read_csv(ROOT/'data/patients.csv');p=e.iloc[0];s=load_patient(ROOT/'data',p.patient_id);t=Twin(p.patient_id);db=tmp_path/'events.db'
    first=t.update(s,p,bundle,db);t.update(s,p,bundle,db);assert len(t.history)==1
    t.advance(len(s));second=t.update(s,p,bundle,db);assert second['timestamp']!=first['timestamp'];assert len(t.history)==2
    with sqlite3.connect(db) as c:assert c.execute('SELECT count(*) FROM predictions').fetchone()[0]==2
    t.reset();assert t.cursor==12 and not t.running and not t.history
    t.advance(len(s),999999);assert t.cursor==len(s)-1

def test_live_prefix_parity():
    e,s=generate(1,2,7);pd.testing.assert_series_equal(features(s,e.iloc[0]).iloc[100],features(s.iloc[:101],e.iloc[0]).iloc[-1])
