import argparse,json,hashlib
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score,recall_score,f1_score,average_precision_score,roc_auc_score,confusion_matrix,brier_score_loss,precision_recall_curve
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from .data import generate,save_data
from .features import features,labels,eligible,FEATURES,DYNAMIC,baseline_score

def measure(y,p,cut=.5):
    pred=np.asarray(p)>=cut;y=np.asarray(y);tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel();two=len(np.unique(y))==2
    return dict(n=len(y),prevalence=float(y.mean()),precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),
        f1=float(f1_score(y,pred,zero_division=0)),pr_auc=float(average_precision_score(y,p)) if two else None,
        roc_auc=float(roc_auc_score(y,p)) if two else None,brier=float(brier_score_loss(y,p)),false_positive_rate=float(fp/(fp+tn)) if fp+tn else None,
        false_positive_windows_per_100=float(100*fp/len(y)),confusion_matrix=[[int(tn),int(fp)],[int(fn),int(tp)]])

def calibrated(bundle,x):
    p=np.clip(bundle['model'].predict_proba(x[bundle['features']])[:,1],1e-6,1-1e-6)
    return bundle['calibrator'].predict_proba(np.log(p/(1-p)).reshape(-1,1))[:,1]

def run(root,patients=160,days=7,seed=2026,threshold=180,horizon=120):
    root=Path(root);(root/'artifacts').mkdir(parents=True,exist_ok=True);ehr,sensors=generate(patients,days,seed);save_data(ehr,sensors,root/'data');rows=[]
    for _,pr in ehr.iterrows():
        s=sensors[sensors.patient_id==pr.patient_id].reset_index(drop=True);x=features(s,pr)
        x['target']=labels(s,threshold,horizon);x['patient_id']=pr.patient_id;x['timestamp']=s.timestamp
        rows.append(x[(x.index>=12)&(x.index%3==0)&x.target.notna()&eligible(x)])
    table=pd.concat(rows,ignore_index=True);ids=ehr.patient_id.to_numpy().copy();np.random.default_rng(seed).shuffle(ids)
    a,b,c=int(.55*patients),int(.70*patients),int(.85*patients)
    split=dict(train=ids[:a].tolist(),validation=ids[a:b].tolist(),calibration=ids[b:c].tolist(),test=ids[c:].tolist())
    sets={k:table[table.patient_id.isin(v)] for k,v in split.items()}
    for name,d in sets.items():
        if d.target.nunique()!=2:raise ValueError(f'{name} lacks both classes; increase population/days transparently.')
    tr,va,ca,te=[sets[k] for k in ['train','validation','calibration','test']];trials=[];models=[]
    for leaves in [7,15]:
        m=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=leaves,learning_rate=.08,l2_regularization=5,early_stopping=False,random_state=seed)
        m.fit(tr[FEATURES],tr.target);ap=average_precision_score(va.target,m.predict_proba(va[FEATURES])[:,1]);trials.append(dict(max_leaf_nodes=leaves,validation_pr_auc=float(ap)));models.append(m)
    best=int(np.argmax([t['validation_pr_auc'] for t in trials]));model=models[best]
    p=np.clip(model.predict_proba(ca[FEATURES])[:,1],1e-6,1-1e-6);calibrator=LogisticRegression(C=1e6).fit(np.log(p/(1-p)).reshape(-1,1),ca.target)
    config=dict(patients=patients,days=days,seed=seed,threshold=threshold,horizon_minutes=horizon)
    version='gt-1.0-'+hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:8]
    bundle=dict(model=model,calibrator=calibrator,features=FEATURES,config=config,version=version,reference=tr[FEATURES].median().to_dict(),alert_cutoff=.5)
    prob=calibrated(bundle,te);raw=model.predict_proba(te[FEATURES])[:,1];base=(baseline_score(te,horizon)>threshold).astype(float)
    ab=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=trials[best]['max_leaf_nodes'],learning_rate=.08,l2_regularization=5,early_stopping=False,random_state=seed).fit(tr[DYNAMIC],tr.target)
    ap=np.clip(ab.predict_proba(ca[DYNAMIC])[:,1],1e-6,1-1e-6);abc=LogisticRegression(C=1e6).fit(np.log(ap/(1-ap)).reshape(-1,1),ca.target)
    abundle=dict(model=ab,calibrator=abc,features=DYNAMIC);precision,recall,_=precision_recall_curve(te.target,prob);frac,mean=calibration_curve(te.target,prob,n_bins=10,strategy='quantile')
    imp=permutation_importance(model,va[FEATURES],va.target,scoring='average_precision',n_repeats=2,random_state=seed,max_samples=2500,n_jobs=1)
    importance=sorted([dict(feature=f,importance=float(v)) for f,v in zip(FEATURES,imp.importances_mean)],key=lambda x:-x['importance']);below=te.current_glucose<=threshold
    report=dict(config=config,version=version,algorithm='HistGradientBoostingClassifier',split=split,rows={k:len(v) for k,v in sets.items()},sensor_rows=len(sensors),trials=trials,
        ml=measure(te.target,prob),baseline=measure(te.target,base),dynamic_only=measure(te.target,calibrated(abundle,te)),below_threshold_at_prediction=measure(te.target[below],prob[below]),raw_brier=float(brier_score_loss(te.target,raw)),
        pr_curve=dict(precision=precision.tolist(),recall=recall.tolist()),calibration=dict(mean_prediction=mean.tolist(),event_fraction=frac.tolist()),importance=importance)
    pd.DataFrame(dict(patient_id=te.patient_id,timestamp=te.timestamp,y=te.target,probability=prob,baseline=base,current_glucose=te.current_glucose)).to_csv(root/'artifacts/test_predictions.csv',index=False)
    joblib.dump(bundle,root/'artifacts/model.joblib');(root/'artifacts/metrics.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ['version','rows','ml','baseline','dynamic_only']},indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--patients',type=int,default=160);p.add_argument('--days',type=int,default=7);p.add_argument('--seed',type=int,default=2026);p.add_argument('--threshold',type=float,default=180);p.add_argument('--horizon',type=int,default=120);a=p.parse_args()
    if a.patients<20 or a.days<2:p.error('Use at least 20 patients and 2 days.')
    run(a.root,a.patients,a.days,a.seed,a.threshold,a.horizon)
