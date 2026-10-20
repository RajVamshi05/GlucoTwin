from pathlib import Path
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
import json,sqlite3
import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from glucotwin.data import load_patient
from glucotwin.features import features,eligible
from glucotwin.train import calibrated
from glucotwin.twin import Twin,local_sensitivity
ROOT=Path(__file__).parent
st.set_page_config(page_title='GlucoTwin | Research Console',page_icon='◉',layout='wide')
st.markdown('''<style>
.stApp{background:#f4f7fb;color:#163047} .block-container{padding-top:2rem;max-width:1450px}
h1,h2,h3{letter-spacing:-.035em} [data-testid="stMetric"]{background:white;border:1px solid #dbe5ef;border-radius:14px;padding:18px}
[data-testid="stSidebar"]{background:#e7eff5} .hero{background:#102f42;color:white;padding:28px 32px;border-radius:18px;margin-bottom:22px}
.hero h1{color:white;font-size:44px;margin:0}.hero p{color:#afd9df;margin:6px 0}.label{font-size:12px;letter-spacing:2px;color:#79d5cb}
</style>''',unsafe_allow_html=True)
if not (ROOT/'artifacts/model.joblib').exists():
    st.error('Train the reproducible model first: python -m glucotwin.train');st.stop()
@st.cache_resource
def resources():return joblib.load(ROOT/'artifacts/model.joblib'),json.loads((ROOT/'artifacts/metrics.json').read_text())
@st.cache_data
def profiles():return pd.read_csv(ROOT/'data/patients.csv')
@st.cache_data
def stream(pid):return load_patient(ROOT/'data',pid)
bundle,report=resources();ehr=profiles();cfg=bundle['config']
st.sidebar.title('◉ GLUCOTWIN');st.sidebar.caption('SYNTHETIC RESEARCH CONSOLE')
pid=st.sidebar.selectbox('Synthetic patient',ehr.patient_id.tolist(),index=ehr.patient_id.tolist().index(report['split']['test'][0]))
page=st.sidebar.radio('Workspace',['Executive Overview','Patient Profile','Live Digital Twin','Risk and Explainability','Scenario Simulator','Model Performance','Prediction Log'])
st.sidebar.divider();st.sidebar.caption('Research proof-of-concept. No real wearable connection. No diagnosis or treatment advice.')
st.sidebar.caption(f"Model {bundle['version']}")
if 'twins' not in st.session_state:st.session_state.twins={}
if pid not in st.session_state.twins:st.session_state.twins[pid]=Twin(pid)
twin=st.session_state.twins[pid];s=stream(pid);profile=ehr[ehr.patient_id==pid].iloc[0]
partition=next(k for k,v in report['split'].items() if pid in v)
st.markdown(f'<div class="hero"><div class="label">PATIENT DIGITAL TWIN / SYNTHETIC DATA</div><h1>GlucoTwin</h1><p>From Reactive Glucose Monitoring to Personalized Predictive Health.</p></div>',unsafe_allow_html=True)
st.caption(f'{pid} · {partition.title()} partition · 5-minute simulated observations · Event: any glucose > {cfg["threshold"]:g} mg/dL in the next {cfg["horizon_minutes"]} minutes')

def timeline(past):
    fig=go.Figure(go.Scatter(x=past.timestamp,y=past.glucose_mg_dl,mode='lines',name='Observed synthetic CGM',line=dict(color='#087f8c',width=3),connectgaps=False))
    fig.add_hline(y=cfg['threshold'],line_dash='dash',line_color='#a95922',annotation_text='Event threshold')
    now=past.timestamp.iloc[-1];end=now+pd.Timedelta(minutes=cfg['horizon_minutes'])
    fig.add_vrect(x0=now,x1=end,fillcolor='#087f8c',opacity=.06,line_width=0)
    fig.update_layout(height=370,template='plotly_white',margin=dict(l=15,r=15,t=25,b=15),yaxis_title='Glucose (mg/dL)',xaxis_title='Simulated time (naive local clock)',xaxis_range=[max(past.timestamp.iloc[0],now-pd.Timedelta(hours=12)),end])
    return fig

