from pathlib import Path
import numpy as np
import pandas as pd

def generate(n_patients=160,days=7,seed=2026):
    rng=np.random.default_rng(seed); profiles=[]; streams=[];n=days*288
    ts=pd.date_range('2026-01-01',periods=n,freq='5min'); hours=ts.hour.to_numpy()+ts.minute.to_numpy()/60
    for i in range(n_patients):
        pid=f'PT-{i+1:04d}'; baseline=float(rng.uniform(100,157)); sensitivity=rng.uniform(.65,1.5)
        profiles.append(dict(patient_id=pid,age=int(rng.integers(30,79)),sex=rng.choice(['Female','Male']),
            diabetes_status='Simulated type 2 diabetes',diabetes_duration_years=int(rng.integers(1,22)),
            hba1c_pct=round(float(np.clip(5.8+(baseline-100)*.035+rng.normal(0,.35),5.5,10)),2),
            historical_fasting_glucose=round(baseline+rng.normal(0,8),1),baseline_glucose=round(baseline,2),
            baseline_glucose_sd=round(float(rng.uniform(9,20)),2),diagnoses=rng.choice(['Type 2 diabetes','Type 2 diabetes; hypertension']),
            medication_category=rng.choice(['Synthetic oral-agent category','None recorded']),
            history_note='Entirely synthetic. Baseline predates replay. Medication has no modeled effect.'))
        meal=np.zeros(n);activity=np.zeros(n);sleep=np.zeros(n);response=np.zeros(n)
        for d in range(days):
            sleep[d*288:(d+1)*288]=np.clip(rng.normal(7,1),4,9)
            for hr in [8,13,20]:
                at=int(np.clip(d*288+hr*12+rng.integers(-9,10),0,n-1));meal[at]=1
                lag=np.arange(min(60,n-at));x=lag/10
                response[at:at+len(lag)]+=rng.uniform(35,85)*sensitivity*x*np.exp(1-x)
            for _ in range(2):
                at=d*288+int(rng.integers(80,260));activity[at:min(at+6,n)]=1
        steps=rng.poisson(5,n)+activity*rng.integers(220,500,n)
        act_effect=np.convolve(activity,np.exp(-np.arange(36)/12),mode='full')[:n]*1.4
        noise=np.zeros(n)
        for j in range(1,n):noise[j]=.92*noise[j-1]+rng.normal(0,2)
        g=np.clip(baseline+response-act_effect+6*np.sin(2*np.pi*(hours-4)/24)+2*(7-sleep)+noise+rng.normal(0,1.5,n),60,350)
        missing=rng.random(n)<.012;at=int(rng.integers(50,n-20));missing[at:at+6]=True;g[missing]=np.nan
        hr=np.clip(67+activity*35+7*np.sin(2*np.pi*hours/24)+rng.normal(0,4,n),45,150)
        streams.append(pd.DataFrame(dict(patient_id=pid,timestamp=ts,glucose_mg_dl=g,heart_rate_bpm=hr,
            hrv_ms=np.clip(60-activity*15+rng.normal(0,7,n),15,100),steps=steps.astype(int),sleep_duration_hours=sleep,
            meal_event=meal.astype(int),activity_event=activity.astype(int),sensor_quality=np.where(missing,'missing','ok'))))
    return pd.DataFrame(profiles),pd.concat(streams,ignore_index=True)

def save_data(profiles,sensors,root):
    root=Path(root);(root/'sensors').mkdir(parents=True,exist_ok=True);profiles.to_csv(root/'patients.csv',index=False)
    for pid,g in sensors.groupby('patient_id'):g.to_csv(root/'sensors'/f'{pid}.csv.gz',index=False,compression={'method':'gzip','mtime':0})

def load_patient(root,pid):return pd.read_csv(Path(root)/'sensors'/f'{pid}.csv.gz',parse_dates=['timestamp'])
