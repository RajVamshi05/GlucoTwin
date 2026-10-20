"""Regenerate competition PDFs from the executed metrics; no external services."""
from pathlib import Path
import json,textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';D.mkdir(exist_ok=True)
r=json.loads((ROOT/'artifacts/metrics.json').read_text());W,H=1280,720
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(FONT).exists():
 pdfmetrics.registerFont(TTFont('Body',FONT));pdfmetrics.registerFont(TTFont('Bold',BOLD))
else:
 from reportlab.pdfbase.pdfmetrics import Font
 pdfmetrics.registerFont(Font('Body','Helvetica','WinAnsiEncoding'));pdfmetrics.registerFont(Font('Bold','Helvetica-Bold','WinAnsiEncoding'))
navy=HexColor('#102f42');teal=HexColor('#087f8c');muted=HexColor('#526b7c');white=HexColor('#ffffff')
def base(c,title,num):
 c.setFillColor(HexColor('#f4f7fb'));c.rect(0,0,W,H,fill=1,stroke=0);c.setFillColor(teal);c.rect(0,H-16,W,16,fill=1,stroke=0)
 c.setFillColor(navy);c.setFont('Bold',34);c.drawString(64,628,title);c.setFont('Body',14);c.setFillColor(muted)
 c.drawString(64,35,'GLUCOTWIN  /  SYNTHETIC RESEARCH PROOF OF CONCEPT');c.drawRightString(1216,35,str(num))
def paragraph(c,txt,x,y,width=95,size=23,color=navy):
 c.setFillColor(color);c.setFont('Body',size)
 for line in textwrap.wrap(txt,width):c.drawString(x,y,line);y-=size*1.5
 return y

def architecture(c,num=1):
 base(c,'A continuously updating, patient-specific monitoring twin',num)
 boxes=[(64,420,340,115,'Historical profile','Synthetic EHR and baseline'),(64,225,340,115,'Sensor replay','CGM, HR, steps, sleep, meals'),(470,320,340,140,'Causal twin state','Past-only features + quality gate'),(890,420,325,115,'Prediction engine','Trained classifier + calibration'),(890,225,325,115,'Clinical research view','Dashboard + SQLite audit')]
 for x,y,w,h,title,desc in boxes:
  c.setFillColor(white);c.setStrokeColor(HexColor('#c8d9e5'));c.roundRect(x,y,w,h,12,fill=1,stroke=1);c.setFont('Bold',20);c.setFillColor(navy);c.drawString(x+18,y+h-38,title);paragraph(c,desc,x+18,y+h-72,30,16)
 c.setStrokeColor(teal);c.setLineWidth(3)
 for pts in [[(404,477),(437,477),(437,410),(470,410)],[(404,282),(437,282),(437,365),(470,365)],[(810,410),(847,410),(847,477),(890,477)],[(1052,420),(1052,340)]]:
  path=c.beginPath();path.moveTo(*pts[0])
  for point in pts[1:]:path.lineTo(*point)
  c.drawPath(path)
  x,y=pts[-1];prev=pts[-2]
  if x!=prev[0]:c.line(x,y,x-10,y+6);c.line(x,y,x-10,y-6)
  else:c.line(x,y,x-6,y+10);c.line(x,y,x+6,y+10)
 paragraph(c,'Offline: simulator > labels > patient split > train > validate > calibrate > final test',64,142,110,20)
 paragraph(c,'Future observations are used only for labels and explicit retrospective evaluation.',64,104,110,19)