def metrics(state):
    cols=st.columns(4);g=state['observed_glucose'];p=state['probability']
    cols[0].metric('Latest observed glucose','Missing' if g is None else f'{g:.0f} mg/dL')
    cols[1].metric('Synthetic event estimate','Withheld' if p is None else f'{p:.1%}')
    cols[2].metric('Prediction horizon',f"{cfg['horizon_minutes']} min")
    cols[3].metric('Data quality',state['data_quality'])
    st.caption(f"Twin and prediction timestamp: {state['timestamp']} · {state['alert']} · No validated clinical uncertainty interval")

@st.fragment(run_every='2s')
def live():
    cols=st.columns(5)
    if cols[0].button('Start / Resume',key='start'):twin.running=True
    if cols[1].button('Pause',key='pause'):twin.running=False
    if cols[2].button('Step +5 min',key='step'):twin.running=False;twin.advance(len(s))
    if cols[3].button('Advance +1 hour',key='hour'):twin.running=False;twin.advance(len(s),12)
    if cols[4].button('Reset',key='reset'):twin.reset()
    if twin.running:twin.advance(len(s))
    state=twin.update(s,profile,bundle,ROOT/'artifacts/events.sqlite');metrics(state)
    st.plotly_chart(timeline(s.iloc[:twin.cursor+1]),use_container_width=True)
    st.caption('Shaded area = prediction horizon, not a glucose forecast. This model classifies events and does not forecast a glucose curve.')
    f=state['features'];a,b,c=st.columns(3);a.metric('60-minute mean',f"{f['mean_60m']:.1f} mg/dL");b.metric('15-minute slope',f"{f['slope_15m']:+.2f} mg/dL/min");c.metric('60-minute steps',f"{f['steps_60m']:.0f}")
    with st.expander('Inspect evolving twin state'):st.json(state)
    st.dataframe(pd.DataFrame(twin.history).tail(8),hide_index=True,use_container_width=True)

if page=='Live Digital Twin':
    st.subheader('Live Digital Twin');st.write('Replay recorded synthetic observations. Each tick updates the state and recomputes the estimate.');live()
