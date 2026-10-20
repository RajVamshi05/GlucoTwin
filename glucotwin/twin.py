from dataclasses import dataclass,field
import sqlite3
import pandas as pd
from .features import features,eligible
from .train import calibrated

@dataclass
class Twin:
    patient_id:str
    cursor:int=12
    running:bool=False
    history:list=field(default_factory=list)
    state:dict=field(default_factory=dict)
    def advance(self,length,steps=1):
        self.cursor=min(length-1,self.cursor+steps)
        if self.cursor==length-1:self.running=False
    def reset(self):self.cursor=12;self.running=False;self.history=[];self.state={}
    def update(self,stream,profile,bundle,db_path):
        past=stream.iloc[:self.cursor+1];x=features(past,profile).iloc[[-1]];ok=bool(eligible(x).iloc[0])
        probability=float(calibrated(bundle,x)[0]) if ok else None;stamp=str(past.iloc[-1].timestamp)
        state=dict(patient_id=self.patient_id,timestamp=stamp,prediction_timestamp=stamp,
            observed_glucose=None if pd.isna(past.iloc[-1].glucose_mg_dl) else float(past.iloc[-1].glucose_mg_dl),probability=probability,
            horizon_minutes=bundle['config']['horizon_minutes'],alert='Insufficient data' if probability is None else ('Review' if probability>=bundle['alert_cutoff'] else 'Below alert cutoff'),
            model_version=bundle['version'],features=x.iloc[0].to_dict(),data_quality='Missing or stale' if not ok else ('Recent gaps' if x.missing_fraction_60m.iloc[0]>0 else 'Available'))
        self.state=state
        if not self.history or self.history[-1]['timestamp']!=stamp:self.history.append({k:v for k,v in state.items() if k!='features'})
        with sqlite3.connect(db_path) as con:
            con.execute('CREATE TABLE IF NOT EXISTS predictions (patient_id TEXT, timestamp TEXT, observed_glucose REAL, probability REAL, horizon INTEGER, alert TEXT, model_version TEXT, PRIMARY KEY(patient_id,timestamp,model_version))')
            con.execute('INSERT OR IGNORE INTO predictions VALUES (?,?,?,?,?,?,?)',(self.patient_id,stamp,state['observed_glucose'],probability,state['horizon_minutes'],state['alert'],state['model_version']))
        return state

def local_sensitivity(bundle,x):
    base=float(calibrated(bundle,x)[0]);out=[]
    for col in bundle['features']:
        changed=x.copy();changed[col]=bundle['reference'][col];out.append(dict(feature=col,probability_change=base-float(calibrated(bundle,changed)[0])))
    return pd.DataFrame(out).assign(magnitude=lambda z:z.probability_change.abs()).sort_values('magnitude',ascending=False)