c=canvas.Canvas(str(D/'ARCHITECTURE.pdf'),pagesize=(W,H));c.setTitle('GlucoTwin Architecture');architecture(c);c.showPage();c.save()
slides=[
 ('GlucoTwin', ['A Personalized, Continuously Updating Digital Twin for Early Prediction of Glucose Excursions','From Reactive Glucose Monitoring to Personalized Predictive Health.','Vansh Deep Singh | IIIT Allahabad | B.Tech ECE, 2023-2027']),
 ('The problem: snapshots miss changing trajectories',['Historical measurements describe a baseline. Sensor streams describe what is changing.','This prototype joins both streams to estimate a future high-glucose event.','Research question: can recent observations and patient history predict the simulator-defined event?']),
 ('A precise prediction contract',['At t: use only information available through t.','Event: any glucose >180 mg/dL during t+5 to t+120 minutes.','Require a complete future horizon to assign a training label. Report currently-below-threshold windows separately.']),
 ('architecture',[]),
 ('Synthetic data with temporal structure',['160 fictional patients. Seven days each. 322,560 sensor rows.','Patient baselines, delayed meal peaks, activity-associated changes, circadian patterns and autocorrelated noise.','Random and contiguous CGM dropouts. Hidden response parameters excluded from model features.']),
 ('A trained model with patient-separated evaluation',['88 training / 24 validation / 24 calibration / 24 test patients.','Histogram gradient boosting: select leaf count using validation average precision.','Separate sigmoid calibration. Fixed 0.50 alert cutoff. No test-set tuning.']),
 ('results',[]),
 ('The result has important limits',['Dynamic-only F1: 0.847. Fused F1: 0.845. No demonstrated personalization benefit.','Brier slightly worsened after calibration: 0.06867 to 0.06952.','Below-threshold-at-t F1: 0.745. Main results include continuation of existing elevations.']),
 ('live',[]),
 ('Interpretation and scenario exploration',['Local sensitivity replaces one feature with its training median. It is non-additive and non-causal.','Scenarios change a copied observed history, then recompute features and the estimate.','A missing sensor interval withholds the estimate. No intervention or treatment advice.']),
 ('Reproducible by design',['Seeded generator, pinned dependencies and bundled trained model.','Shared feature code for training and replay. Persistent idempotent SQLite audit.','Tests cover future-data isolation, labels, partitions, missingness, replay and dashboard navigation.']),
 ('What the prototype establishes',['An end-to-end patient monitoring twin with real model training and evolving state.','It predicts assumptions built into a synthetic simulator. It does not establish clinical validity.','Next research step: independent licensed longitudinal data, patient-level uncertainty and prospective evaluation.']),
 ('A transparent submission',['Runnable local application, source, trained model, metrics and documentation.','Architecture and presentation PDFs, demonstration script and walkthrough materials.','Public repository and hosted recording links must be verified before submission.'])]
c=canvas.Canvas(str(D/'GLUCOTWIN_PRESENTATION.pdf'),pagesize=(W,H));c.setTitle('GlucoTwin Competition Presentation')
for i,(title,points) in enumerate(slides,1):
 if title=='architecture':architecture(c,i)
 elif title=='results':
  base(c,'Held-out performance on synthetic patients',i)
  headers=['Model','Precision','Recall','F1','PR-AUC'];xs=[64,500,680,850,1030]
  c.setFont('Bold',23);c.setFillColor(teal)
  for x,h in zip(xs,headers):c.drawString(x,520,h)
  for y,key,label in [(440,'ml','Fused model'),(355,'baseline','Rule baseline'),(270,'dynamic_only','Dynamic-only')]:
   m=r[key];c.setFillColor(navy);c.setFont('Body',24)
   for x,val in zip(xs,[label]+[f'{m[k]:.3f}' for k in ['precision','recall','f1','pr_auc']]):c.drawString(x,y,val)
  paragraph(c,'11,567 test windows from 24 held-out patients. PR-AUC = average precision.',64,170,110,20)
  paragraph(c,'Fused false-positive rate: 6.78%. Correlated windows are not independent alert episodes.',64,122,110,20)
 elif title=='live':
  base(c,'The twin changes as new observations arrive',i)
  image=D/'demo_frames/live_meal.png'
  if image.exists():c.drawImage(str(image),64,98,width=750,height=520,preserveAspectRatio=True,anchor='c')
  paragraph(c,'Start / pause / resume',860,490,24,22);paragraph(c,'Step / advance / reset',860,410,24,22);paragraph(c,'Past-only live view',860,330,24,22);paragraph(c,'Persistent audit log',860,250,24,22)
 else:
  base(c,title,i);y=525
  for j,point in enumerate(points):
   c.setFillColor(teal);c.circle(75,y+7,5,fill=1,stroke=0);y=paragraph(c,point,100,y,86,25)-45
 c.showPage()
c.save()
print('Created architecture and 13-slide presentation PDFs')