else:
    # Leaving replay pauses it. Patient states persist independently in this session.
    twin.running=False;state=twin.update(s,profile,bundle,ROOT/'artifacts/events.sqlite');past=s.iloc[:twin.cursor+1]
    if page=='Executive Overview':
        metrics(state);st.plotly_chart(timeline(past),use_container_width=True)
        a,b=st.columns([1.5,1]);a.subheader('A patient-specific view');a.write('Historical HbA1c and baseline glucose combine with recent CGM, activity, meal annotations and sleep. Use Live Digital Twin to replay this patient and watch the state change.')
        b.subheader('Review context');b.info('Review the recent glucose trajectory, available activity information, and the synthetic patient history.')
        st.subheader('Recent review flags');st.dataframe(pd.DataFrame([r for r in twin.history if r['alert']!='Below alert cutoff']).tail(5),hide_index=True)
    elif page=='Patient Profile':
        st.subheader(f'{pid} · Historical profile');a,b,c=st.columns(3)
        a.metric('Age',int(profile.age));b.metric('Historical HbA1c',f'{profile.hba1c_pct:.1f}%');c.metric('Historical baseline',f'{profile.baseline_glucose:.0f} mg/dL')
        st.dataframe(profile.astype(str).rename('Value').to_frame(),use_container_width=True);st.info('Historical values are independently generated before replay. They are not calculated from the held-out future timeline.')
    elif page=='Risk and Explainability':
        metrics(state);st.subheader('Local model sensitivity')
        if state['probability'] is None:st.warning('Estimate withheld because sensor data are stale or incomplete.')
        else:
            x=features(past,profile).iloc[[-1]];loc=local_sensitivity(bundle,x).head(8)
            st.plotly_chart(px.bar(loc,x='probability_change',y='feature',orientation='h',color_discrete_sequence=['#087f8c']),use_container_width=True)
            st.caption('Actual estimate minus estimate after replacing ONE feature with its training median. Not additive contributions, SHAP values, or causal effects. Correlated features can produce unrealistic replacement combinations.')
        st.write('Sigmoid calibration uses separate synthetic patients. Clinical calibration, uncertainty intervals, external validity and intervention effects remain unvalidated.')
        st.dataframe(pd.Series(state['features'],name='Current feature').to_frame())
    elif page=='Scenario Simulator':
        st.subheader('Explore hypothetical inputs');st.warning('Input sensitivity only. These edits do not establish causal effects or provide treatment advice. Original state and audit log remain unchanged.')
        scenario=st.selectbox('Scenario',['Recent glucose trajectory','Meal annotation now','Recent activity','Missing sensor interval','Alternate historical profile'])
        altered=past.copy();pr=profile.copy()
        if scenario=='Recent glucose trajectory':
            delta=st.slider('Change over the recent 30 minutes (mg/dL)',-40,60,20);n=min(6,len(altered));altered.loc[altered.index[-n:],'glucose_mg_dl']+=np.linspace(0,delta,n)
        elif scenario=='Meal annotation now':altered.loc[altered.index[-1],'meal_event']=1
        elif scenario=='Recent activity':
            steps=st.slider('Extra steps in recent 30 minutes',0,3000,1200);altered.loc[altered.index[-6:],'steps']+=steps//6;altered.loc[altered.index[-6:],'heart_rate_bpm']+=20
        elif scenario=='Missing sensor interval':altered.loc[altered.index[-6:],'glucose_mg_dl']=np.nan
        else:
            other=st.selectbox('Alternate synthetic EHR',ehr.patient_id.tolist(),index=1);pr=ehr[ehr.patient_id==other].iloc[0]
        x=features(altered,pr).iloc[[-1]];p=float(calibrated(bundle,x)[0]) if eligible(x).iloc[0] else None
        a,b=st.columns(2);a.metric('Original estimate','Withheld' if state['probability'] is None else f"{state['probability']:.1%}");b.metric('Scenario estimate','Withheld' if p is None else f'{p:.1%}')
        st.plotly_chart(timeline(altered),use_container_width=True)
    elif page=='Model Performance':
        st.subheader('Held-out synthetic patients');st.warning('Simulator performance does not establish clinical validity. Overlapping windows are correlated; this is one seeded experiment.')
        table=pd.DataFrame({k:report[k] for k in ['ml','baseline','dynamic_only']}).T
        st.dataframe(table[['n','precision','recall','f1','pr_auc','roc_auc','brier','false_positive_rate']],use_container_width=True)
        st.caption('PR-AUC is average precision. Baseline emits binary decisions, so its Brier/AP values describe binary scores. Alert cutoff fixed at 0.50. False positives count windows, not independent clinical episodes.')
        a,b=st.columns(2)
        a.plotly_chart(px.imshow(report['ml']['confusion_matrix'],text_auto=True,x=['Predicted no event','Predicted event'],y=['Actual no event','Actual event'],color_continuous_scale='Teal',title='Confusion matrix'),use_container_width=True)
        curve=report['pr_curve'];b.plotly_chart(go.Figure(go.Scatter(x=curve['recall'],y=curve['precision'])).update_layout(title='Precision–recall',xaxis_title='Recall',yaxis_title='Precision'),use_container_width=True)
        c=report['calibration'];fig=go.Figure(go.Scatter(x=c['mean_prediction'],y=c['event_fraction'],mode='lines+markers',name='Synthetic test bins'));fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',line_dash='dash',name='Ideal'));fig.update_layout(title='Reliability diagram',xaxis_title='Mean predicted probability',yaxis_title='Observed event fraction')
        st.plotly_chart(fig,use_container_width=True);st.plotly_chart(px.bar(pd.DataFrame(report['importance']).head(10),x='importance',y='feature',orientation='h',title='Validation permutation importance (AP decrease)'),use_container_width=True)
        with st.expander('Dataset, partitions and early-warning subset'):st.json({k:report[k] for k in ['config','rows','sensor_rows','trials','below_threshold_at_prediction','split']})
        st.download_button('Download metrics JSON',(ROOT/'artifacts/metrics.json').read_bytes(),'metrics.json')
    else:
        st.subheader('Persistent prediction audit log')
        with sqlite3.connect(ROOT/'artifacts/events.sqlite') as con:logs=pd.read_sql_query('SELECT * FROM predictions WHERE patient_id=? ORDER BY timestamp',con,params=[pid])
        st.dataframe(logs,use_container_width=True,hide_index=True);st.download_button('Export patient log',logs.to_csv(index=False),'prediction_log.csv')
        if st.checkbox('Retrospective evaluation: reveal complete recorded timeline'):
            st.warning('Future ground truth is shown ONLY for retrospective inspection. These observations are not forecasts.')
            st.plotly_chart(px.line(s,x='timestamp',y='glucose_mg_dl',title='Complete synthetic ground truth'),use_container_width=True)
