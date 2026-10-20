import numpy as np
import pandas as pd
STATIC=['age','hba1c_pct','historical_fasting_glucose','baseline_glucose','diabetes_duration_years']
DYNAMIC=['current_glucose','mean_15m','mean_30m','mean_60m','sd_60m','slope_15m','heart_rate_bpm','hr_mean_30m','steps_60m','minutes_since_meal','sleep_duration_hours','missing_fraction_60m','minutes_since_glucose','hour_sin','hour_cos']
PERSONAL=['deviation_from_baseline','rolling_deviation'];FEATURES=STATIC+DYNAMIC+PERSONAL

def features(frame,profile):
    f=frame.reset_index(drop=True);raw=f.glucose_mg_dl;g=raw.ffill(limit=3);out=pd.DataFrame(index=f.index)
    out['current_glucose']=g
    for k in [15,30,60]:out[f'mean_{k}m']=g.rolling(k//5,min_periods=1).mean()
    out['sd_60m']=g.rolling(12,min_periods=2).std();out['slope_15m']=(g-g.shift(3))/15
    out['heart_rate_bpm']=f.heart_rate_bpm;out['hr_mean_30m']=f.heart_rate_bpm.rolling(6,min_periods=1).mean()
    out['steps_60m']=f.steps.rolling(12,min_periods=1).sum();pos=pd.Series(np.arange(len(f)),index=f.index)
    last=pos.where(f.meal_event.eq(1)).ffill();out['minutes_since_meal']=((pos-last)*5).fillna(1440).clip(upper=1440)
    out['sleep_duration_hours']=f.sleep_duration_hours;out['missing_fraction_60m']=raw.isna().rolling(12,min_periods=1).mean()
    out['minutes_since_glucose']=((pos-pos.where(raw.notna()).ffill())*5).fillna(1440)
    h=f.timestamp.dt.hour+f.timestamp.dt.minute/60;out['hour_sin']=np.sin(2*np.pi*h/24);out['hour_cos']=np.cos(2*np.pi*h/24)
    for col in STATIC:out[col]=profile[col]
    out['deviation_from_baseline']=g-profile['baseline_glucose'];out['rolling_deviation']=g-g.expanding(min_periods=1).mean()
    return out[FEATURES]

def labels(frame,threshold=180,horizon_minutes=120):
    if horizon_minutes<=0 or horizon_minutes%5:raise ValueError('Horizon must be a positive multiple of five.')
    fut=pd.concat([frame.glucose_mg_dl.shift(-k) for k in range(1,horizon_minutes//5+1)],axis=1)
    return fut.gt(threshold).any(axis=1).astype(float).where(fut.notna().all(axis=1))

def eligible(x):return (x.minutes_since_glucose<=15)&(x.missing_fraction_60m<=.25)&x.current_glucose.notna()
def baseline_score(x,horizon=120):return x.current_glucose+x.slope_15m.fillna(0).clip(lower=0)*horizon
